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
| RPi ethernet IP | `10.0.0.XX` (XX = bot number) | `10.0.0.7` |
| PC ethernet IP | `10.0.0.2XX` (2XX = 200 + bot number) | `10.0.0.207` |
| ROS_DOMAIN_ID | Same as bot number | `7` |
| Discovery Server ID | `0` (all bots) | `0` |
| Discovery Server Port | `11811` (all bots) | `11811` |

> **IMPORTANT:** Do not change the RPi hostname from `ubuntu`. The TurtleBot 4 setup scripts, upstart jobs, and all official documentation assume this default. Changing it creates subtle breakage and makes every online tutorial harder to follow. You will identify your bot by its sticker number, `ROS_DOMAIN_ID`, and IP address.

### Fleet Network Information

| Item | Value |
|---|---|
| Wi-Fi SSID (5 GHz, for RPi) | `GL-MT3000-3e8-5G` |
| Wi-Fi SSID (2.4 GHz, for Create 3) | `GL-MT3000-3e8` |
| Wi-Fi Passkey | *(provided by instructor)* |

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
   - SSID: `GL-MT3000-3e8-5G`
   - Passkey: *(provided by instructor)*

2. Open a terminal (`Ctrl+Alt+T`) and update your system:

```bash
sudo apt update && sudo apt upgrade -y
```

3. Install essential tools:

```bash
sudo apt install -y git vim net-tools ssh curl wget chrony mc arp-scan nmap
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
sudo apt install -y ros-humble-irobot-create-msgs
sudo apt install -y ros-humble-irobot-create-description
sudo apt install -y ros-humble-image-transport-plugins
```

> **IMPORTANT:** The `irobot-create-msgs` package is required to deserialize Create 3 messages on the PC. Without it, topics like `/odom`, `/dock_status`, and `/wheel_status` will appear as "invalid message type" errors.

5. Install the Raspberry Pi Imager (you will use this in Part 2):

```bash
sudo apt install -y rpi-imager
```

### 1.4 Configure PC Ethernet for Direct RPi Connection

You will connect to the RPi via a direct ethernet cable during setup. Configure your PC's ethernet port with a static IP now so it is ready when you need it.

1. Find your ethernet interface name:

```bash
ip link show
```

Look for an interface like `eno1`, `enp0s25`, or `eth0` (NOT `wlan0`).

2. Create a NetworkManager connection profile with a static IP:

```bash
sudo nmcli connection add type ethernet con-name pi-direct \
  ifname <YOUR_ETHERNET_INTERFACE> \
  ipv4.method manual \
  ipv4.addresses 10.0.0.2XX/24
```

Replace `<YOUR_ETHERNET_INTERFACE>` with your interface name (e.g., `eno1`), and replace `XX` with your bot number. For example, bot 07:

```bash
sudo nmcli connection add type ethernet con-name pi-direct \
  ifname eno1 \
  ipv4.method manual \
  ipv4.addresses 10.0.0.207/24
```

This connection will activate automatically whenever you plug an ethernet cable into the PC.

### 1.5 Verify Clock Sync

Clock synchronization between the PC, RPi, and Create 3 is critical. Drift causes TF transform failures, SLAM breakage, and silent data loss. Set this up now so it is working before you touch the robot.

1. Check that chrony is running:

```bash
sudo systemctl enable chrony
sudo systemctl start chrony
chronyc tracking
```

Look for "Leap status: Normal" and a low "System time" offset (under 1 second).

### 1.6 Checkpoint A

Before moving to Part 2, verify:

- [ ] Ubuntu 22.04 installed, hostname is `turtlebot4pc-XX`
- [ ] Username is `turtlebot4`, password is `turtlebot4`
- [ ] Connected to fleet Wi-Fi (`GL-MT3000-3e8-5G`)
- [ ] ROS 2 Humble installed: `ros2 --help` returns usage info
- [ ] turtlebot4-desktop installed: `dpkg -l | grep turtlebot4`
- [ ] Raspberry Pi Imager installed: `rpi-imager` launches
- [ ] Ethernet connection `pi-direct` created: `nmcli connection show pi-direct`
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

5. Click the **gear icon** (or Edit Settings) and configure the following:
   - **Hostname:** `ubuntu`
   - **Enable SSH:** Yes, use password authentication
   - **Username:** `ubuntu`
   - **Password:** `turtlebot4`
   - **Configure wireless LAN:**
     - SSID: `GL-MT3000-3e8-5G`
     - Password: *(provided by instructor)*
     - Wireless LAN country: `US`
   - **Locale settings:** Timezone `America/New_York`

