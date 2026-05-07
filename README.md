# TurtleBot 4 Lite Fleet Installation Guide

**50-Bot Fleet | ROS 2 Humble | Fast DDS Discovery Server**
**Ubuntu 22.04 | Ignition Gazebo Fortress**

---

## Before You Begin

This guide walks you through the complete setup of one TurtleBot 4 Lite and its companion computer. Every student will perform this setup for their assigned bot. By the end, you will have a fully functional robot communicating with your PC over the fleet network using Fast DDS Discovery Server.

### Your Assigned Numbers

Each bot and companion computer has a sticker with a number from 01 to 50. All configuration values are derived from this number.

| Parameter | Value | Example (Bot 07) |
|---|---|---|
| Bot / PC number | Sticker on your hardware | 07 |
| PC hostname | `turtlebot4pc-XX` | `turtlebot4pc-07` |
| PC username | `turtlebot4` | `turtlebot4` |
| PC password | `turtlebot4` | `turtlebot4` |
| RPi hostname | `ubuntu` (do not change) | `ubuntu` |
| RPi username | `ubuntu` | `ubuntu` |
| RPi password | `turtlebot4` | `turtlebot4` |
| ROS_DOMAIN_ID | Same as bot number | `7` |
| Discovery Server ID | Same as bot number | `7` |
| Discovery Server Port | `11811` (all bots) | `11811` |
| RPi IP address | You will discover this | (found in Part 2) |

> **IMPORTANT:** Do not change the RPi hostname from `ubuntu`. The TurtleBot 4 setup scripts, upstart jobs, and all official documentation assume this default. Changing it creates subtle breakage and makes every online tutorial harder to follow. You will identify your bot by its sticker number, `ROS_DOMAIN_ID`, and IP address.

### Fleet Network Information

| Item | Value |
|---|---|
| Wi-Fi SSID | `GL-MT3000-3e8` |
| Wi-Fi Passkey | *(provided by instructor)* |
| Wi-Fi Band | 5 GHz (recommended for RPi) |

### What You Need at the Bench

- Your assigned TurtleBot 4 Lite (with sticker number)
- Your assigned companion computer (with matching sticker number)
- Charging dock for the TurtleBot
- Ethernet cable (to connect the PC to the RPi for first boot)
- MicroSD card reader (if SD card is not already in the RPi)
- USB flash drive with Ubuntu 22.04 Desktop installer (provided by instructor)

---

## Part 1: Companion Computer Setup

The companion computer (offboard PC) is your primary workstation. You will use it to run RViz, send navigation goals, launch teleop, and develop ROS 2 nodes. The TurtleBot communicates with this PC over Wi-Fi through the Discovery Server running on the RPi.

### 1.1 Install Ubuntu 22.04 Desktop

1. Insert the Ubuntu 22.04 bootable USB into your companion computer.
2. Power on the PC. Enter the BIOS/boot menu (usually F12, F2, or Del) and select the USB drive.
3. Follow the Ubuntu installer. Use the following settings:
   - Choose "Erase disk and install Ubuntu" (this will wipe the PC completely).
   - Set your name to `turtlebot4`.
   - Set the computer name (hostname) to `turtlebot4pc-XX` where XX is your bot number (e.g., `turtlebot4pc-07`).
   - Set the username to `turtlebot4`.
   - Set the password to `turtlebot4`.
4. Complete the installation, remove the USB drive, and reboot into Ubuntu.

### 1.2 First Boot Housekeeping

1. Connect the PC to the fleet Wi-Fi network:
   - SSID: `GL-MT3000-3e8`
   - Passkey: *(provided by instructor)*

2. Open a terminal (`Ctrl+Alt+T`) and update your system:

```bash
sudo apt update && sudo apt upgrade -y
```

3. Install essential tools:

```bash
sudo apt install -y git vim net-tools ssh curl wget chrony mc arp-scan
```

4. Verify your hostname:

```bash
hostnamectl
```

The "Static hostname" line should show `turtlebot4pc-XX`.

### 1.3 Install ROS 2 Humble

1. Set up the ROS 2 apt repository:

