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

Dock-aware: when the robot is docked, the /scan subscription is
destroyed so the LiDAR powers down. It is recreated on undock.

Usage with SLAM Toolbox:
  ros2 launch turtlebot4_navigation slam.launch.py scan_topic:=/scan_normalized
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan
from irobot_create_msgs.msg import DockStatus
import math


class ScanNormalizer(Node):
    def __init__(self):
        super().__init__('scan_normalizer')
        self.target_count = 1083  # Fixed count slam_toolbox will lock onto

        # Scan subscription (created/destroyed based on dock state)
        self.scan_sub = None
        self.is_docked = False

        self.pub = self.create_publisher(
            LaserScan, '/scan_normalized', 10)

        # Create3 publishes /dock_status with best-effort reliability,
        # so we must subscribe with a compatible QoS profile.
        self.create_subscription(
            DockStatus, '/dock_status', self.dock_cb,
            qos_profile_sensor_data)

        # Start with scan subscription active -- if the bot happens to
        # be docked at launch, the first /dock_status callback will
        # tear it down.
        self._create_scan_sub()

        self.get_logger().info(
            f'Normalizing scans to {self.target_count} readings '
            f'(dock-aware, LiDAR will idle when docked)')

    # -- Dock state management ----------------------------------------

    def dock_cb(self, msg):
        docked = msg.is_docked

        if docked and not self.is_docked:
            self.is_docked = True
            self._destroy_scan_sub()
            self.get_logger().info(
                'Docked -- unsubscribed from /scan, LiDAR will idle')

        elif not docked and self.is_docked:
            self.is_docked = False
            self._create_scan_sub()
            self.get_logger().info(
                'Undocked -- resubscribed to /scan')

    def _create_scan_sub(self):
        if self.scan_sub is None:
            self.scan_sub = self.create_subscription(
                LaserScan, '/scan', self.scan_cb, 10)

    def _destroy_scan_sub(self):
        if self.scan_sub is not None:
            self.destroy_subscription(self.scan_sub)
            self.scan_sub = None

    # -- Scan normalization (unchanged) --------------------------------

    def scan_cb(self, msg):
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
