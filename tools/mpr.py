# mpremote over RFC2217 for a board whose main.py deep-sleeps right after boot.
# Each new RFC2217 connection resets the board; we release DTR/RTS (pyserial
# asserts both by default) and spam Ctrl-C until the REPL prompt shows, before
# mpremote takes over the same connection.
#
# Usage: uv run --no-project --with mpremote python tools/mpr.py connect "$P" fs ls
#   P='rfc2217://host.docker.internal:2217?ign_set_control'
#   (on the Mac: esp_rfc2217_server -v /dev/cu.usbserial-XXXX)
import sys, time, serial

_orig = serial.serial_for_url


def _patched(url, *a, **kw):
    s = _orig(url, *a, **kw)  # mpremote passes do_not_open=True
    s.dtr = False
    s.rts = False
    real_open = s.open

    def open_and_interrupt():
        real_open()
        # mpremote uses timeout=None: without this, read() blocks forever on a sleeping board
        timeout, s.timeout = s.timeout, 0.1
        buf, t = b"", time.time()
        while b">>> " not in buf:
            if time.time() - t > 8:
                raise SystemExit("REPL not reached: board in deep sleep? Press the button/reset and retry")
            s.write(b"\x03")
            time.sleep(0.05)
            buf = buf[-16:] + s.read(s.in_waiting or 1)
        s.reset_input_buffer()
        s.timeout = timeout

    s.open = open_and_interrupt
    return s


serial.serial_for_url = _patched
from mpremote.main import main

sys.exit(main())