6. Click **Save**, then click **Write** and wait for the image to be written and verified.
7. The Imager will automatically unmount the SD card when finished. Remove and reinsert the SD card reader to remount it for the next step.

### 2.2 Pre-Configure the SD Card

After flashing, the SD card has a partition called `writable`. Mount it and make additional edits before first boot.

1. Find the writable partition:

```bash
# Check where it mounted (look for "writable")
lsblk
# Usually something like /media/turtlebot4/writable
```

2. **Copy default shell configuration files.** On a fresh Ubuntu Server image, the `/etc/skel` files are not always copied to the `ubuntu` user's home directory. Fix this now:

```bash
sudo cp /media/turtlebot4/writable/etc/skel/.bashrc /media/turtlebot4/writable/home/ubuntu/
sudo cp /media/turtlebot4/writable/etc/skel/.profile /media/turtlebot4/writable/home/ubuntu/
sudo cp /media/turtlebot4/writable/etc/skel/.bash_logout /media/turtlebot4/writable/home/ubuntu/
sudo chown -R 1000:1000 /media/turtlebot4/writable/home/ubuntu/
```

3. **Configure the ethernet static IP.** Create the ethernet netplan file so the RPi gets a known IP on first boot (substitute your bot number for XX):

```bash
sudo nano /media/turtlebot4/writable/etc/netplan/40-ethernets.yaml
```

Enter the following:

```yaml
network:
  version: 2
  renderer: networkd
  ethernets:
    eth0:
      addresses:
        - 10.0.0.XX/24
      dhcp4: false
      optional: false
    usb0:
      addresses:
        - 192.168.186.3/24
      dhcp4: false
      optional: false
```

For example, bot 07 would use `10.0.0.7/24`.

> **IMPORTANT:** The `usb0` interface is the internal USB-C connection between the RPi and the Create 3. The Create 3 webserver is at `192.168.186.2` on this interface. Do not change the `usb0` address.

4. **Set file permissions** on the netplan file:

```bash
sudo chmod 600 /media/turtlebot4/writable/etc/netplan/40-ethernets.yaml
```

> **IMPORTANT:** Use spaces only, not tabs in YAML files. Each indent level is exactly 2 spaces.

5. **Copy your SSH public key to the SD card.** This allows passwordless SSH login.

First, generate an SSH key on your PC if you don't already have one:

```bash
# Check if you already have a key:
ls ~/.ssh/id_rsa.pub

# If the file does not exist, generate one:
ssh-keygen -t rsa -b 4096
# Press Enter to accept defaults, no passphrase needed for lab use
```

Then copy the key to the SD card:

```bash
sudo mkdir -p /media/turtlebot4/writable/home/ubuntu/.ssh
sudo cp ~/.ssh/id_rsa.pub /media/turtlebot4/writable/home/ubuntu/.ssh/authorized_keys
sudo chown -R 1000:1000 /media/turtlebot4/writable/home/ubuntu/.ssh
sudo chmod 700 /media/turtlebot4/writable/home/ubuntu/.ssh
sudo chmod 600 /media/turtlebot4/writable/home/ubuntu/.ssh/authorized_keys
```

6. Eject the SD card and insert it into the powered-off Raspberry Pi.

### 2.3 First Boot of the RPi

The RPi is powered by the USB-C cable from the Create 3 base. You will connect to the RPi over ethernet from your companion PC using the static IP you configured on the SD card. The RPi will also connect to the fleet Wi-Fi automatically (configured by the Imager).

1. Insert the flashed SD card into the Raspberry Pi.
2. Connect an ethernet cable between the RPi's ethernet port and your companion PC's ethernet port.
3. Place the TurtleBot on its charging dock. The Create 3 will power up, and the USB-C cable will power the RPi. The green power LED on the RPi should illuminate.
4. Wait 2-3 minutes for the RPi to complete its first boot.
5. SSH into the RPi using the static IP you set in Section 2.2:

```bash
ssh ubuntu@10.0.0.XX
```

For example, bot 07:

```bash
ssh ubuntu@10.0.0.7
```

> **TIP:** If SSH fails with "Connection refused", the RPi is still booting. Wait another minute and try again.

6. You will be logged in via your SSH key with no password prompt.

