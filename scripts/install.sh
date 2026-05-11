#!/bin/bash
# install.sh - Install TurtleBot4 FAU fleet custom scripts and services
# Usage: sudo ./install.sh
#
# This script:
#   1. Installs Python dependencies (smbus2, Pillow, i2c-tools)
#   2. Copies scripts to /opt/turtlebot4/scripts/
#   3. Copies systemd service files to /etc/systemd/system/
#   4. Enables and starts all services
#   5. Verifies each service is running
#
# Note: ROS_DOMAIN_ID and Discovery Server config are inherited from
# /etc/turtlebot4/setup.bash which is sourced by the service files.
# No per-bot configuration is needed in this script.

set -e

if [ "$EUID" -ne 0 ]; then
    echo "Error: This script must be run with sudo."
    echo "Usage: sudo $0"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
INSTALL_DIR="/opt/turtlebot4/scripts"
SERVICE_DIR="/etc/systemd/system"

# Read domain ID from setup.bash if it exists
DOMAIN_ID="(unknown)"
if [ -f /etc/turtlebot4/setup.bash ]; then
    DOMAIN_ID=$(grep ROS_DOMAIN_ID /etc/turtlebot4/setup.bash | head -1 | cut -d'"' -f2)
fi

echo "==========================================="
echo "  TurtleBot4 FAU Fleet Installer"
echo "==========================================="
echo "  ROS_DOMAIN_ID:  $DOMAIN_ID (from setup.bash)"
echo "  Install dir:    $INSTALL_DIR"
echo "==========================================="
echo ""

# Step 1: Install Python dependencies
echo "[1/5] Installing Python dependencies..."
apt install -y python3-pip i2c-tools > /dev/null 2>&1 || true
pip3 install --break-system-packages smbus2 Pillow > /dev/null 2>&1 || true
echo "       Done."

# Step 2: Copy scripts
echo "[2/5] Copying scripts to $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR"
cp "$SCRIPT_DIR/scan_normalizer.py" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/custom_display.py" "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR"/*.py
echo "       Done."

# Step 3: Copy service files
echo "[3/5] Installing systemd services..."
for svc_file in "$REPO_DIR/services/"*.service; do
    if [ -f "$svc_file" ]; then
        svc_name=$(basename "$svc_file")
        cp "$svc_file" "$SERVICE_DIR/$svc_name"
        echo "       Installed $svc_name"
    fi
done

# Step 4: Enable and start services
echo "[4/5] Enabling and starting services..."
systemctl daemon-reload
systemctl enable scan-normalizer.service 2>/dev/null
systemctl enable turtlebot4-display.service 2>/dev/null
systemctl restart scan-normalizer.service
systemctl restart turtlebot4-display.service
echo "       Done."

# Step 5: Verify
echo "[5/5] Verifying services..."
echo ""
if systemctl is-active --quiet scan-normalizer.service; then
    echo "  scan-normalizer:     RUNNING"
else
    echo "  scan-normalizer:     FAILED"
    echo "    Check logs: sudo journalctl -u scan-normalizer.service -f"
fi

if systemctl is-active --quiet turtlebot4-display.service; then
    echo "  turtlebot4-display:  RUNNING"
else
    echo "  turtlebot4-display:  FAILED"
    echo "    Check logs: sudo journalctl -u turtlebot4-display.service -f"
fi

echo ""
echo "==========================================="
echo "  Installation complete!"
echo "  ROS_DOMAIN_ID=$DOMAIN_ID (from /etc/turtlebot4/setup.bash)"
echo "==========================================="
echo ""
echo "Useful commands:"
echo "  sudo systemctl status scan-normalizer.service"
echo "  sudo systemctl status turtlebot4-display.service"
echo "  sudo journalctl -u scan-normalizer.service -f"
echo "  sudo journalctl -u turtlebot4-display.service -f"
echo ""
echo "To update later:"
echo "  cd ~/Turtlebot4_FAU && git pull"
echo "  sudo ./scripts/install.sh"
