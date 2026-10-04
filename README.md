# M5Stack ATOM - SwitchBot Lock Controller

Control your **SwitchBot Lock** by simply pressing the button on your **M5Stack ATOM**! 🚪🔐

This project provides a complete solution to integrate your M5Stack ATOM (ESP32) with the SwitchBot API and control a SwitchBot Lock over Wi-Fi.

## 🌟 Features

- ✅ **Deep sleep mode** - ~10uA chip consumption while idle (ESP32-PICO datasheet; the whole board draws more) vs ~80mA active
- ✅ **Wake on button press** - ESP32 wakes from deep sleep when button is pressed
- ✅ **On-demand Wi-Fi** - Connects only when needed, disconnects immediately after API response
- ✅ **Fast reconnect** - Caches Wi-Fi BSSID for ~1-2s faster reconnection after deep sleep
- ✅ **Optional static IP** - Skip DHCP negotiation for ~500ms-1s faster connection
- ✅ **Multicolor LED feedback** - Different colors indicate status and errors
- ✅ **SwitchBot API v1.1** with signed token + secret headers
- ✅ **Reliable result** - Success only when the API body reports `statusCode` 100 (HTTP 200 alone is not enough: an offline lock or hub also returns 200)
- ✅ **Auto retry** - Retries API call once on failure; on `401` resyncs NTP first (RTC drift during deep sleep)
- ✅ **Automated test suite** - 57 tests via Docker (Python 3.13 + pytest)
- ✅ **CI/CD** - GitHub Actions runs tests on push/PR
- ✅ **Complete setup guide** for VS Code + MicroPython

## 📋 Requirements

### Hardware

- **M5Stack ATOM** (ESP32-PICO-D4)
- USB Type-C cable
- **SwitchBot smart lock** (set up and working) — tested with Lock Pro and Lock Ultra
- **Atomic Battery Base** (200mAh, optional) - for portable battery-powered operation

### Software