> **IMPORTANT:** Do NOT change the hostname. Leave it as `ubuntu`.

7. **Enable the USB gadget ethernet interface** so the RPi can communicate with the Create 3 over USB:

```bash
sudo nano /boot/firmware/config.txt
```

Find the line:

```
dtoverlay=dwc2
```

Change it to:

```
dtoverlay=dwc2,dr_mode=peripheral
```

Then add the ethernet gadget kernel module:

```bash
echo "g_ether" | sudo tee -a /etc/modules
```

8. **Install smbus2** for the LCD display (needed later in Part 4):

```bash
sudo pip3 install --break-system-packages smbus2 Pillow
```

9. **Update the system:**

```bash
sudo apt update && sudo apt upgrade -y
```

10. Reboot to apply the USB gadget changes:

```bash
sudo reboot
```

11. Wait 2-3 minutes, then SSH back in:

```bash
ssh ubuntu@10.0.0.XX
```

12. Verify the USB gadget interface is active:

```bash
ip a show usb0
```

You should see the `usb0` interface with the `192.168.186.3/24` address.

13. Verify Wi-Fi connected automatically:

```bash
ip a show wlan0
```

Look for an `inet` line showing your Wi-Fi IP address (e.g., `192.168.X.X`).

14. **Write down the Wi-Fi IP address:**

| Item | Your Value |
|---|---|
| My RPi IP address (wlan0) | __________________ |
| My RPi MAC address (wlan0) | __________________ |

> **TIP:** Record the MAC address too (shown in `ip a show wlan0` on the `link/ether` line). Your instructor may use this later for DHCP reservations on the router.

15. Verify internet access:

```bash
ping -c 3 google.com
```

### 2.4 Run the TurtleBot 4 Setup Script

This is the official setup script from the `turtlebot4_setup` repository. It installs ROS 2 Humble, all TurtleBot 4 packages, and configures the RPi for use as a TurtleBot 4.

1. Run the script:

```bash
wget -qO - https://raw.githubusercontent.com/turtlebot/turtlebot4_setup/humble/scripts/turtlebot4_setup.sh | bash
```

> **WARNING:** This script takes 20-40 minutes depending on network speed. Partway through, the script will detect that you are not running the official TurtleBot 4 image and your SSH session will crash. This is expected. Do not panic.

2. **When your SSH session crashes**, open a new terminal on your PC and SSH back in:

```bash
ssh ubuntu@10.0.0.XX
```

3. Reboot the RPi:

```bash
sudo reboot
```

4. Wait 2-3 minutes, then SSH back in and run the setup script again:

```bash
ssh ubuntu@10.0.0.XX
wget -qO - https://raw.githubusercontent.com/turtlebot/turtlebot4_setup/humble/scripts/turtlebot4_setup.sh | bash
```

The script will pick up where it left off and complete the installation.

5. **Before rebooting**, you must fix the network configuration. The setup script overwrites the netplan files with defaults that will break your connection. Edit the ethernet config:

```bash
sudo nano /etc/netplan/40-ethernets.yaml
```

Replace the contents with the following (substitute your bot number for XX):

```yaml
network:
  version: 2
  renderer: networkd
  ethernets:
    eth0:
      addresses:
        - 10.0.0.XX/24
      dhcp4: false
      optional: false
    usb0:
      addresses:
        - 192.168.186.3/24
      dhcp4: false
      optional: false
```

Then edit the Wi-Fi config:

```bash
sudo nano /etc/netplan/50-wifis.yaml
```

Make sure it contains your fleet Wi-Fi settings (get the password from your instructor):

```yaml
network:
  version: 2
  renderer: networkd
  wifis:
    wlan0:
      optional: true
      dhcp4: true
      access-points:
        "GL-MT3000-3e8-5G":
          password: "YOUR_FLEET_PASSWORD"
```

Set permissions on both files:

```bash
sudo chmod 600 /etc/netplan/40-ethernets.yaml
sudo chmod 600 /etc/netplan/50-wifis.yaml
```

6. Install chrony for clock synchronization (critical for SLAM, TF transforms, and Create 3 communication):

```bash
sudo apt install -y chrony
sudo systemctl enable chrony
sudo systemctl start chrony
```

7. Now reboot:

```bash
sudo reboot
```

8. Wait 2-3 minutes, then SSH back in. Try the ethernet IP first, and if that works, also verify the Wi-Fi IP:

```bash
ssh ubuntu@10.0.0.XX
# Once logged in:
ip a show wlan0
chronyc tracking
```