```bash
sudo apt install -y software-properties-common
sudo add-apt-repository universe
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) \
  signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
  http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
  | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
sudo apt update
```

2. Install ROS 2 Humble Desktop (full install including RViz, Gazebo plugins, and dev tools):

```bash
sudo apt install -y ros-humble-desktop
```

> **TIP:** This install can take 10-15 minutes. It includes RViz2, Gazebo, rqt, and all core ROS 2 libraries.

3. Source ROS 2 in every new terminal by adding it to `~/.bashrc`:

```bash
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

4. Install the TurtleBot 4 desktop packages and additional tools:

```bash
sudo apt install -y ros-humble-turtlebot4-desktop
sudo apt install -y ros-humble-rmw-fastrtps-cpp
sudo apt install -y ros-humble-slam-toolbox
sudo apt install -y ros-humble-rtabmap-ros
sudo apt install -y ros-humble-nav2-bringup
sudo apt install -y ros-humble-turtlebot4-navigation
sudo apt install -y ros-humble-turtlebot4-viz
sudo apt install -y ros-humble-teleop-twist-keyboard
```

5. Install the Raspberry Pi Imager (you will use this in Part 2):

```bash
sudo apt install -y rpi-imager
```

### 1.4 Verify Clock Sync

Clock synchronization between the PC, RPi, and Create 3 is critical. Drift causes TF transform failures, SLAM breakage, and silent data loss. Set this up now so it is working before you touch the robot.

1. Check that chrony is running:

```bash
sudo systemctl enable chrony
sudo systemctl start chrony
chronyc tracking
```

Look for "Leap status: Normal" and a low "System time" offset (under 1 second).

### 1.5 Checkpoint A

Before moving to Part 2, verify:

- [ ] Ubuntu 22.04 installed, hostname is `turtlebot4pc-XX`
- [ ] Username is `turtlebot4`, password is `turtlebot4`
- [ ] Connected to fleet Wi-Fi (`GL-MT3000-3e8`)
- [ ] ROS 2 Humble installed: `ros2 --help` returns usage info
- [ ] turtlebot4-desktop installed: `dpkg -l | grep turtlebot4`
- [ ] Raspberry Pi Imager installed: `rpi-imager` launches
- [ ] chrony running: `chronyc tracking` shows normal status

---

## Part 2: Raspberry Pi and TurtleBot 4 Lite Setup

In this section you will flash the RPi SD card, boot the RPi using power from the Create 3's USB-C cable, connect via ethernet from your PC, run the official TurtleBot 4 setup script, configure Discovery Server, and apply hardware-specific fixes for the Lite model.

### 2.1 Flash the SD Card

1. Remove the microSD card from the Raspberry Pi (the Pi must be powered off -- remove the bot from the dock first).
2. Insert the microSD card into your companion computer using a card reader.
3. Launch the Raspberry Pi Imager:

```bash
rpi-imager
```

4. In the Imager, select:
   - **Operating System:** Other general-purpose OS > Ubuntu > Ubuntu Server 22.04.x LTS (64-bit)
   - **Storage:** select your microSD card

> **WARNING:** Do NOT use the Imager gear icon to pre-configure Wi-Fi, hostname, or SSH. The TurtleBot 4 setup script handles all of this. Pre-configuring can conflict with the setup tool.

5. Click "Write" and wait for the image to be written and verified.
6. Remove the SD card and insert it into the powered-off Raspberry Pi.

### 2.2 First Boot of the RPi

The RPi is powered by the USB-C cable from the Create 3 base. You will connect to the RPi over ethernet from your companion PC.

1. Insert the flashed SD card into the Raspberry Pi.
2. Connect an ethernet cable between the RPi's ethernet port and your companion PC's ethernet port.
3. Place the TurtleBot on its charging dock. The Create 3 will power up, and the USB-C cable will power the RPi. The green power LED on the RPi should illuminate.
4. Wait 2-3 minutes for the RPi to complete its first boot.
5. On your companion PC, find the RPi on the ethernet link. Open a terminal and run:

```bash
# Scan for the RPi on the ethernet interface
# Find your ethernet interface name first:
ip link show
# Look for an interface like enp0s25, eno1, or eth0 (NOT wlan0)

