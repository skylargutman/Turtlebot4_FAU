#!/usr/bin/env python3
"""
scan_normalizer.py - TurtleBot4 FAU Fleet
Normalizes RPLidar scan messages to a fixed point count.

The RPLidar on the TurtleBot 4 Lite occasionally produces scans with
inconsistent point counts. SLAM Toolbox locks onto the first scan's
count and rejects anything different, causing mapping failures.

This node subscribes to /scan, resamples every message to a fixed
1083 readings via linear interpolation, and republishes on
/scan_normalized.

Usage with SLAM Toolbox:
  ros2 launch turtlebot4_navigation slam.launch.py scan_topic:=/scan_normalized
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
import math


class ScanNormalizer(Node):
    def __init__(self):
        super().__init__('scan_normalizer')
        self.target_count = 1083  # Fixed count slam_toolbox will lock onto
        self.sub = self.create_subscription(
            LaserScan, '/scan', self.cb, 10)
        self.pub = self.create_publisher(
            LaserScan, '/scan_normalized', 10)
        self.get_logger().info(
            f'Normalizing scans to {self.target_count} readings')

    def cb(self, msg):
        n_in = len(msg.ranges)
        n_out = self.target_count

        if n_in == n_out:
            self.pub.publish(msg)
            return

        # Resample by linear interpolation
        new_ranges = [0.0] * n_out
        new_intensities = [0.0] * n_out
        has_intensities = len(msg.intensities) == n_in

        for i in range(n_out):
            src_idx = i * (n_in - 1) / (n_out - 1)
            lo = int(math.floor(src_idx))
            hi = min(lo + 1, n_in - 1)
            frac = src_idx - lo

            r_lo = msg.ranges[lo]
            r_hi = msg.ranges[hi]

            if math.isinf(r_lo) or math.isinf(r_hi):
                new_ranges[i] = r_lo if frac < 0.5 else r_hi
            else:
                new_ranges[i] = r_lo * (1 - frac) + r_hi * frac

            if has_intensities:
                new_intensities[i] = (
                    msg.intensities[lo] * (1 - frac) +
                    msg.intensities[hi] * frac
                )

        out = LaserScan()
        out.header = msg.header
        out.angle_min = msg.angle_min
        out.angle_max = msg.angle_max
        out.angle_increment = (msg.angle_max - msg.angle_min) / (n_out - 1)
        out.time_increment = msg.time_increment
        out.scan_time = msg.scan_time
        out.range_min = msg.range_min
        out.range_max = msg.range_max
        out.ranges = new_ranges
        out.intensities = new_intensities if has_intensities else []

        self.pub.publish(out)


def main():
    rclpy.init()
    node = ScanNormalizer()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        try:
            rclpy.shutdown()
        except Exception:
            pass


if __name__ == '__main__':
    main()
