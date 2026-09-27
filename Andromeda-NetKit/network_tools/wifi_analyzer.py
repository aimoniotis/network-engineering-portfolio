import platform
import shutil
import subprocess


def _run_scan(command):
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=30,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        raise RuntimeError("Wi-Fi scan timed out.") from error
    except OSError as error:
        raise RuntimeError(f"Unable to run Wi-Fi scan: {error}") from error

    output = result.stdout.strip() or result.stderr.strip()
    if result.returncode != 0:
        raise RuntimeError(output or "The operating system could not scan for Wi-Fi networks.")
    if not output:
        return "No nearby Wi-Fi networks were reported."
    return output


def run(_request=""):
    system = platform.system()
    if system == "Windows":
        command = shutil.which("netsh")
        if not command:
            raise RuntimeError("The Windows netsh utility was not found.")
        return _run_scan([command, "wlan", "show", "networks", "mode=bssid"])

    if system == "Linux":
        command = shutil.which("nmcli")
        if command:
            return _run_scan(
                [
                    command,
                    "--colors",
                    "no",
                    "--terse",
                    "--fields",
                    "IN-USE,SSID,BSSID,CHAN,RATE,SIGNAL,SECURITY",
                    "device",
                    "wifi",
                    "list",
                    "--rescan",
                    "yes",
                ]
            )

        command = shutil.which("iwlist")
        if command:
            return _run_scan([command, "scanning"])
        raise RuntimeError(
            "Install NetworkManager's nmcli utility to scan nearby Wi-Fi networks."
        )

    if system == "Darwin":
        airport = (
            "/System/Library/PrivateFrameworks/Apple80211.framework/"
            "Versions/Current/Resources/airport"
        )
        if shutil.which(airport):
            return _run_scan([airport, "-s"])
        system_profiler = shutil.which("system_profiler")
        if system_profiler:
            return _run_scan([system_profiler, "-detailLevel", "basic", "SPAirPortDataType"])
        raise RuntimeError("No supported macOS Wi-Fi scan utility was found.")

    raise RuntimeError(f"Wi-Fi scanning is not supported on {system or 'this platform'}.")
