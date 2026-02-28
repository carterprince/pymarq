# pymarq

![pymarq](/pymarq.svg)

A simple Python library for interacting with [ViewMarq](https://www.automationdirect.com/adc/overview/catalog/hmi_(human_machine_interface)/message_displays/message_displays) LED message displays over Modbus TCP.

## Installation

```bash
pip install git+https://github.com/carterprince/pymarq
```

or with `uv`:

```bash
uv pip install git+https://github.com/carterprince/pymarq
```

## Usage

```python
from pymarq import ViewMarq

display = ViewMarq("192.168.1.100")

# Simple string
display.write("Hello World")

# Multi-line string
display.write("Line 1\nLine 2")

# With color
display.write("WARNING", color=ViewMarq.RED)
display.write("OK", color=ViewMarq.GREEN)
display.write("CAUTION", color=ViewMarq.AMBER)

# Rich text with inline formatting (per-character/word colors and blinking)
display.write_rich("<RED>W<AMB>A<GRN>R<RED>N<AMB>I<GRN>N<RED>G")
display.write_rich("System: <RED><BL F>FAULT<BL N><GRN> - Check Engine")

# Per-line control: scroll, direction, speed, and color
display.write_lines([
    "Static Header",
    ("Breaking News", True, "left", "fast", ViewMarq.RED),
    ("All clear", False, None, None, ViewMarq.GREEN),
])

# Scroll text across the display
display.scroll("Hello World", direction="left", speed="fast", color=ViewMarq.AMBER)

# Scroll with a pause and justification
display.scroll("ALERT", direction="left", speed="medium", color=ViewMarq.RED, pause=3, justify="center")

# Clear the display
display.clear()

# Draw a rectangle
display.draw_rect(0, 0, 32, 8, color=ViewMarq.GREEN)

# Draw a single pixel
display.put_pixel(5, 5, color=ViewMarq.RED)
```

## API

### `ViewMarq(ip, port=502)`

Creates a display connection. `port` defaults to 502 (standard Modbus TCP).

---

### `write(content, color="")`

Sends text to the display. `content` can be a plain string, a newline-delimited string, or a list of strings. Each item/line is positioned on a separate row (8px apart by default).

---

### `write_rich(content)`

Sends text to the display allowing inline ViewMarq formatting tags for per-character or per-word styling. Automatically parses known tags (e.g., `<RED>`, `<GRN>`, `<BL F>`, `<CS 2>`) and wraps the remaining text appropriately. Supports multi-line strings.

---

### `write_lines(lines)`

Writes a list of lines to the display with per-line control over scrolling, direction, speed, and color.

Each item in `lines` can be:
- A plain `str` — displayed statically in the default color.
- A `tuple` of `(text, scroll, direction, speed, color)` — all fields after `text` are optional.

```python
display.write_lines([
    "Static line",
    ("Scrolling line", True, "left", "fast", ViewMarq.RED),
])
```

---

### `scroll(content, direction="left", speed="medium", color="", pause=0, justify="center")`

Scrolls text across the entire display. `content` can be a plain string (supports `\n` for multi-line) or a list of strings.

| Parameter | Options | Description |
|---|---|---|
| `direction` | `left`, `right`, `up`, `down` | Scroll direction |
| `speed` | `slow`, `medium`, `fast` | Scroll speed |
| `color` | See color constants | Text color |
| `pause` | `int` (seconds) | Pause duration before re-scrolling; `0` for continuous |
| `justify` | `left`, `center`, `right`, `top`, `bottom` | Justification during pause |

---

### `clear()`

Clears the display.

---

### `draw_rect(x, y, width, height, color="")`

Draws a rectangle outline at the given pixel coordinates.

---

### `put_pixel(x, y, color="")`

Draws a single pixel at the given coordinates.

---

### Color constants

| Constant | Value |
|---|---|
| `ViewMarq.GREEN` | `<GRN>` |
| `ViewMarq.RED` | `<RED>` |
| `ViewMarq.AMBER` | `<AMB>` |

### Instance attributes

| Attribute | Default | Description |
|---|---|---|
| `display_id` | `1` | Target display ID |
| `line_height` | `8` | Vertical pixel offset between lines |

## See Also

- [ViewMarq Hardware User Manual](https://cdn.automationdirect.com/static/manuals/mduserm/mduserm.html)
