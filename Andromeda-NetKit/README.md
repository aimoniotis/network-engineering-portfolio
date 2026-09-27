# ⚡ Andromeda NetKit

## Run from source

```bash
python3 main.py
```

Install the Python runtime dependencies with:

```bash
python3 -m pip install -r requirements.txt
```

`requirements.txt` includes all external Python libraries used by the app,
including Pillow for the background image.
Tkinter is part of Python's standard library distribution but may need to be
installed separately by your operating system (for example, `python3-tk` on
Debian/Ubuntu). The installers verify Tkinter before building.

The GUI opens maximized with the supplied cosmic wallpaper and planet icon.
Choose Light or Dark mode from the diagnostics panel. PC & Connection
Information does not open automatically; select **My Host Information** when
you want to view local
interfaces and subnet addresses, gateways, DNS, proxy settings, Wi-Fi details,
and public IPv4/IPv6 lookups. Public IP lookups contact api.ipify.org; the
internet provider indicator shares your public IP with ipwho.is to identify
the ISP. The report is shown locally and is not uploaded by the app. The
interface and About dialog credit Konstantinos Aimoniotis and show software
version 1.0. Tool choices include emoji labels.
The Donate button is centered at the bottom of the diagnostics list with a
black background and white text; About and Privacy are grouped on the right
side of the header.

The homepage links to the in-app privacy statement, FAQ/support, the complete
feature list, and the
[GitHub repository](https://github.com/aimoniotis/network-engineering-portfolio).
Support issues open the repository's GitHub Issues page. The footer shows
`© 2026 Konstantinos Aimoniotis`.
The Wi-Fi analyzer uses your operating system's wireless tools. Linux requires
`nmcli` or `iwlist`, Windows uses `netsh`, and macOS uses its built-in AirPort
utilities. Results depend on the adapter, permissions, and OS support.

Internet speed and quality tests require `speedtest-cli` and an internet
connection. The test transfers data to and from a third-party speed-test
server, and uses ping to measure latency, jitter, and packet loss.

The full-port scanner probes TCP and UDP ports 1-65535. A UDP port that does
not respond is reported as `open|filtered`, since a silent response cannot
distinguish an open UDP service from packet filtering. Only scan systems and
networks you own or have explicit permission to test.

## Run the test suite

```bash
python3 -m unittest discover -s tests -v
```

## Build and install on Linux

From this directory, build and install the standalone app and application-menu
shortcut with:

```bash
bash install_linux.sh
```

The build creates an isolated `.venv`, quietly installs the requirements from
`requirements-build.txt` (runtime packages plus PyInstaller), and bundles the
Python libraries into `dist/AndromedaNetKit`. Users launching the packaged
app do not need Python or pip installed. Tkinter and system tools such as
`nmcli`/`iwlist` and `ping` are OS-provided, not Python packages.

## Build a Windows executable

On Windows, install Python 3 with Tcl/Tk support. Run `install_windows.bat` to
quietly install build dependencies, create the standalone executable, copy it
to your user Programs folder, and add a Start-menu shortcut. Alternatively,
run `build_windows.bat` to only create `dist\AndromedaNetKit.exe`. The
generated `.ico` file is embedded in the executable.

PyInstaller builds for the operating system on which it runs. Build the Windows
`.exe` on Windows and the Linux executable on Linux; the Linux executable is
not a Windows `.exe`.
