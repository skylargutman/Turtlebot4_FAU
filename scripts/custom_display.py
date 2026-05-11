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

import os
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from std_msgs.msg import String
from sensor_msgs.msg import BatteryState

try:
    from irobot_create_msgs.msg import DockStatus
    HAS_DOCK_MSG = True
except ImportError:
    HAS_DOCK_MSG = False

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
        """Send a PIL Image (mode '1') to the display.
        Black background, white lit pixels."""
        # Convert to 1-bit
        bw = image.convert('1')

        # Set column and page address
        self._cmd(0x21)  # Set column address
        self._cmd(0)     # Start
        self._cmd(WIDTH - 1)  # End
        self._cmd(0x22)  # Set page address
        self._cmd(0)     # Start
        self._cmd(PAGES - 1)  # End

        # Build page buffer
        # In mode '1', pixel value 255 = white (lit), 0 = black (off)
        pages = [0] * (WIDTH * PAGES)
        pixels = bw.load()
        for y in range(HEIGHT):
            for x in range(WIDTH):
                if pixels[x, y]:  # white pixel = lit
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

        # Subscribe to topics with sensor QoS for Create 3 compatibility
        self.create_subscription(
            BatteryState, '/battery_state', self._battery_cb,
            qos_profile_sensor_data)
        self.create_subscription(
            String, '/ip', self._ip_cb,
            qos_profile_sensor_data)

        if HAS_DOCK_MSG:
            self.create_subscription(
                DockStatus, '/dock_status', self._dock_cb,
                qos_profile_sensor_data)

        # Refresh display every 2 seconds
        self.timer = self.create_timer(2.0, self._refresh)

        # Load fonts
        try:
            self.font = ImageFont.truetype(
                '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf', 12)
            self.font_sm = ImageFont.truetype(
                '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf', 11)
        except Exception:
            self.font = ImageFont.load_default()
            self.font_sm = self.font

    def _battery_cb(self, msg):
        self.battery_pct = msg.percentage * 100.0

    def _ip_cb(self, msg):
        self.ip_address = msg.data

    def _dock_cb(self, msg):
        self.dock_status = 'docked' if msg.is_docked else 'undocked'

    def _refresh(self):
        if self.oled is None:
            return

        # Black background, white text
        img = Image.new('1', (WIDTH, HEIGHT), 0)
        draw = ImageDraw.Draw(img)

        domain = os.environ.get('ROS_DOMAIN_ID', '?')

        # Line 1: Header
        draw.text((0, 0), f'TB4 #{domain}', font=self.font, fill=255)
        draw.text((80, 0), f'{self.battery_pct:.0f}%', font=self.font, fill=255)

        # Separator
        draw.line([(0, 15), (WIDTH, 15)], fill=255)

        # Line 2: IP address
        draw.text((0, 18), f'{self.ip_address}', font=self.font_sm, fill=255)

        # Line 3: Dock status
        draw.text((0, 34), f'Dock: {self.dock_status}', font=self.font_sm, fill=255)

        # Line 4: Battery bar
        bar_y = 50
        bar_w = 100
        bar_h = 10
        draw.rectangle([(0, bar_y), (bar_w, bar_y + bar_h)], outline=255)
        fill_w = int(bar_w * min(self.battery_pct / 100.0, 1.0))
        if fill_w > 0:
            draw.rectangle([(0, bar_y), (fill_w, bar_y + bar_h)], fill=255)

        self.oled.display(img)


def main():
    rclpy.init()
    node = DisplayNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        if node.oled:
            node.oled.clear()
        node.destroy_node()
        try:
            rclpy.shutdown()
        except Exception:
            pass


if __name__ == '__main__':
    main()