# Then scan for neighbors:
arp-scan --interface=YOUR_ETHERNET_INTERFACE --localnet
```

> **TIP:** If `arp-scan` does not find the RPi, try:
> ```bash
> # The RPi may use a link-local address. Check:
> ip neigh show
> # Or try mDNS (may not work on first boot):
> ping ubuntu.local
> ```
>
> If none of these work, you can also check your router's admin page for a device called `ubuntu`, or as a fallback, temporarily plug a keyboard and HDMI monitor (micro HDMI cable required) into the RPi and run `ip a` directly.

6. Once you have the RPi's IP, SSH in:

```bash
ssh ubuntu@<RPI_ETHERNET_IP>
```

7. Default credentials:
   - Username: `ubuntu`
   - Password: `ubuntu`

8. You will be prompted to change the password immediately. Set the new password to `turtlebot4`.

> **IMPORTANT:** Do NOT change the hostname. Leave it as `ubuntu`.

### 2.3 Connect the RPi to Fleet Wi-Fi

Before running the TurtleBot setup script, the RPi needs internet access to download packages.

1. Edit the netplan configuration:

```bash
sudo nano /etc/netplan/50-cloud-init.yaml
```

2. Add or modify the `wlan0` section (be careful with indentation -- use spaces, not tabs):

```yaml
network:
  version: 2
  wifis:
    wlan0:
      optional: true
      dhcp4: true
      access-points:
        "GL-MT3000-3e8":
          password: "YOUR_FLEET_PASSWORD"