Verify that `wlan0` has an IP address and chrony shows "Leap status: Normal".

9. Verify the setup tool is installed:

```bash
turtlebot4-setup
```

You should see the TurtleBot4 Setup menu. Press `q` to exit for now.

### 2.5 Configure Discovery Server

Now you will configure the RPi as a Discovery Server. This is the critical networking step that allows your PC to communicate with the robot without multicast flooding the fleet network.

**First, access the Create 3 webserver from your PC:**

The Create 3 webserver is at `192.168.186.2` over the internal USB-C connection between the RPi and the Create 3. The PC cannot reach this address directly because the network is internal to the bot. You will use SSH port forwarding to tunnel the webserver to your PC's browser.

1. From your PC, open a new terminal and start an SSH tunnel:

```bash
ssh -L 8080:192.168.186.2:80 ubuntu@10.0.0.XX
```

For example, bot 42:

```bash
ssh -L 8080:192.168.186.2:80 ubuntu@10.0.0.42
```

This forwards your PC's `localhost:8080` to the Create 3's webserver. Leave this terminal open for the rest of this section.

2. In your PC's web browser, open:

```
http://localhost:8080
```

You should see the Create 3 webserver landing page. From here you can navigate using the menu.

3. **Update the firmware.** The firmware update link in the Create 3 webserver does not work. Download firmware version **H.2.6** manually from:

**https://iroboteducation.github.io/create3_docs/releases/overview/**

Then navigate to **Update** in the webserver menu and upload the firmware file. The Create 3 will reboot when complete (60-90 seconds, you will hear tones).

4. **Factory reset the Create 3.** Navigate to **About** > **Reset**. Click "Reset to Factory Default". The Create 3 will reboot again.

> **IMPORTANT:** The factory reset MUST happen BEFORE configuring Discovery Server. The reset clears settings that the RPi will write to the Create 3 in the next steps. If you configure Discovery Server first and then factory reset, you will have to redo the Discovery Server configuration.

> **TIP:** When the Create 3 reboots, your SSH tunnel may hang briefly while the USB connection re-establishes. If the browser shows "connection refused", wait 30 seconds and refresh.

5. **Enable odometry TF publishing.** After the factory reset completes, navigate to **Application** > **Configuration** in the webserver menu. Scroll down to the parameters section. In the text box, add the following YAML:

```yaml
robot_state:
  ros__parameters:
    publish_odometry_tfs: true
    publish_tf: true
```

Click **Save**, then click **Restart Application**.

> **IMPORTANT:** Without these parameters, the Create 3 publishes the `/odom` topic but does not publish the corresponding TF transform from `odom` to `base_link`. SLAM and NAV2 will fail silently because the TF tree is broken. This is a non-obvious gotcha that has cost hours of debugging.

**Now configure Discovery Server on the RPi:**

6. In your existing SSH session on the RPi (or open a new one), run the TurtleBot 4 setup tool:

```bash
turtlebot4-setup
```

7. Navigate to **ROS Setup > Bash Setup** and set:
   - `ROS_DOMAIN_ID`: your bot number (e.g., `7` for bot 07)
   - `TURTLEBOT4_DIAGNOSTICS`: `False` (disable diagnostics to save CPU on the RPi)
   - `ROS_NAMESPACE`: leave blank

8. Navigate to **ROS Setup > Discovery Server** and configure:
   - Enabled: `True`
   - Onboard Server Port: `11811` (leave default)
   - Onboard Server ID: `0` (leave default)
   - Offboard Server IP: **leave blank** (do not set this)
   - Offboard Server Port: `11811` (leave default)
   - Offboard Server ID: leave default

> **IMPORTANT:** Leave the Offboard Server IP blank. Setting an offboard server is not recommended for this fleet because it would cause all robots to cross-communicate and overload the network.

9. Navigate to **Wi-Fi Setup** and configure:
   - Wi-Fi Mode: `Client`
   - SSID: `GL-MT3000-3e8`
   - Password: *(provided by instructor)*
   - Band: `Any` (the Create 3 only supports 2.4 GHz)
   - DHCP: `True`

> **NOTE:** The Create 3 only supports 2.4 GHz Wi-Fi, so use the `GL-MT3000-3e8` SSID (not the 5G version). The RPi connects to the 5G network separately via netplan.

10. Save the settings, then select **Apply Settings** from the main menu.

