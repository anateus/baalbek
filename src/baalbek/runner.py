from __future__ import annotations

import fcntl
import os
import pty
import select
import struct
import termios
from dataclasses import dataclass

import pyte


@dataclass
class RunResult:
    exit_code: int
    raw_output: bytes
    plain_output: str


def run_command(args: list[str], rows: int = 24, cols: int = 80) -> RunResult:
    pid, master_fd = pty.fork()

    if pid == 0:
        os.execvp(args[0], args)

    fcntl.ioctl(
        master_fd, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0)
    )

    raw = b""
    try:
        while True:
            ready, _, _ = select.select([master_fd], [], [], 0.5)
            if not ready:
                break
            try:
                chunk = os.read(master_fd, 4096)
                if not chunk:
                    break
                raw += chunk
            except OSError:
                break
    finally:
        try:
            while True:
                ready, _, _ = select.select([master_fd], [], [], 0.1)
                if not ready:
                    break
                try:
                    chunk = os.read(master_fd, 4096)
                    if not chunk:
                        break
                    raw += chunk
                except OSError:
                    break
        except OSError:
            pass
        os.close(master_fd)

    _, status = os.waitpid(pid, 0)
    exit_code = os.waitstatus_to_exitcode(status)

    screen = pyte.Screen(cols, rows)
    stream = pyte.ByteStream(screen)
    stream.feed(raw)

    lines = [line.rstrip() for line in screen.display]
    while lines and not lines[-1]:
        lines.pop()
    plain_output = "\n".join(lines)

    return RunResult(exit_code=exit_code, raw_output=raw, plain_output=plain_output)