```

> **IMPORTANT:** Make sure `wifis:` is aligned with any existing `ethernets:` line. All indentation must be exactly 4 spaces. Do NOT use tabs.

3. Apply the network configuration:

```bash
sudo netplan apply
```

4. Wait 10-15 seconds, then verify connectivity:

```bash
ip a show wlan0
```

Look for an `inet` line showing your IP address (e.g., `192.168.X.X`).

5. **Write down this IP address.** This is your RPi IP for the rest of the setup:

| Item | Your Value |
|---|---|
| My RPi IP address (wlan0) | __________________ |
| My RPi MAC address (wlan0) | __________________ |

> **TIP:** Record the MAC address too (shown in `ip a show wlan0` on the `link/ether` line). Your instructor may use this later for DHCP reservations on the router.

6. Verify internet access:

```bash
ping -c 3 google.com
```

7. Now that Wi-Fi is working, you can disconnect the ethernet cable if you prefer to SSH over Wi-Fi going forward:

```bash
# From your PC, SSH over Wi-Fi instead:
ssh ubuntu@<RPI_WIFI_IP>
```

### 2.4 Run the TurtleBot 4 Setup Script

This is the official setup script from the `turtlebot4_setup` repository. It installs ROS 2 Humble, all TurtleBot 4 packages, and configures the RPi for use as a TurtleBot 4.

1. Run the script:

```bash
wget -qO - https://raw.githubusercontent.com/turtlebot/turtlebot4_setup/humble/scripts/turtlebot4_setup.sh | bash
```

> **WARNING:** This script takes 20-40 minutes depending on network speed. Do not interrupt it. Do not close the terminal or let SSH disconnect. If the screen blanks, press a key to wake it up.

2. When the script completes, reboot the RPi:

```bash
sudo reboot
```

3. Wait 2-3 minutes, then SSH back in (using the Wi-Fi IP you recorded):

```bash
ssh ubuntu@<RPI_WIFI_IP>
# Password: turtlebot4
```

4. Verify the setup tool is installed:

```bash
turtlebot4-setup
```

You should see the TurtleBot4 Setup menu. Press `q` to exit for now.

### 2.5 Configure Discovery Server

Now you will configure the RPi as a Discovery Server. This is the critical networking step that allows your PC to communicate with the robot without multicast flooding the fleet network.

**First, update and factory-reset the Create 3:**

The Create 3 webserver is at `192.168.186.2` and is only reachable from the RPi over the internal USB-C connection. It is NOT reachable from your companion PC. All commands in this section must be run from your SSH session on the RPi.

1. From the RPi, verify you can reach the Create 3:

```bash
curl -s http://192.168.186.2/ | head -5
```

You should see HTML output. If you get "Connection refused" or no output, the Create 3 may not be fully booted yet. Wait 1-2 minutes and try again.

2. Check the current Create 3 firmware version:

```bash
curl -s http://192.168.186.2/api/firmware-version
```

3. Perform a **factory reset** on the Create 3. This disconnects it from any Wi-Fi networks and clears all settings:

```bash
curl -X POST http://192.168.186.2/api/factory-reset
```

Wait for the Create 3 to reboot (you will hear a series of tones). This takes about 60-90 seconds.

> **IMPORTANT:** The factory reset MUST happen BEFORE configuring Discovery Server. The reset clears settings that the RPi will write to the Create 3 in the next steps. If you configure Discovery Server first and then factory reset, you will have to redo the Discovery Server configuration.

**Now configure Discovery Server on the RPi:**

3. Run the TurtleBot 4 setup tool:

```bash
turtlebot4-setup
```

4. Navigate to **ROS Setup > Bash Setup** and set:
   - `ROS_DOMAIN_ID`: your bot number (e.g., `7` for bot 07)

5. Navigate to **ROS Setup > Discovery Server** and configure:
   - Enabled: `True`
   - Onboard Server Port: `11811` (leave default)
   - Onboard Server ID: your bot number (e.g., `7` for bot 07)
   - Offboard Server IP: **leave blank** (do not set this)
   - Offboard Server Port: `11811` (leave default)
   - Offboard Server ID: leave default

> **IMPORTANT:** Leave the Offboard Server IP blank. Setting an offboard server is not recommended for this fleet because it would cause all robots to cross-communicate and overload the network.

6. Navigate to **Wi-Fi Setup** and verify:
   - Wi-Fi Mode: `Client`
   - SSID: `GL-MT3000-3e8`
   - Password: *(provided by instructor)*
   - Band: `5GHz`
   - DHCP: `True`

7. Save the settings, then select **Apply Settings** from the main menu.

> **WARNING:** Applying settings will write configuration to the Create 3, which will reboot. Your SSH session may hang if Wi-Fi settings changed. Wait 2-3 minutes for the full reboot cycle. The Create 3 will chime when it is ready.

8. After the Create 3 chimes, verify from the RPi terminal:

```bash
turtlebot4-source
ros2 daemon stop && ros2 daemon start
ros2 topic list
```

> **TIP:** You may need to run `ros2 topic list` twice. The first call starts the daemon and begins discovering topics. The second call will show the full list.

### 2.6 Configure Discovery Server on the PC

Now go back to your companion PC and configure it as a Discovery Server client pointing to your RPi.

1. On your companion PC, download and run the official configuration script:

```bash
wget -qO - https://raw.githubusercontent.com/turtlebot/turtlebot4_setup/humble/turtlebot4_discovery/configure_discovery.sh | bash <(cat) </dev/tty
```

2. The script will prompt you. Enter the following:

| Prompt | Your Value |
|---|---|
| `ROS_DOMAIN_ID` | Your bot number (e.g., `7`) |
| `Discovery Server ID` | Your bot number (e.g., `7`) |
| `Discovery Server IP` | Your RPi Wi-Fi IP address |
| `Discovery Server Port` | Press Enter for default (`11811`) |
| Done/add another? | `d` (done) |

3. After the script finishes, source your updated bashrc and restart the daemon:

```bash
source ~/.bashrc
ros2 daemon stop && ros2 daemon start
```

### 2.7 RPLidar URDF Fix (90-Degree Rotation)

The TurtleBot 4 Lite RPLidar has an incorrect rotation value in the default URDF. Without this fix, your lidar scans will be rotated 90 degrees, causing SLAM and NAV2 to produce incorrect maps and navigation behavior.

1. SSH into the RPi and edit the URDF file:

```bash
ssh ubuntu@<RPI_WIFI_IP>
sudo nano /opt/ros/humble/share/turtlebot4_description/urdf/lite/turtlebot4.urdf.xacro
```

2. Find the RPLidar joint definition. Look for the line containing the rplidar `rpy` value. It will look something like:

```xml
rpy="${pi/2} 0 0"
```

3. Change it to:

```xml
rpy="${pi} 0 0"
```

4. Save the file (`Ctrl+O`, Enter, `Ctrl+X` in nano).

> **IMPORTANT:** This fix changes `pi/2` to `pi`. The lidar is physically mounted at 180 degrees, not 90. Without this fix, your entire SLAM map will be rotated and obstacle detection will be wrong.

### 2.8 Checkpoint B

Before moving to Part 3, verify:

- [ ] RPi booted, `ubuntu` login works with password `turtlebot4`
- [ ] RPi connected to fleet Wi-Fi, IP address recorded
- [ ] TurtleBot 4 setup script completed and rebooted
- [ ] Create 3 factory reset completed BEFORE Discovery Server config (via `curl` from RPi)
- [ ] Discovery Server enabled via `turtlebot4-setup` (server ID = bot number)
- [ ] `ROS_DOMAIN_ID` set to your bot number
- [ ] Create 3 chimed after applying settings
- [ ] Discovery Server configured on the companion PC (Section 2.6)
- [ ] RPLidar URDF `rpy` changed from `pi/2` to `pi`
- [ ] SSH from PC to RPi works over Wi-Fi

---

## Part 3: End-to-End Verification

Now that both machines are configured, it is time to verify the full communication chain.

### 3.1 Verify ROS 2 Communication

1. From your companion PC, list topics:

```bash
ros2 topic list
```

You should see topics from the robot including `/scan`, `/odom`, `/cmd_vel`, and various Create 3 and OAK-D camera topics. If you see nothing, run the command again (the daemon may need a moment to discover all topics).

2. Drive the robot with teleop to confirm the full communication chain:

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

Use the keyboard controls to drive the robot forward, backward, and turn. If the robot moves, your PC-to-RPi-to-Create3 chain is working.

3. Verify the lidar:

```bash
ros2 topic echo /scan --once
```

You should see a `LaserScan` message with range data. If all ranges are `inf` or the scan appears rotated, double-check the URDF fix from Section 2.7.

4. Verify the camera (use the compressed topic for bandwidth):

```bash
ros2 topic echo /oakd/rgb/preview/image_raw/compressed --once
```

You should see a `CompressedImage` message. To view the image visually:

```bash
ros2 run rqt_image_view rqt_image_view
```

Select the `/oakd/rgb/preview/image_raw/compressed` topic in the dropdown.

### 3.2 Checkpoint C: Basic System Verification

- [ ] `ros2 topic list` shows robot topics from the PC
- [ ] `teleop_twist_keyboard` drives the robot
- [ ] `/scan` topic returns LaserScan data
- [ ] Camera compressed topic returns image data
- [ ] RPi IP address is recorded and PC Discovery Server points to it

> **NOTE:** The full SLAM test will be performed after the custom scripts are installed in Part 4, since SLAM Toolbox requires the `scan_normalizer` to handle inconsistent lidar point counts.

---


## Part 4: Custom Scripts and Services

This fleet uses custom Python scripts that run as systemd services on the RPi. All scripts, service files, and the install script are in the fleet GitHub repository at:

**https://github.com/skylargutman/turtlebot4_fau**

Students clone the repo onto the RPi and run a single install script that handles everything.

### 4.1 Clone and Install

1. SSH into the RPi:

```bash
ssh ubuntu@<RPI_WIFI_IP>
```

2. Clone the fleet repository:

```bash
cd ~
sudo apt install -y git
git clone https://github.com/skylargutman/turtlebot4_fau.git
```

3. Run the install script with your bot number:

```bash
cd ~/turtlebot4_fau
chmod +x scripts/install.sh
sudo ./scripts/install.sh <YOUR_BOT_NUMBER>
```

For example, for bot 07:

```bash
sudo ./scripts/install.sh 7
```

The install script will:
- Install Python dependencies (`smbus2`, `Pillow`, `i2c-tools`)
- Copy scripts to `/opt/turtlebot4/scripts/`
- Copy and configure systemd service files (setting your `ROS_DOMAIN_ID`)
- Enable and start all services
- Print a status report showing which services are running

4. Verify both services are active:

```bash
sudo systemctl status scan-normalizer.service
sudo systemctl status turtlebot4-display.service
```

5. To update scripts later (when the instructor pushes changes):

```bash
cd ~/turtlebot4_fau
git pull
sudo ./scripts/install.sh <YOUR_BOT_NUMBER>
```

---

### 4.2 scan_normalizer

The RPLidar occasionally produces scans with inconsistent point counts. SLAM Toolbox locks onto the first scan's count and rejects anything different, causing mapping failures. The `scan_normalizer` subscribes to `/scan`, resamples every message to a fixed 1083 readings via linear interpolation, and republishes on `/scan_normalized`. You will point SLAM Toolbox at `/scan_normalized` instead of `/scan`.

This service starts automatically on boot after the install script runs.

**To verify** (from your PC or RPi):

```bash
ros2 topic hz /scan_normalized
```

**To check logs:**

```bash
sudo journalctl -u scan-normalizer.service -f
```

---

### 4.3 LCD Display (I2C Bus 1)

All bots have a small SSD1306 OLED display connected to I2C bus 1 (not the default bus 3). The stock TurtleBot 4 display driver does not work with this wiring, so the fleet uses a custom Python script that bit-bangs the display directly using `smbus2`.

This service starts automatically on boot after the install script runs.

**To verify the hardware** (quick test from the RPi):

```bash
sudo python3 -c "
import smbus2, time
bus = smbus2.SMBus(1)
init = [0xAE, 0xD5, 0x80, 0xA8, 0x3F, 0xD3, 0x00, 0x40,
        0x8D, 0x14, 0x20, 0x00, 0xA1, 0xC8, 0xDA, 0x12,
        0x81, 0xCF, 0xD9, 0xF1, 0xDB, 0x40, 0xA4, 0xA6, 0xAF]
