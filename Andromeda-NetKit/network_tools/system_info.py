import json
import ipaddress
import os
import platform
import re
import shutil
import socket
import subprocess
import urllib.error
import urllib.request


def _command(args, timeout=10, required=False):
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        if required:
            raise RuntimeError(f"Could not run {args[0]}: {error}") from error
        return ""
    if result.returncode != 0:
        if required:
            raise RuntimeError(result.stderr.strip() or f"{args[0]} returned an error.")
        return ""
    return result.stdout.strip()


def _linux_info():
    report = []
    ip_command = shutil.which("ip")
    default_devices = set()
    if ip_command:
        addresses_text = _command([ip_command, "-j", "address", "show"])
        routes_text = _command([ip_command, "-j", "route", "show", "table", "all"])
        try:
            interfaces = json.loads(addresses_text) if addresses_text else []
            routes = json.loads(routes_text) if routes_text else []
        except json.JSONDecodeError:
            interfaces, routes = [], []

        route_by_device = {}
        for route in routes:
            if route.get("dst") in ("default", "0.0.0.0/0", "::/0"):
                if route.get("dev"):
                    default_devices.add(route["dev"])
                route_by_device.setdefault(route.get("dev", ""), []).append(
                    f"{route.get('gateway', 'gateway not reported')} "
                    f"({route.get('dst', 'default route')})"
                )

        report.append("Network interfaces and addresses:")
        for interface in interfaces:
            name = interface.get("ifname", "unknown")
            report.append(f"  {name} ({interface.get('operstate', 'unknown state')})")
            for address in interface.get("addr_info", []):
                if address.get("scope") != "host":
                    report.append(
                        f"    {address.get('family', 'IP')}: "
                        f"{address.get('local', 'unknown')}/{address.get('prefixlen', '?')}"
                    )
            for gateway in route_by_device.get(name, []):
                report.append(f"    Default gateway: {gateway}")
        if default_devices:
            wireless_devices = [
                device
                for device in default_devices
                if os.path.isdir(f"/sys/class/net/{device}/wireless")
            ]
            connection_type = "Wi-Fi" if wireless_devices else "Wired or virtual"
            report.insert(0, f"Connection type: {connection_type}")
    else:
        report.append("Network interfaces and addresses (hostname lookup):")
        try:
            addresses = sorted(
                {
                    result[4][0]
                    for result in socket.getaddrinfo(
                        socket.gethostname(), None, type=socket.SOCK_STREAM
                    )
                    if result[0] in (socket.AF_INET, socket.AF_INET6)
                }
            )
        except socket.gaierror:
            addresses = []
        report.extend(f"  {address}" for address in addresses)
        if not addresses:
            report.append("  Not reported; install the iproute2 'ip' utility for interface details.")

    resolv_conf = "/etc/resolv.conf"
    try:
        with open(resolv_conf, encoding="utf-8") as file:
            dns_servers = [
                line.split()[1]
                for line in file
                if line.strip().startswith("nameserver ") and len(line.split()) > 1
            ]
    except OSError:
        dns_servers = []
    report.append("DNS servers: " + (", ".join(dict.fromkeys(dns_servers)) or "Not reported"))

    active_connection = shutil.which("nmcli")
    if active_connection:
        connection = _command(
            [
                active_connection,
                "--terse",
                "--escape",
                "no",
                "--fields",
                "TYPE,DEVICE,NAME",
                "connection",
                "show",
                "--active",
            ]
        )
        report.append("Active connections:")
        report.extend(f"  {line}" for line in connection.splitlines() if line)
        if not default_devices and connection:
            active_types = [
                line.split(":", 1)[0].lower()
                for line in connection.splitlines()
                if line
            ]
            report.insert(
                0,
                "Connection type: "
                + (
                    "Wi-Fi"
                    if any("wireless" in item or "wifi" in item for item in active_types)
                    else "Ethernet/other"
                ),
            )
        wifi = _command(
            [
                active_connection,
                "--terse",
                "--escape",
                "no",
                "--fields",
                "IN-USE,SSID,BSSID,CHAN,RATE,SIGNAL,SECURITY",
                "device",
                "wifi",
                "list",
                "--rescan",
                "no",
            ]
        )
        active_wifi = [line for line in wifi.splitlines() if line.startswith("*:")]
        report.append("Connected Wi-Fi: " + (active_wifi[0] if active_wifi else "Not connected / unavailable"))
    else:
        iwgetid = shutil.which("iwgetid")
        ssid = _command([iwgetid, "--raw"]) if iwgetid else ""
        report.append("Wi-Fi SSID: " + (ssid or "Not reported"))

    return report


