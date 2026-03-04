from __future__ import annotations

import fcntl
import os
import pty
import select
import struct
import sys
import termios
import tty
from dataclasses import dataclass

import pyte


@dataclass
class RunResult:
    exit_code: int
    raw_output: bytes
    plain_output: str


def run_command(args: list[str], timeout: float = 300) -> RunResult:
    import signal
    import time

    try:
        size = os.get_terminal_size()
        rows, cols = size.lines, size.columns
    except OSError:
        rows, cols = 24, 200

    pid, master_fd = pty.fork()

    if pid == 0:
        os.execvp(args[0], args)

    fcntl.ioctl(
        master_fd, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0)
    )

    interactive = True
    tty_fd = -1
    try:
        stdin_fd = sys.stdin.fileno()
        stdout_fd = sys.stdout.fileno()
        old_attrs = termios.tcgetattr(stdin_fd)
        tty.setraw(stdin_fd)
    except (OSError, AttributeError, termios.error):
        interactive = False
        stdin_fd = -1
        stdout_fd = -1
        old_attrs = None

    output_fd = stdout_fd
    if output_fd == -1:
        try:
            tty_fd = os.open("/dev/tty", os.O_WRONLY)
            output_fd = tty_fd
        except OSError:
            pass

    raw = b""
    start_time = time.monotonic()
    child_exited = False

    try:
        while True:
            if time.monotonic() - start_time > timeout:
                os.kill(pid, signal.SIGTERM)
                break

            fds = [master_fd] + ([stdin_fd] if interactive else [])
            ready, _, _ = select.select(fds, [], [], 0.1)

            if interactive and stdin_fd in ready:
                try:
                    data = os.read(stdin_fd, 4096)
                    if data:
                        os.write(master_fd, data)
                except OSError:
                    pass

            if master_fd in ready:
                try:
                    chunk = os.read(master_fd, 4096)
                    if not chunk:
                        break
                    raw += chunk
                    if output_fd != -1:
                        os.write(output_fd, chunk)
                except OSError:
                    break

            result = os.waitpid(pid, os.WNOHANG)
            if result[0] != 0:
                child_exited = True
                while True:
                    r, _, _ = select.select([master_fd], [], [], 0.1)
                    if not r:
                        break
                    try:
                        chunk = os.read(master_fd, 4096)
                        if not chunk:
                            break
                        raw += chunk
                        if output_fd != -1:
                            os.write(output_fd, chunk)
                    except OSError:
                        break
                break
    finally:
        if interactive and old_attrs is not None:
            termios.tcsetattr(stdin_fd, termios.TCSADRAIN, old_attrs)
        os.close(master_fd)
        if tty_fd != -1:
            os.close(tty_fd)

    if child_exited:
        _, status = result
    else:
        _, status = os.waitpid(pid, 0)
    exit_code = os.waitstatus_to_exitcode(status)

    screen = pyte.Screen(cols, max(rows, 500))
    stream = pyte.ByteStream(screen)
    stream.feed(raw)

    lines = [line.rstrip() for line in screen.display]
    while lines and not lines[-1]:
        lines.pop()
    plain_output = "\n".join(lines)

    return RunResult(exit_code=exit_code, raw_output=raw, plain_output=plain_output)