for c in init:
    bus.write_byte_data(0x3c, 0x00, c)
bus.write_byte_data(0x3c, 0x00, 0xA5)
time.sleep(3)
bus.write_byte_data(0x3c, 0x00, 0xAE)
print('If the screen flashed white, the display works!')
"
```

**To check logs:**

```bash
sudo journalctl -u turtlebot4-display.service -f
```

---

### 4.4 SLAM Verification Test

Now that the `scan_normalizer` service is running, you can verify SLAM. The normalizer must be active because SLAM Toolbox will fail on raw `/scan` due to inconsistent point counts.

1. Confirm the normalizer is publishing (from your PC):

```bash
ros2 topic hz /scan_normalized
```

2. Launch SLAM Toolbox using the normalized topic:

```bash
ros2 launch turtlebot4_navigation slam.launch.py scan_topic:=/scan_normalized
```

3. In a second terminal, launch RViz:

```bash
ros2 launch turtlebot4_viz view_robot.launch.py
```

4. In a third terminal, drive the robot around with teleop:

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

Drive slowly around your bench area. You should see a map building in RViz. If the map looks reasonable (walls where walls should be, no wild rotations), your full setup is complete.

5. Stop all three terminals (`Ctrl+C` in each).

### 4.5 Checkpoint D: Custom Scripts Verified

- [ ] Install script ran successfully on the RPi
- [ ] `scan-normalizer.service` is active and `/scan_normalized` is publishing
- [ ] `turtlebot4-display.service` is active and the LCD shows information
- [ ] SLAM Toolbox with `/scan_normalized` builds a correct map in RViz

---

### 4.6 AprilTag Detection Node

Instructions for installing the `apriltag_detector` ROS 2 package will be provided.

### 4.7 YOLO Human Detection Node

Instructions for installing Ultralytics YOLO and the detection ROS 2 node will be provided.

### 4.8 NAV2 Launch Configuration

Instructions for the two-step NAV2 launch process (localization first, then nav2) will be provided.

### 4.9 Additional Scripts

Any additional scripts will be added to the repository. After a `git pull`, re-run the install script to deploy them.

---

## Part 5: Troubleshooting

These are common problems encountered during setup and operation, along with their fixes. Many of these were discovered the hard way during development.

### Empty `ros2 topic list`

**Symptom:** `ros2 topic list` returns nothing or only `/parameter_events` and `/rosout`.

**Cause:** The ROS 2 daemon has stale state, or the Discovery Server connection is not established.

**Fix:**

```bash
ros2 daemon stop && ros2 daemon start
ros2 topic list    # run this twice
```

If still empty, verify:
- `ROS_DISCOVERY_SERVER` in your terminal matches the RPi IP: `echo $ROS_DISCOVERY_SERVER`
- `ROS_DOMAIN_ID` matches on both PC and RPi: `echo $ROS_DOMAIN_ID`
- `RMW_IMPLEMENTATION` is `rmw_fastrtps_cpp` on both machines: `echo $RMW_IMPLEMENTATION`
- The RPi is actually on the network: `ping <RPI_IP>`

### Lidar Scans Appear Rotated

**Symptom:** The SLAM map is rotated 90 degrees. Walls appear in the wrong places.

**Cause:** The RPLidar URDF `rpy` value was not updated (still set to `pi/2` instead of `pi`).

**Fix:** Follow Section 2.7. Edit the URDF on the RPi and restart the robot upstart job:

```bash
turtlebot4-setup
# Navigate to ROS Setup > Robot Upstart > Restart
```

### Create 3 Does Not Chime After Applying Settings

**Symptom:** After applying Discovery Server settings, the Create 3 never chimes and topics do not appear.

**Cause:** Clock drift between the PC, RPi, and Create 3, or the factory reset was not performed before configuring Discovery Server.

**Fix:**
- Power cycle the entire robot: remove it from the dock, wait 10 seconds, place it back.
- Verify chrony/NTP is running on both PC and RPi.
- If the problem persists, re-do the Create 3 factory reset from the webserver, then re-apply Discovery Server settings from `turtlebot4-setup`.

### Camera Images Are Laggy or Dropping

**Symptom:** `rqt_image_view` shows very delayed or frozen images from the OAK-D camera.

**Cause:** Raw image topics consume too much bandwidth over Wi-Fi.

**Fix:** Always use the compressed image topic:

```
/oakd/rgb/preview/image_raw/compressed
```

If you still experience issues, you may need to increase the Fast DDS send/receive buffer sizes. Create or edit a Fast DDS XML config file on the RPi and set the buffer sizes to at least 1MB.

### NAV2 Fails to Navigate

**Symptom:** NAV2 does not accept goals, or the robot does not move toward the goal.

**Cause:** The NAV2 launch order matters. Localization must start before the navigation stack.

**Fix:** Launch in this order, each in a separate terminal:

```bash
# Terminal 1: Localization (with your saved map)
ros2 launch turtlebot4_navigation localization.launch.py \
  map:=/path/to/your/map.yaml