def _windows_info():
    powershell = shutil.which("powershell") or shutil.which("pwsh")
    if not powershell:
        raise RuntimeError("PowerShell was not found; cannot read Windows network settings.")

    script = (
        "$items = Get-NetIPConfiguration -All -ErrorAction SilentlyContinue | "
        "ForEach-Object { [PSCustomObject]@{ "
        "Interface=$_.InterfaceAlias; Description=$_.NetAdapter.InterfaceDescription; "
        "Status=$_.NetAdapter.Status; IPv4=@($_.IPv4Address | ForEach-Object "
        "{ \"$($_.IPAddress)/$($_.PrefixLength)\" }); "
        "IPv6=@($_.IPv6Address | ForEach-Object "
        "{ \"$($_.IPAddress)/$($_.PrefixLength)\" }); "
        "Gateways=@($_.IPv4DefaultGateway, $_.IPv6DefaultGateway | "
        "Where-Object { $_ } | ForEach-Object { $_.NextHop }); "
        "DNS=@($_.DNSServer.ServerAddresses) } }; "
        "$items | ConvertTo-Json -Depth 5 -Compress"
    )
    output = _command(
        [powershell, "-NoProfile", "-NonInteractive", "-Command", script],
        timeout=20,
        required=True,
    )
    try:
        interfaces = json.loads(output) if output else []
    except json.JSONDecodeError as error:
        raise RuntimeError("Windows returned invalid network configuration data.") from error
    if isinstance(interfaces, dict):
        interfaces = [interfaces]

    report = ["Network interfaces:"]
    dns_servers = []
    active_types = []
    for interface in interfaces:
        report.append(
            f"  {interface.get('Interface', 'Unknown')} "
            f"({interface.get('Status', 'unknown status')})"
        )
        if interface.get("Description"):
            report.append(f"    Adapter: {interface['Description']}")
        if interface.get("Status") == "Up":
            adapter_description = (
                f"{interface.get('Interface', '')} {interface.get('Description', '')}"
            ).lower()
            active_types.append(
                "Wi-Fi"
                if any(word in adapter_description for word in ("wi-fi", "wireless", "wlan"))
                else "Ethernet/other"
            )
        for family in ("IPv4", "IPv6"):
            addresses = interface.get(family) or []
            for address in addresses:
                report.append(f"    {family}: {address}")
        for gateway in interface.get("Gateways") or []:
            report.append(f"    Default gateway: {gateway}")
        dns_servers.extend(interface.get("DNS") or [])
    report.insert(
        0,
        "Connection type: "
        + (", ".join(dict.fromkeys(active_types)) if active_types else "Not connected / unknown"),
    )
    report.append("DNS servers: " + (", ".join(dict.fromkeys(dns_servers)) or "Not reported"))

    wifi = _command([shutil.which("netsh") or "netsh", "wlan", "show", "interfaces"])
    ssid_match = re.search(r"^\s*SSID\s*:\s*(.+)$", wifi, re.MULTILINE)
    bssid_match = re.search(r"^\s*BSSID\s*:\s*(.+)$", wifi, re.MULTILINE)
    signal_match = re.search(r"^\s*Signal\s*:\s*(.+)$", wifi, re.MULTILINE)
    wifi_parts = [
        f"{label}: {match.group(1).strip()}"
        for label, match in (
            ("SSID", ssid_match),
            ("BSSID", bssid_match),
            ("Signal", signal_match),
        )
        if match
    ]
    report.append("Wi-Fi: " + ("; ".join(wifi_parts) if wifi_parts else "Not connected / unavailable"))

    proxy = _command(
        [
            powershell,
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            "$p=Get-ItemProperty 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings' "
            "-ErrorAction SilentlyContinue; "
            "if ($p.ProxyEnable) { $p.ProxyServer } else { 'System proxy disabled' }",
        ]
    )
    report.append("System proxy: " + (proxy or "Not reported"))
    profile = _command(
        [
            powershell,
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            "Get-NetConnectionProfile -ErrorAction SilentlyContinue | "
            "Select-Object InterfaceAlias,Name,NetworkCategory,IPv4Connectivity,"
            "IPv6Connectivity | ConvertTo-Json -Compress",
        ]
    )
    if profile:
        report.append("Network profiles:")
        report.extend(f"  {line}" for line in profile.splitlines())
    return report


