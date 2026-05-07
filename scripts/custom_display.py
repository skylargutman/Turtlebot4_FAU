#!/usr/bin/env python3
"""
custom_display.py - TurtleBot4 FAU Fleet
Custom SSD1306 OLED display driver for I2C bus 1.

The TurtleBot 4 Lite fleet at FAU has SSD1306 displays wired to I2C
bus 1 (not the default bus 3). The stock TurtleBot 4 display driver
does not work with this wiring. This script bit-bangs the display
directly using smbus2.

Dependencies:
  pip3 install --break-system-packages smbus2 Pillow

Hardware:
  - SSD1306 128x64 OLED on I2C bus 1, address 0x3c
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from sensor_msgs.msg import BatteryState

import smbus2
import time
from PIL import Image, ImageDraw, ImageFont

# Display config
I2C_BUS = 1
I2C_ADDR = 0x3c
WIDTH = 128
HEIGHT = 64
PAGES = HEIGHT // 8

CMD = 0x00
DATA = 0x40


class SSD1306:
    """Minimal SSD1306 driver using smbus2."""

    def __init__(self, bus_num=I2C_BUS, addr=I2C_ADDR):
        self.bus = smbus2.SMBus(bus_num)
        self.addr = addr
        self._init_display()

    def _cmd(self, c):
        self.bus.write_byte_data(self.addr, CMD, c)

    def _init_display(self):
        init_seq = [
            0xAE,           # Display OFF
            0xD5, 0x80,     # Set display clock divide
            0xA8, 0x3F,     # Set multiplex (64-1)
            0xD3, 0x00,     # Display offset 0
            0x40,           # Start line 0
            0x8D, 0x14,     # Charge pump enable
            0x20, 0x00,     # Horizontal addressing mode
            0xA1,           # Segment remap
            0xC8,           # COM scan direction
            0xDA, 0x12,     # COM pins config for 128x64
            0x81, 0xCF,     # Contrast
            0xD9, 0xF1,     # Pre-charge
            0xDB, 0x40,     # VCOMH deselect
            0xA4,           # Resume to RAM content
            0xA6,           # Normal display (not inverted)
            0xAF,           # Display ON
        ]
        for c in init_seq:
            self._cmd(c)

    def display(self, image):
        """Send a PIL Image to the display."""
        # Convert to 1-bit and extract pixel data
        buf = image.convert('1').tobytes()

        # Set column and page address
        self._cmd(0x21)  # Set column address
        self._cmd(0)     # Start
        self._cmd(WIDTH - 1)  # End
        self._cmd(0x22)  # Set page address
        self._cmd(0)     # Start
        self._cmd(PAGES - 1)  # End

        # Convert horizontal pixel data to page format
        pages = [0] * (WIDTH * PAGES)
        for y in range(HEIGHT):
            for x in range(WIDTH):
                pixel = buf[y * ((WIDTH + 7) // 8) + x // 8]
                if pixel & (0x80 >> (x % 8)):
                    pass  # pixel is white (set)
                else:
                    pages[(y // 8) * WIDTH + x] |= (1 << (y % 8))

        # Send data in chunks (smbus2 max is 32 bytes)
        for i in range(0, len(pages), 32):
            chunk = pages[i:i + 32]
            self.bus.write_i2c_block_data(self.addr, DATA, chunk)

    def clear(self):
        """Clear the display."""
        img = Image.new('1', (WIDTH, HEIGHT), 0)
        self.display(img)


class DisplayNode(Node):
    """ROS 2 node that renders status info on the SSD1306."""

    def __init__(self):
        super().__init__('custom_display')

        self.battery_pct = 0.0
        self.ip_address = 'waiting...'
        self.dock_status = 'unknown'

        # Initialize display
        try:
            self.oled = SSD1306()
            self.get_logger().info(
                f'Display initialized on i2c-{I2C_BUS} at 0x{I2C_ADDR:02x}')
        except Exception as e:
            self.get_logger().error(f'Failed to init display: {e}')
            self.oled = None
            return

        # Subscribe to topics
        self.create_subscription(
            BatteryState, '/battery_state', self._battery_cb, 10)
        self.create_subscription(
            String, '/ip', self._ip_cb, 10)

        # Refresh display every 2 seconds
        self.timer = self.create_timer(2.0, self._refresh)

        # Try to load a TTF font, fall back to default
        try:
            self.font = ImageFont.truetype(
                '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf', 10)
            self.font_sm = ImageFont.truetype(
                '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf', 8)
        except Exception:
            self.font = ImageFont.load_default()
            self.font_sm = self.font

    def _battery_cb(self, msg):
        self.battery_pct = msg.percentage * 100.0

    def _ip_cb(self, msg):
        self.ip_address = msg.data

    def _refresh(self):
        if self.oled is None:
            return

        img = Image.new('1', (WIDTH, HEIGHT), 0)
        draw = ImageDraw.Draw(img)

        # Header line
        draw.text((0, 0), f'TB4 FAU', font=self.font, fill=1)
        draw.text((80, 0), f'{self.battery_pct:.0f}%', font=self.font, fill=1)

        # Separator
        draw.line([(0, 12), (WIDTH, 12)], fill=1)

        # IP address
        draw.text((0, 16), f'IP: {self.ip_address}', font=self.font_sm, fill=1)

        # Status
        draw.text((0, 28), f'Dock: {self.dock_status}', font=self.font_sm, fill=1)

        # Domain ID
        import os
        domain = os.environ.get('ROS_DOMAIN_ID', '?')
        draw.text((0, 40), f'Domain: {domain}', font=self.font_sm, fill=1)

        # Hostname
        import socket
        draw.text((0, 52), socket.gethostname(), font=self.font_sm, fill=1)

        self.oled.display(img)


def main():
    rclpy.init()
    node = DisplayNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node.oled:
            node.oled.clear()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