# Terminal 2: Navigation (after localization is running)
ros2 launch turtlebot4_navigation nav2.launch.py
```

### Map Saving Fails or Produces Empty Map

**Symptom:** The saved map PGM file is all gray or contains no data.

**Cause:** The map_saver timed out before the map was fully received, or it was listening on the wrong topic.

**Fix:** Use explicit timeout and topic remapping:

```bash
ros2 run nav2_map_server map_saver_cli -f ~/maps/my_map \
  -p save_map_timeout:=10.0
```

If using RTAB-Map (which publishes to `/rtabmap/map` instead of `/map`), add the remap:

```bash
ros2 run nav2_map_server map_saver_cli -f ~/maps/my_map \
  -p save_map_timeout:=10.0 -r map:=/rtabmap/map
```

### RMW Mismatch Between Machines

**Symptom:** PC and RPi are on the same network and same domain ID, but cannot see each other's topics.

**Cause:** One machine is using `rmw_cyclonedds_cpp` while the other uses `rmw_fastrtps_cpp`. Discovery Server requires Fast DDS on all machines.

**Fix:** On every machine, verify:

```bash
echo $RMW_IMPLEMENTATION
# Must show: rmw_fastrtps_cpp
```

If it shows `cyclonedds` or is empty, update your `setup.bash` and re-source it.

### LCD Display Not Working

**Symptom:** The small OLED screen on the Lite bot shows nothing.

**Cause:** The display is on I2C bus 1 but the default TurtleBot 4 software expects bus 3. The stock display driver will not work with this fleet's wiring. You must use the custom Python display script (see Section 4.3).

**Fix:**
1. Verify the display is detected: `i2cdetect -y 1` (look for `0x3c`)
2. Run the quick hardware test from Section 4.3 to confirm the display physically works
3. Check that the custom display service is running: `sudo systemctl status turtlebot4-display.service`
4. Check the service logs: `sudo journalctl -u turtlebot4-display.service -f`

---

## Part 6: Student Setup Worksheet

Fill in this worksheet as you complete each section. Keep it at your bench for reference.

| Item | Your Value |
|---|---|
| Student name | |
| Bot number (sticker) | |
| PC hostname | `turtlebot4pc-` |
| RPi hostname | `ubuntu` |
| RPi password (new) | `turtlebot4` |
| ROS_DOMAIN_ID | |
| Discovery Server ID | |
| RPi IP address (wlan0) | |
| RPi MAC address (wlan0) | |
| Create 3 firmware version | |

### Completion Checklist

Have your instructor initial each section when complete:

| Section | Description | Instructor Init. |
|---|---|---|
| Part 1 | Companion PC: Ubuntu + ROS 2 + tools installed | |
| Part 2.1-2.4 | RPi: flashed, setup script run, rebooted | |
| Part 2.5-2.6 | Discovery Server configured on RPi and PC | |
| Part 2.7 | URDF lidar fix applied | |
| Part 3 | PC connected to robot, teleop drives the bot | |
| Part 4.1-4.3 | Fleet scripts installed, both services running | |
| Part 4.4 | SLAM test with /scan_normalized passes | |

### Quick Reference Commands

**SSH into RPi:**
```bash
ssh ubuntu@<RPI_IP>
```

**Restart ROS 2 daemon (run on both PC and RPi when things look stale):**
```bash
ros2 daemon stop && ros2 daemon start
```

**Check environment variables:**
```bash
echo $ROS_DOMAIN_ID
echo $RMW_IMPLEMENTATION
echo $ROS_DISCOVERY_SERVER
```

**Run TurtleBot 4 setup tool (on RPi only):**
```bash
turtlebot4-setup
```

**Drive the robot:**
```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

