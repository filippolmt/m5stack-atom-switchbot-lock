# AGENTS.md

MicroPython firmware for M5Stack ATOM Lite (ESP32-PICO-D4) controlling a SwitchBot Lock via API v1.1. Single file (`main.py`), deep sleep between button presses. Short press = UNLOCK, long press (≥1s) = LOCK. Config lives in `config.py` (git-ignored, from `config_template.py`).

## Commands

```bash
make test                                                  # full suite in Docker
uvx --with pytest pytest tests/test_wifi.py::test_name -v  # single test, no Docker

# Flash firmware at 115200 baud — 460800 causes disconnects on some boards
esptool --port $PORT --baud 115200 erase-flash
esptool --port $PORT --baud 115200 write_flash 0x1000 M5STACK_ATOM-*.bin

mpremote connect $PORT cp main.py :main.py
```

From the toolbox container (no USB in Docker Desktop on macOS): the user runs `esp_rfc2217_server -v /dev/cu.usbserial-XXXX` on the Mac; then use `PORT='rfc2217://host.docker.internal:2217?ign_set_control'` and `uv run --no-project --with mpremote python tools/mpr.py` in place of `mpremote` (plain mpremote can't reach the REPL: `main.py` deep-sleeps right after boot). Details: README "Working from the toolbox container".

## mbedTLS heap constraint (CRITICAL)

WiFi/mbedTLS use an ESP32 **system heap** invisible to Python. Changing what `main.py` allocates at import time shifts that heap and can make the HTTPS call fail with `MBEDTLS_ERR_MPI_ALLOC_FAILED`.

Keep `main.py`'s module level as it is: same imports, constants and function definitions. Put new logic inside existing functions, with lazy imports or `try: from config import X` there. Allocate `Pin()` / `machine.ADC()` and call `gc.collect()` only after `urequests.post()`. Confirmed to break TLS: a new module-level `Pin()` or function, `WDT(timeout=...)`, `wlan.config(pm=0)`.

**A `main.py` change is done only when it passes on hardware**: upload it, press the button with the serial log open, and see `HTTP status: 200` with `"statusCode":100` in the response. Passing tests prove nothing here — the stubs have no system heap.

## Testing

`tests/conftest.py` injects fake MicroPython modules (`machine`, `network`, `neopixel`, `urequests`, `ntptime`, `config`) into `sys.modules` before `import main`; a new hardware dependency needs a stub there first. The `_reset_rtc` fixture clears RTC memory between tests.