> **WARNING:** Applying settings will write configuration to the Create 3, which will reboot. Your SSH session may hang if Wi-Fi settings changed. Wait 2-3 minutes for the full reboot cycle. The Create 3 will chime when it is ready.

11. After the Create 3 chimes, go back into `turtlebot4-setup` and navigate to **About > Model**. Select `lite`.

12. Verify from the RPi terminal:

```bash
turtlebot4-source
ros2 daemon stop && ros2 daemon start
ros2 topic list
```

> **TIP:** You may need to run `ros2 topic list` twice. The first call starts the daemon and begins discovering topics. The second call will show the full list.

> **REFERENCE:** Full Create 3 webserver documentation: https://iroboteducation.github.io/create3_docs/webserver/overview/

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
| `Discovery Server ID` | `0` |
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
- [ ] RPi connected to fleet Wi-Fi, Wi-Fi IP address recorded
- [ ] RPi ethernet static IP `10.0.0.XX` working
- [ ] `usb0` interface active with `192.168.186.3/24`
- [ ] TurtleBot 4 setup script completed (ran twice: crash, reboot, re-run)
- [ ] Netplan files updated with correct settings after setup script
- [ ] Chrony installed and running on the RPi: `chronyc tracking`
- [ ] Create 3 firmware updated to H.2.6 and factory reset (via SSH tunnel + browser)
- [ ] Create 3 `publish_odometry_tfs` parameters set to `true`
- [ ] Discovery Server enabled via `turtlebot4-setup` (server ID = 0)
- [ ] `ROS_DOMAIN_ID` set to your bot number
- [ ] Model set to `lite` in About menu
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

**https://github.com/skylargutman/Turtlebot4_FAU**

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
git clone https://github.com/skylargutman/Turtlebot4_FAU.git
```

3. Run the install script:

```bash
cd ~/Turtlebot4_FAU
chmod +x scripts/install.sh
sudo ./scripts/install.sh
```

The install script will:
- Install Python dependencies (`smbus2`, `Pillow`, `i2c-tools`)
- Copy scripts to `/opt/turtlebot4/scripts/`
- Copy systemd service files to `/etc/systemd/system/`
- Enable and start all services
- Print a status report showing which services are running

> **NOTE:** The services inherit all ROS 2 configuration (domain ID, Discovery Server, RMW) from `/etc/turtlebot4/setup.bash`, which was written by `turtlebot4-setup` in Section 2.5. No per-bot configuration is needed in the install script.

4. Verify both services are active:

```bash
sudo systemctl status scan-normalizer.service
sudo systemctl status turtlebot4-display.service
```

5. To update scripts later (when the instructor pushes changes):

```bash
cd ~/Turtlebot4_FAU
git pull
sudo ./scripts/install.sh
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

### SSH Crashes During TurtleBot 4 Setup Script

**Symptom:** Your SSH session freezes or disconnects partway through running `turtlebot4_setup.sh`.

**Cause:** The setup script detects you are not running the official TurtleBot 4 image and exits abruptly, which kills your SSH session.

**Fix:** This is expected behavior. Open a new terminal on your PC, SSH back in via the ethernet IP (`ssh ubuntu@10.0.0.XX`), reboot (`sudo reboot`), and re-run the script. It will pick up where it left off.

### Lost Network After Setup Script / Reboot

**Symptom:** After running `turtlebot4_setup.sh` and rebooting, the RPi is unreachable via SSH on both ethernet and Wi-Fi.

**Cause:** The setup script overwrites `40-ethernets.yaml` and `50-wifis.yaml` with default values that do not have your static IP or Wi-Fi credentials. If you rebooted without editing these files, the RPi has no usable network config.

**Fix:** You need to re-edit the SD card. Power off the bot, pull the SD card, mount it on your PC, and edit both files:
- `/media/turtlebot4/writable/etc/netplan/40-ethernets.yaml`: add your static `10.0.0.XX/24` address (and `usb0` config)
- `/media/turtlebot4/writable/etc/netplan/50-wifis.yaml`: add the fleet SSID and password

Eject, reinsert, and boot again. To avoid this in the future, always edit these files before rebooting after the setup script completes (see Section 2.4).

### "Invalid message type" for Create 3 Topics

**Symptom:** Running `ros2 topic echo /dock_status` (or `/wheel_status`, `/odom`, etc.) on the PC returns "The message type 'irobot_create_msgs/msg/...' is invalid". `/odom` may not appear in `ros2 topic list` at all.