def _macos_info():
    report = []
    route = shutil.which("route")
    if route:
        for family, args in (("IPv4", ["-n", "get", "default"]), ("IPv6", ["-n", "get", "-inet6", "default"])):
            output = _command([route, *args])
            gateway = re.search(r"^\s*gateway:\s*(\S+)", output, re.MULTILINE)
            interface = re.search(r"^\s*interface:\s*(\S+)", output, re.MULTILINE)
            if gateway:
                report.append(f"{family} default gateway: {gateway.group(1)}")
            if interface:
                report.append(f"{family} route interface: {interface.group(1)}")
    networksetup = shutil.which("networksetup")
    if networksetup:
        services = _command([networksetup, "-listallnetworkservices"])
        report.append("Network services:")
        report.extend(f"  {line}" for line in services.splitlines()[1:] if line and not line.startswith("*"))
        report.append("Wi-Fi details:")
        report.append(_command([networksetup, "-getairportnetwork", "en0"]) or "Not connected / unavailable")
    return report


def _public_ip(version):
    url = f"https://api{version}.ipify.org"
    request = urllib.request.Request(url, headers={"User-Agent": "AndromedaNetKit/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            result = response.read(128).decode("ascii", errors="replace").strip()
        address = ipaddress.ip_address(result)
        if address.version != version:
            return f"Unavailable (lookup did not return IPv{version})"
        return str(address)
    except (urllib.error.URLError, TimeoutError, OSError):
        return "Unavailable (no public route, IPv6, or lookup service response)"
    except ValueError:
        return "Unavailable (lookup service returned an invalid IP address)"


def _proxy_settings():
    configured = {
        name: value
        for name, value in os.environ.items()
        if name.lower() in {"http_proxy", "https_proxy", "all_proxy", "no_proxy"}
    }
    safe_values = []
    for name, value in sorted(configured.items()):
        value = re.sub(r"(://[^:/@\s]+):[^@\s]+@", r"\1:***@", value)
        safe_values.append(f"{name}={value}")
    return "; ".join(safe_values) or "No proxy environment variables set"


def run(_request=""):
    system = platform.system()
    if system == "Windows":
        details = _windows_info()
    elif system == "Linux":
        details = _linux_info()
    elif system == "Darwin":
        details = _macos_info()
    else:
        raise RuntimeError(f"Connection details are not supported on {system}.")

    report = [
        "PC AND CONNECTION INFORMATION",
        "=" * 34,
        f"Operating system: {platform.platform()}",
        f"Computer name: {platform.node() or 'Not reported'}",
        "",
        *details,
        "",
        f"Proxy environment: {_proxy_settings()}",
        "",
        "Public IP addresses (looked up online):",
        f"  IPv4: {_public_ip(4)}",
        f"  IPv6: {_public_ip(6)}",
        "",
        "Public IP lookups send a request to api.ipify.org. "
        "This report is shown locally and is not uploaded by this app.",
    ]
    return "\n".join(report)
