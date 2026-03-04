from __future__ import annotations

import pyte
from rich.text import Text
from textual.widgets import Static


def raw_to_rich_text(raw_output: bytes, cols: int = 200, rows: int = 500) -> Text:
    screen = pyte.Screen(cols, rows)
    stream = pyte.ByteStream(screen)
    stream.feed(raw_output)
    text = Text()
    for y in range(rows):
        line = screen.buffer[y]
        has_content = any(line[x].data.strip() for x in line)
        if not has_content:
            continue
        line_text = "".join(line[x].data for x in range(cols))
        text.append(line_text.rstrip() + "\n")
    return text


class OutputViewer(Static):
    def __init__(self, raw_output: bytes, **kwargs) -> None:
        super().__init__(**kwargs)
        self._raw_output = raw_output

    def on_mount(self) -> None:
        rich_text = raw_to_rich_text(self._raw_output)
        self.update(rich_text)
