# pymarq

A simple Python library for interacting with [ViewMarq](https://www.automationdirect.com/adc/shopping/catalog/operator_interfaces/viewmarq_led_message_displays) LED message displays over Modbus TCP.

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
```

## API

### `ViewMarq(ip, port=502)`

Creates a display connection. `port` defaults to 502 (standard Modbus TCP).

### `write(content, color="<GRN>")`

Sends text to the display. `content` can be a plain string, a newline-delimited string, or a list of strings. Each item/line is positioned on a separate row (8px apart by default).

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
