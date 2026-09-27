import errno
import socket
from concurrent.futures import ThreadPoolExecutor


PORTS = range(1, 65536)
WORKERS = 256
TCP_TIMEOUT = 0.5
UDP_TIMEOUT = 0.2
PORT_SERVICES = {
    20: "FTP-data",
    21: "FTP",
    22: "SSH",
    23: "Telnet",
    25: "SMTP",
    53: "DNS",
    67: "DHCP",
    68: "DHCP",
    69: "TFTP",
    80: "HTTP",
    110: "POP3",
    123: "NTP",
    143: "IMAP",
    161: "SNMP",
    389: "LDAP",
    443: "HTTPS",
    445: "SMB",
    514: "Syslog",
    587: "SMTP submission",
    636: "LDAPS",
    993: "IMAPS",
    1433: "Microsoft SQL Server",
    3306: "MySQL",
    3389: "RDP",
    5432: "PostgreSQL",
    5900: "VNC",
    8080: "HTTP proxy",
    8443: "HTTPS alternate",
}
CHUNK_SIZE = 512


def _scan_tcp_port(target_ip, port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as connection:
            connection.settimeout(TCP_TIMEOUT)
            if connection.connect_ex((target_ip, port)) == 0:
                return port
    except OSError:
        return None
    return None


def _scan_udp_port(target_ip, port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as connection:
            connection.settimeout(UDP_TIMEOUT)
            connection.sendto(b"", (target_ip, port))
            try:
                connection.recvfrom(1024)
                return port, "open"
            except socket.timeout:
                return port, "open|filtered"
    except OSError as error:
        if error.errno == errno.ECONNREFUSED or getattr(error, "winerror", None) in (
            10054,
            10061,
        ):
            return port, "closed"
        return port, "open|filtered"


def _scan_all_ports(target_ip, protocol):
    scanner = _scan_tcp_port if protocol == "TCP" else _scan_udp_port
    results = []
    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        for start in range(PORTS.start, PORTS.stop, CHUNK_SIZE):
            port_batch = range(start, min(start + CHUNK_SIZE, PORTS.stop))
            results.extend(executor.map(scanner, [target_ip] * len(port_batch), port_batch))
    return results


def _format_port(port, protocol, state="open"):
    service = PORT_SERVICES.get(port)
    description = f" ({service})" if service else ""
    return f"{protocol}/{port}  {state}{description}"


def run(target):
    try:
        target_ip = socket.gethostbyname(target)
    except socket.gaierror as error:
        raise RuntimeError(f"Could not resolve target {target}: {error}") from error

    tcp_results = _scan_all_ports(target_ip, "TCP")
    udp_results = _scan_all_ports(target_ip, "UDP")
    tcp_open = [port for port in tcp_results if port is not None]
    udp_open = []
    udp_state_counts = {"open": 0, "closed": 0, "open|filtered": 0}
    for result in udp_results:
        port, state = result
        udp_state_counts[state] += 1
        if state == "open":
            udp_open.append(port)

    lines = [
        f"Full port scan for {target} ({target_ip})",
        "Scanned TCP ports 1-65535 and UDP ports 1-65535.",
        "",
        f"TCP: {len(tcp_open)} open",
    ]
    lines.extend(_format_port(port, "TCP") for port in tcp_open)
    lines.extend(
        [
            "",
            f"UDP: {udp_state_counts['open']} open, "
            f"{udp_state_counts['closed']} closed, "
            f"{udp_state_counts['open|filtered']} open|filtered",
        ]
    )
    lines.extend(_format_port(port, "UDP") for port in udp_open)
    lines.append(
        "UDP open|filtered means no response was received; the port may be open "
        "or blocked by a firewall."
    )
    lines.append(
        "Only scan systems and networks you own or have explicit permission to test."
    )
    return "\n".join(lines)
