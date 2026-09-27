import ipaddress
import platform
import subprocess
from concurrent.futures import ThreadPoolExecutor


def _check_host(ip_address):
    if platform.system() == "Windows":
        command = ["ping", "-n", "1", "-w", "800", str(ip_address)]
    else:
        command = ["ping", "-c", "1", "-W", "1", str(ip_address)]
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=3,
            check=False,
        )
        return str(ip_address) if result.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def run(subnet_prefix):
    try:
        network = ipaddress.ip_network(f"{subnet_prefix}.0/24", strict=False)
    except ValueError as error:
        raise ValueError("Enter a valid /24 subnet prefix, such as 192.168.1.") from error

    hosts = list(network.hosts())
    with ThreadPoolExecutor(max_workers=64) as executor:
        active_hosts = [host for host in executor.map(_check_host, hosts) if host]

    if not active_hosts:
        return f"Scan complete for {network}; no active hosts responded."
    return f"Active hosts on {network} ({len(active_hosts)}):\n" + "\n".join(active_hosts)