**View camera feed:**
```bash
ros2 run rqt_image_view rqt_image_view
```

**Check lidar:**
```bash
ros2 topic echo /scan --once
```

**Launch SLAM:**
```bash
ros2 launch turtlebot4_navigation slam.launch.py scan_topic:=/scan_normalized
```

**Launch RViz:**
```bash
ros2 launch turtlebot4_viz view_robot.launch.py
```

**Save a map:**
```bash
ros2 run nav2_map_server map_saver_cli -f ~/maps/my_map -p save_map_timeout:=10.0
```

---

## References

- [TurtleBot 4 User Manual](https://turtlebot.github.io/turtlebot4-user-manual/)
- [TurtleBot 4 Setup (GitHub, Humble branch)](https://github.com/turtlebot/turtlebot4_setup/tree/humble)
- [TurtleBot 4 Discovery Server Guide](https://turtlebot.github.io/turtlebot4-user-manual/setup/discovery_server.html)
- [TurtleBot 4 Networking Guide](https://turtlebot.github.io/turtlebot4-user-manual/setup/networking.html)
- [TurtleBot 4 Multiple Robots Tutorial](https://turtlebot.github.io/turtlebot4-user-manual/tutorials/multiple_robots.html)
- [ROS 2 Humble Documentation](https://docs.ros.org/en/humble/index.html)
