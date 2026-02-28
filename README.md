# pymarq

![pymarq](/pymarq.svg)

A simple Python library for interacting with [ViewMarq](https://www.automationdirect.com/adc/overview/catalog/hmi_(human_machine_interface)/message_displays/message_displays) LED message displays over Modbus TCP.

## Installation

```bash
pip install git+https://github.com/carterprince/pymarq
```

## Usage

### Simple Text
```python
from pymarq import ViewMarq

display = ViewMarq("192.168.1.100")

# Simple string
display.write("Hello World")

# Multi-line string
display.write("Line 1\nLine 2")

# Simple color control
display.write("OK", color=ViewMarq.GREEN)
display.write("CAUTION", color=ViewMarq.AMBER)
display.write("WARNING", color=ViewMarq.RED)

# Clear the display
display.clear()
```

### Rich Text & Scrolling
All text methods natively support inline ViewMarq tags for per-character colors, blinking, and font changes.

```python
# Mixed colors and blinking in one line
display.write("System: <RED><BL F>FAULT<BL N> <GRN>(Normal)")

# Scrolling text
display.scroll("Continuous scroll...", speed="fast", color=ViewMarq.GREEN)

# Create a scrolling rainbow
rainbow = "<RED>R<AMB>A<GRN>I<RED>N<AMB>B<GRN>O<RED>W"
display.scroll(rainbow, direction="left", speed="medium")
```

### Advanced Control
```python
# Per-line control: text, scroll, direction, speed, and color
display.write_lines([
    "Static Header",
    ("Scrolling Subtitle", True, "left", "fast", ViewMarq.RED),
    ("<GRN>Status: <AMB>Wait", False),
])

# Draw a rectangle
display.draw_rect(0, 0, 32, 8, color=ViewMarq.GREEN)

# Draw a single pixel
display.put_pixel(5, 5, color=ViewMarq.RED)
```

## API

### `ViewMarq(ip, port=502)`
Creates a display connection. `port` defaults to 502.

---

### `write(content, color=ViewMarq.GREEN)`
Sends text to the display. `content` can be a string, a newline-delimited string, or a list of strings. Supports inline tags.

---

### `write_lines(lines)`
Writes a list of lines with per-line control. 
Each item can be a `str` or a `tuple` of `(text, scroll, direction, speed, color)`.

---

### `scroll(content, direction="left", speed="medium", color=ViewMarq.GREEN, pause=0, justify="center")`
Scrolls text across the entire display. Supports inline tags for multi-colored scrolling.

| Parameter | Options | Description |
|---|---|---|
| `direction` | `left`, `right`, `up`, `down` | Scroll direction |
| `speed` | `slow`, `medium`, `fast` | Scroll speed |
| `pause` | `int` (seconds) | Pause duration before re-scrolling |
| `justify` | `left`, `center`, `right`, `top`, `bottom` | Justification during pause |

---

### `draw_rect(x, y, width, height, color=ViewMarq.GREEN)`
Draws a rectangle outline at the given pixel coordinates.

---

### `put_pixel(x, y, color=ViewMarq.GREEN)`
Draws a single pixel at the given coordinates.

---

### Color constants
- `ViewMarq.GREEN` (`<GRN>`)
- `ViewMarq.RED` (`<RED>`)
- `ViewMarq.AMBER` (`<AMB>`)

## See Also
- [ViewMarq Hardware User Manual](https://cdn.automationdirect.com/static/manuals/mduserm/mduserm.html)
