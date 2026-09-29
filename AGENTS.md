# Repository guidance

## Read the implementation

DS5Dongle is RP2040/RP2350 firmware for a USB to Bluetooth DualSense bridge. It
does not contain the DS5 Bridge Windows companion, WinUSB transport, or installer.
Start with `README.md` and `.github/workflows/build-firmware.yml`; use source
code as the authority when older documentation differs.

`src/main.cpp` owns startup and the Core 0 poll loop. `src/bt.cpp` handles the
controller connection, `src/usb_descriptors.cpp` and `src/usb.cpp` define the
host facing USB device, and `src/audio.cpp` runs audio work on Core 1. HID
configuration is implemented in `src/cmd.cpp`, `src/config.h`, and
`src/config.cpp`; `tools/config_tool.py` is the corresponding host tool.

## Build and verify

For reproducible firmware builds, follow `.github/workflows/build-firmware.yml`:
Pico SDK `2.3.0`, its TinyUSB checkout at
`2d56dc533e45e4e91b15e93fdab5e22e964f328d`, Arm GNU Toolchain
`15.2.Rel1`, CMake, and Ninja. Initialize this repository's `lib/WDL` and
`lib/opus` submodules with `git submodule update --init --recursive`. Verify
the SDK and TinyUSB Git revisions and compiler version rather than assuming a
local SDK installation matches CI. The convenience scripts may use different
dependency revisions; use the workflow pins for release evidence.

Configure each Release variant in its own build directory, with
`-DPICO_SDK_PATH=<sdk-path>` and the intended `-DVERSION=<version>`. The
default board is Pico 2 W. Use `-DPICO_W_BUILD=ON` for Pico W (speaker
processing disabled), or `-DWAVESHARE_RP2350B_PLUS_W_BUILD=ON` for Waveshare
RP2350B-Plus-W. These board options are mutually exclusive. CI's debug
variant uses `-DENABLE_SERIAL=ON -DENABLE_VERBOSE=ON -DWAKE_DEBUG=ON`; it is
built with `CMAKE_BUILD_TYPE=Release` and is a separate UF2. Build with
`cmake --build <build-dir> --target ds5-bridge` and inspect that directory's
`ds5-bridge.uf2`. Do not substitute a UF2 from another board or configuration.

The opt-in `DS5_PICO2W_EXPERIMENTAL_225MHZ` and
`DS5_PICO2W_EXPERIMENTAL_300MHZ` options are Pico 2 W only, default off, and
mutually exclusive. They select VREG 1.15 V with CYW43 PIO /3 or /4, boot2
XIP /3 or /4, and RXDELAY 3 or 4, respectively. Leave both off for the standard
150 MHz firmware. Keep these clock settings coupled. Check actual compile
commands for `main.cpp`, the CYW43 driver, and `bs2_default` when changing
them, and compare the standard UF2 against a same-toolchain baseline.

Run the native HID policy CTest in `tests/` and the Python configuration tool
unittests in `tests/test_config_tool.py` when changing these paths. A successful
test run, build, ELF or UF2 inspection, and a `picotool` report are bounded
host/static/build evidence only. Record
the source revision, dependency revisions, build options, artifact SHA-256,
board, and complete check results. Device boot, pairing, audio behavior,
stability, and game compatibility require explicit hardware tests. The
225/300 MHz experimental overclocks are outside the RP2350 frequency
specification. Evidence for both is limited to build/static checks; neither is
hardware qualified. RP2350 datasheet sections 14.9.1, 14.9.5, and 14.9.6 give
a 1.21 V DVDD absolute maximum, 1.16 V operating maximum, and +3% regulator
deviation. At +3%, their nominal 1.15 V can reach 1.1845 V, above the
operating maximum. Nominally preserved peripheral divisors do not establish
hardware safety or reliable operation.

The former 375 MHz / 1.20 V profile was retired after a user-reported no-boot
test. The tested board and cause have not been established; preserve its
[failure record](artifacts/oc375-failed-boot.json).
Its nominal 1.20 V exceeds the operating limit, and +3% deviation can reach
1.236 V, above the absolute maximum.

## Preserve firmware contracts

The configuration protocol uses DualSense gamepad HID feature reports:
`0xF6` writes settings or commands, `0xF7` reads the packed `Config_body`,
`0xF8` reads the firmware version, and `0xF9` reads RSSI and audio state.
Keep `src/cmd.cpp`, `src/config.h`, `src/config.cpp`, the report descriptors,
and `tools/config_tool.py` aligned whenever report IDs, lengths, field order,
validation, or schema version change. Flash-backed settings and BTstack's
pairing storage are separate. Wake and keyboard behavior is compiled into the
base firmware but enabled through runtime configuration; descriptor or USB
re-enumeration changes need device checks.

Runtime `polling_rate_mode` values 0 (250 Hz), 1 (500 Hz), and 2 (dirty
Real-time) retain their existing behavior. Mode 3 uses a fixed 1 ms USB HID
cadence (endpoint interval) and queues the latest complete 63-byte
Bluetooth-derived input state whenever the endpoint is ready. If no new
Bluetooth report arrives, it repeats the same state, including sensor values
and controller timestamp; do not fabricate fresh sensor samples or timestamps.
Keep `Config_body` layout and configuration version 5 unchanged. Keep firmware
validation, `tools/config_tool.py`, and the external web configurator aligned
on mode 3. When Web/CLI changes the mode, use the Web reconnect action or
`python tools/config_tool.py reconnect` (both send `0xF6` function `0x03`),
or instruct a physical replug so the host reads the new HID
endpoint interval. Builds and static checks do not establish 1,000 actual host
receives per second or improved gyro jitter; verify both on hardware.

Core 0 services CYW43, TinyUSB, and the audio queues; it services the watchdog
when enabled (the serial debug build disables it). Core 1
processes audio. Preserve `flash_safe_execute_core_init()` on Core 1 and
`PICO_FLASH_ASSUME_CORE1_SAFE=0`: `config_save()` and BOOTSEL polling must park
Core 1 before QSPI flash access. Audio timing also depends on the RAM
relocations in `CMakeLists.txt` and `cmake/relocate_to_ram.cmake` for Opus, WDL,
and selected Bluetooth/USB hot paths. Review linked SRAM use, stack bounds,
queue behavior, and actual audio output when changing those paths.

## Package releases

The release workflow uploads three assets: the versioned standard UF2,
`config_tool.py`, and `other board.zip` containing the Pico W and Waveshare
UF2s. It excludes the debug UF2. For a local three-asset package, use the
standard UF2, `config_tool.py`, and `other.board.zip` containing exactly those
two other-board UF2s. Keep only 225/300 MHz UF2s in the active experimental
output, outside the release directory, with their build provenance and an
unverified-on-hardware label. Do not treat an artifact upload as a successful
device qualification.
