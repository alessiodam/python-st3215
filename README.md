# Python-ST3215

[![wakatime](https://wakatime.com/badge/user/b67f4ae3-1ee8-40ea-b8d8-196354064008/project/2d953882-4dfb-4c53-8a18-c698dc275f82.svg)](https://wakatime.com/badge/user/b67f4ae3-1ee8-40ea-b8d8-196354064008/project/2d953882-4dfb-4c53-8a18-c698dc275f82)
[![PyPI Version](https://img.shields.io/pypi/v/python-st3215)](https://pypi.org/project/python-st3215/)
![Python Versions](https://img.shields.io/pypi/pyversions/python-st3215)
![License](https://img.shields.io/github/license/alessiodam/python-st3215)
![Downloads](https://img.shields.io/pypi/dm/python-st3215)
[![Issues](https://img.shields.io/github/issues/alessiodam/python-st3215)](https://github.com/alessiodam/python-st3215/issues)

Python-ST3215 is a lightweight and intuitive Python library for communicating with ST3215 Smart Servos over a serial bus.
It provides a high-level interface for reading and writing servo parameters, controlling motion, and working with the servo memory map.


## Features

* Simple API for controlling ST3215 servos
* High-level wrapper for movement and parameter access
* Helpful exceptions for robust applications
* Fully typed and documented through docstrings
* Tested against Waveshare ST3215 hardware


## Installation

Install via pip:

```bash
pip install python-st3215
```


## Quick Start

```python
from python_st3215 import ST3215, ServoNotRespondingError

controller = ST3215("/dev/ttyUSB0")

try:
    servo = controller.wrap_servo(1)
    print("Current location:", servo.sram.read_current_location())
except ServoNotRespondingError:
    print("Servo not responding")
finally:
    controller.close()
```


## Examples

A collection of example scripts is available in the [`examples/`](examples) directory.
These cover tasks such as motion control, serial communication tests, reading/writing parameters, and more.

## Documentation

The library is fully documented through docstrings.
Hover over classes and functions in your editor to see type hints, parameter descriptions, and usage notes.

## Hardware Compatibility

| Brand     | SKU   | Product                                                                      |
|-----------|-------|------------------------------------------------------------------------------|
| Waveshare | 22414 | [ST3215 Series Serial Bus Servo](https://www.waveshare.com/st3215-servo.htm) |
|           |       | USB to RS485 Serial Converter                                                |

## Memory Table

The complete memory map is documented in [`MEMORY_TABLE.md`](MEMORY_TABLE.md).

## License

This project is licensed under the **GPL-3.0-or-later** license.
See the [`LICENSE`](LICENSE) file for full details.

## Supporting the Project

If this library has been useful to you, consider supporting its development:
**[https://ko-fi.com/alessiodam](https://ko-fi.com/alessiodam)**