- **MicroPython v1.24.x or later** — download from [micropython.org/download/M5STACK_ATOM](https://micropython.org/download/M5STACK_ATOM/)
- **VS Code** (optional) for editing
- `mpremote` for file upload and execution
- Python 3.x on your computer
- SwitchBot account with API token and secret (for API v1.1 signing)

## 🚀 Quick Start

### 1. Environment Setup (First Time)

Follow the full guide in **[SETUP.md](SETUP.md)** to:

- Install VS Code and the MicroPython extension
- Flash MicroPython onto your M5Stack ATOM
- Configure the development environment
- Obtain SwitchBot credentials (Token and Device ID)

### 2. Configuration

```bash
# Clone the repository
git clone https://github.com/filippolmt/m5stack-atom-switchbot-lock.git
cd m5stack-atom-switchbot-lock

# Copy and configure the settings file
cp config_template.py config.py
```

Edit `config.py` with your details:

```python
# Wi-Fi configuration
WIFI_SSID = "YourSSID"
WIFI_PASSWORD = "YourPassword"

# SwitchBot API configuration
SWITCHBOT_TOKEN = "YourToken"
SWITCHBOT_SECRET = "YourTokenSecret"
SWITCHBOT_DEVICE_ID = "YourDeviceID"

# M5Stack ATOM button GPIO (preconfigured)
BUTTON_GPIO = 39

# Optional: static IP to skip DHCP (saves ~500ms-1s per connection)
# WIFI_STATIC_IP = ("192.168.1.100", "255.255.255.0", "192.168.1.1", "8.8.8.8")
```

### 3. Upload to the Device (mpremote)

1. Connect the M5Stack ATOM via USB and identify the serial port (e.g., `/dev/cu.usbserial-XXXX` on macOS, `COM3` on Windows, `/dev/ttyUSB0` on Linux).
2. Upload the files with `mpremote` (replace the port with yours):
   ```bash
   mpremote connect /dev/cu.usbserial-XXXX cp main.py :main.py
   mpremote connect /dev/cu.usbserial-XXXX cp config.py :config.py
   ```

### 4. Run It

Execute the script via `mpremote`:

```bash
mpremote connect /dev/cu.usbserial-XXXX run main.py
```

Then press the button on the M5Stack ATOM to control the lock.

### Working from the toolbox container (RFC2217)

Docker Desktop on macOS can't pass USB devices into containers, so when working from [toolbox](https://github.com/filippolmt/toolbox) the serial port is exposed over the network from the Mac.

**On the Mac** (outside the container, restart it every session):

```bash
brew install esptool   # includes esp_rfc2217_server
esp_rfc2217_server -v /dev/cu.usbserial-XXXX
```

- While it runs it holds the serial port: stop it before using the port directly on the Mac.
- It listens on all interfaces: stop it on shared networks.
- It listens on port 2217 (default); if that is taken, pass `-p <port>` and change it in the URL below.

**In the container** (only `uv` needed):

```bash
P='rfc2217://host.docker.internal:2217?ign_set_control'

# Flash (esptool enters the bootloader on its own)
uvx esptool --port "$P" -b 115200 chip-id
uvx esptool --port "$P" -b 115200 erase-flash
uvx esptool --port "$P" -b 115200 write-flash 0x1000 M5STACK_ATOM-*.bin

# Files / REPL: use tools/mpr.py instead of plain mpremote, one command per invocation
uv run --no-project --with mpremote python tools/mpr.py connect "$P" fs ls
uv run --no-project --with mpremote python tools/mpr.py connect "$P" cp main.py :main.py
uv run --no-project --with mpremote python tools/mpr.py connect "$P" reset
```

Plain `mpremote` fails with `could not enter raw repl`: every RFC2217 connection resets the board and `main.py` deep-sleeps right after boot. `tools/mpr.py` spams Ctrl-C during boot until the `>>>` prompt shows, then hands the connection to mpremote. The `Failed to get VID/PID` warnings from esptool are harmless.

## 📁 Project Structure

```
.
├── main.py              # Main MicroPython script
├── config_template.py   # Configuration template
├── config.py            # Configuration (create locally, not in git)
├── tools/mpr.py         # mpremote wrapper for RFC2217 (toolbox container)
├── tests/               # Automated test suite (runs on CPython via Docker)
│   ├── conftest.py      # Hardware stubs + fake config injection
│   ├── test_epoch.py    # Epoch conversion & timestamp tests
│   ├── test_hmac.py     # HMAC-SHA256 (manual + stdlib paths)
│   ├── test_auth_headers.py  # API authentication headers
│   ├── test_send_command.py  # HTTP retry logic & error handling
│   ├── test_rtc_memory.py    # RTC memory serialization
│   ├── test_led.py      # LED brightness scaling
│   └── test_wifi.py     # Wi-Fi connection logic
├── Dockerfile.test      # Test runner image (Python 3.13 + pytest)
├── Makefile             # make test / make test-clean
├── pyproject.toml       # pytest configuration
├── .github/workflows/test.yml  # CI: tests on push/PR to main
├── SETUP.md             # Full setup guide
├── README.md            # This file
├── CLAUDE.md            # Guidance for Claude Code (incl. the mbedTLS constraint)
├── LICENSE              # License
└── .gitignore           # Excludes config.py and other sensitive files
```

## 🔧 How It Works

1. **On boot/reset**: Shows startup message, then enters deep sleep (~10uA)
2. **When you press the button**:
   - ESP32 wakes from deep sleep
   - **Short press (<1s)** = UNLOCK (green LED while holding)
   - **Long press (≥1s)** = LOCK (purple LED while holding)
   - Connects to Wi-Fi (fast reconnect if cached)
   - Syncs time via NTP only if the RTC year is invalid (e.g. after power-on)
   - Sends lock/unlock command to SwitchBot API and checks the `statusCode` in the response body
   - Disconnects Wi-Fi immediately after response
   - LED feedback based on result (Wi-Fi already off)
   - Returns to deep sleep
3. **Power consumption**:
   - Deep sleep: ~10uA for the ESP32 chip (RTC timer + RTC memory, per datasheet); board-level draw is higher and should be measured
   - Active (Wi-Fi + API call): ~80-150mA for 2-4 seconds
   - LED feedback: ~25mA for ~0.5s (Wi-Fi already off)

## 🎮 Button Controls

| Press Duration | Action | LED While Holding |
|----------------|--------|-------------------|
| **< 1 second** | UNLOCK | 🟢 Green |
| **≥ 1 second** | LOCK | 🟣 Purple |

## 💡 LED Color Guide

| Color | Meaning |
|-------|---------|
| 🟢 **Green (holding)** | Short press - will UNLOCK |
| 🟣 **Purple (holding)** | Long press - will LOCK |
| 🔵 **Blue** | Connecting to Wi-Fi (normal scan) |
| 🩵 **Cyan** | Fast reconnect in progress |
| 🟢 **Green (2 blinks)** | Door unlocked successfully |
| 🟣 **Purple (2 blinks)** | Door locked successfully |
| 🟡 **Yellow (4 blinks)** | Time sync error |
| 🟠 **Orange (3 blinks)** | Wi-Fi connection timeout |
| 🔴 **Red (3 blinks)** | API error (incl. lock or hub offline) |
| 🔴 **Red (6 fast blinks)** | Authentication error (401) |

## 🔋 Atomic Battery Base (Optional)

The project supports the [M5Stack Atomic Battery Base](https://docs.m5stack.com/en/atom/Atomic%20Battery%20Base) (200mAh, 3.7V) for portable battery-powered operation.

### Specifications

| Property | Value |
|----------|-------|
| Battery | 3.7V @ 200mAh LiPo |
| Boost converter | ETA9085E10 (5V output) |
| Charging IC | LGS4056HDA (USB-C, 223mA) |
| Standby current | 2.55uA (boost converter) |

### Realistic Battery Life

**Important:** The M5Stack ATOM Lite draws **4-11mA in deep sleep** (not 10uA) due to the always-on USB/serial chip. With the 200mAh battery:

- **Estimated autonomy: 18-50 hours** depending on board revision
- Wake cycle consumption (~80-150mA for 1-5s) is <0.5% of total drain
- **Sleep current dominates** — the USB/serial chip (3-5mA) is the main drain and cannot be disabled in software
- For longer battery life, consider a larger battery (750-1000mAh → 3-8 days)

### Charging

- Connect USB-C to charge (blue LED = charging, green LED = full)
- Dip switch: **boost** for normal operation, **charge** when connected to USB
- Full charge: ~1 hour at 223mA

## 📡 SwitchBot API

The project uses the SwitchBot API v1.1:

- **Endpoint**: `https://api.switch-bot.com/v1.1/devices/{deviceId}/commands`
- **Authentication**: token + secret with signed headers:
  - `Authorization`: your token
  - `nonce`: random hex string
  - `t`: Unix timestamp in milliseconds (1970 epoch)
  - `sign`: Base64(HMAC-SHA256(token + t + nonce, secret))
- **Commands**: `unlock` or `lock`

MicroPython on ESP32 uses the 2000-01-01 epoch internally. The code converts it to the Unix epoch (1970) before signing and retries an NTP sync if the RTC year looks wrong before sending a command. Since the RTC drifts during deep sleep, a `401 Unauthorized` triggers one NTP resync and a retry before reporting an auth error.

Full documentation: https://github.com/OpenWonderLabs/SwitchBotAPI

## 🔍 Monitoring and Debug

Connect to the serial terminal (115200 baud) to see:

**Fresh boot:**
```
==================================================
M5Stack ATOM Lite - SwitchBot Lock Controller
          (Deep Sleep Version)
==================================================

Device ID: XXXXXXXXXXXX
Wake button: GPIO39
Long press threshold: 1000ms

Controls:
  Short press (<1s) = UNLOCK (green LED)
  Long press  (>1s) = LOCK   (purple LED)

Entering deep sleep...
  Wake trigger: GPIO39 LOW (button press)
  Power consumption: ~10uA
==================================================
```

**Short press - UNLOCK (fast reconnect):**
```
==================================================
WAKE FROM DEEP SLEEP - Button pressed!
==================================================
Button held for 450ms
Action: UNLOCK
Fast reconnect available (ch=1)
Fast reconnect (ch=1)... OK!
  IP: 192.168.178.87
Sending UNLOCK command...
HTTP status: 200
Response: {"statusCode":100,"body":{},"message":"success"}
✓ Door unlocked successfully!

Entering deep sleep...
```

**Long press - LOCK (first boot, normal scan):**
```
==================================================
WAKE FROM DEEP SLEEP - Button pressed!
==================================================
Button held for 1552ms
Action: LOCK
Connecting to Wi-Fi: MySSID...
..........................
✓ Connected to Wi-Fi!
  IP: 192.168.178.87
  Cached ch=1 for fast reconnect
Clock seems unsynchronized (year=2000). Trying NTP...
Synchronizing time via NTP...
✓ Time synchronized via NTP (UTC).
Sending LOCK command...
HTTP status: 200
Response: {"statusCode":100,"body":{},"message":"success"}
✓ Door locked successfully!

Entering deep sleep...
```

**Lock or hub offline (HTTP 200 but command failed → red blink):**
```
Sending UNLOCK command...
HTTP status: 200
Response: {"statusCode":161,"body":{},"message":"device offline"}
✗ Command rejected by the API.
Retry 1/1...
...
✗ API error
```

Common body `statusCode` values (SwitchBot API docs): `100` success, `151` device type error, `152` device not found, `160` command not supported, `161` device offline, `171` hub offline, `190` device internal error or invalid command format.

## 🧪 Automated Tests

Tests run on standard CPython inside Docker — no MicroPython or hardware needed. Hardware modules are replaced by stubs automatically.

```bash
make test          # Build Docker image + run all tests
make test-clean    # Remove the test Docker image
```

Tests also run automatically via GitHub Actions on every push and PR to `main`.

**What's tested** (57 test cases):

| Area | Tests |
|------|-------|
| Epoch conversion | Offset constant, `unix_time_ms()` range and precision |
| HMAC-SHA256 | Manual RFC 2104 vs stdlib, long keys, empty inputs |
| Auth headers | Required keys, uppercase Base64 signature, timestamp format |
| HTTP send_command | Retry logic, body statusCode check, 401 NTP resync, response cleanup, attribute-raise resilience |
| RTC memory | Save/load roundtrip, invalid BSSID, channel bounds |
| LED brightness | `_scale()` math, clamping at 255 |
| Wi-Fi connect | Already-connected, timeout, fast reconnect, bssid fallback |

### Hardware check (required for `main.py` changes)

The tests stub the hardware and cannot reproduce the ESP32 **system heap** used by Wi-Fi/mbedTLS. Changing what `main.py` allocates at import time (new module-level functions, constants, imports, `Pin()`) can make the HTTPS call fail on the device with `MBEDTLS_ERR_MPI_ALLOC_FAILED`, even when every test passes.

After uploading a changed `main.py`, open the serial log and press the button: the change is good only if the log shows `HTTP status: 200` and `"statusCode":100`. See [CLAUDE.md](CLAUDE.md) for the rules on what is safe to change.

## 🛠️ Troubleshooting

See the **Troubleshooting** section in [SETUP.md](SETUP.md) for:

- Connection issues with the device
- Errors while flashing the firmware
- Wi-Fi connection problems
- SwitchBot API errors
- Button issues
- Memory handling

## 🔒 Security

⚠️ **IMPORTANT:**

- `config.py` contains sensitive credentials and is excluded from Git
- Do not share your Token or Secret
- Use a secure Wi-Fi network (WPA2/WPA3)
- Consider using a dedicated VLAN for IoT devices

## 🙏 Acknowledgements

- [MicroPython](https://micropython.org/) - Python for microcontrollers
- [M5Stack](https://m5stack.com/) - Quality ESP32 hardware
- [SwitchBot](https://www.switch-bot.com/) - Smart home devices