**Cause:** The PC is missing the `irobot_create_msgs` package. The TurtleBot 4 desktop meta-package does not always pull this in.

**Fix:** Install the Create 3 message and description packages on the PC:

```bash
sudo apt install -y ros-humble-irobot-create-msgs ros-humble-irobot-create-description
ros2 daemon stop && ros2 daemon start
```

Then `/odom` should appear in `ros2 topic list` and topic echos will work properly.

### Missing odom -> base_link TF Transform

**Symptom:** `/odom` topic publishes data, but `ros2 run tf2_ros tf2_echo odom base_link` returns "frame does not exist". SLAM Toolbox or NAV2 fails silently or rejects scans. RViz cannot locate the robot in the world.

**Cause:** The Create 3 does not publish the TF transform from `odom` to `base_link` by default.

**Fix:** Open the Create 3 webserver via SSH tunnel (see Section 2.5) and navigate to **Application** > **Configuration**. Scroll down to the parameters section and add:

```yaml
robot_state:
  ros__parameters:
    publish_odometry_tfs: true
    publish_tf: true
```

Save and restart the application. Verify the fix:

```bash
ros2 run tf2_ros tf2_echo odom base_link
```

You should see translation/rotation values that update as the robot moves.

### Finding the Create 3's Wi-Fi IP Address

**When needed:** If you want to access the Create 3 webserver from your PC's browser without SSH tunneling, the Create 3 needs to be on Wi-Fi and you need its IP address.

**Note:** With Discovery Server enabled, the Create 3 does not need to be on Wi-Fi for normal operation. All ROS 2 traffic goes through the RPi. This is mainly useful for firmware updates or webserver access.

**To find the Create 3 on the fleet network**, run a subnet scan from the RPi or your PC:

```bash
nmap -sn 192.168.8.0/24
```

The Create 3 will appear as a device with an iRobot OUI in the MAC address. You can also identify it by elimination (look for an unknown device on the subnet that is not your PC, RPi, or other known devices).

**The recommended approach** for accessing the Create 3 webserver is SSH port forwarding (no Wi-Fi needed):

```bash
ssh -L 8080:192.168.186.2:80 ubuntu@10.0.0.XX
# Then in your PC browser: http://localhost:8080
```

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

### RPLidar Buffer Overflow / No /dev/ttyUSB0

**Symptom:** The `rplidar_composition` node crashes immediately with "buffer overflow detected" and `/dev/ttyUSB0` does not exist.

**Cause:** The RPLidar interface board (the small PCB between the lidar and the USB cable) is faulty. This is a hardware failure, not a software issue.

**Fix:** Replace the RPLidar interface board. After replacing, verify the lidar is detected:

```bash
lsusb | grep -i "cp210\|silicon"
ls /dev/ttyUSB0
```

You should see a Silicon Labs CP210x device in `lsusb` and `/dev/ttyUSB0` should exist.

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
| PC ethernet IP | `10.0.0.` |
| RPi hostname | `ubuntu` |
| RPi ethernet IP | `10.0.0.` |
| RPi Wi-Fi IP (wlan0) | |
| RPi MAC address (wlan0) | |
| ROS_DOMAIN_ID | |
| Discovery Server ID | `0` |
| Create 3 firmware version | H.2.6 |

### Completion Checklist

Have your instructor initial each section when complete:

| Section | Description | Instructor Init. |
|---|---|---|
| Part 1 | Companion PC: Ubuntu + ROS 2 + tools + ethernet config | |
| Part 2.1-2.3 | RPi: flashed, SD card configured, first boot SSH works, Wi-Fi connected | |
| Part 2.4 | RPi: setup script run, rebooted | |
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

**SSH tunnel to Create 3 webserver:**
```bash
ssh -L 8080:192.168.186.2:80 ubuntu@10.0.0.XX
# Then browse: http://localhost:8080
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
- [iRobot Create 3 Documentation](https://iroboteducation.github.io/create3_docs/)
- [iRobot Create 3 Webserver Reference](https://iroboteducation.github.io/create3_docs/webserver/overview/)
- [iRobot Create 3 Firmware Releases](https://iroboteducation.github.io/create3_docs/releases/overview/)
- [iRobot Create 3 ROS 2 Topics](https://iroboteducation.github.io/create3_docs/api/ros2/)
- [ROS 2 Humble Documentation](https://docs.ros.org/en/humble/index.html)
