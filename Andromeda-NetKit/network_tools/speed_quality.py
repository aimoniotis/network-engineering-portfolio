import platform
import re
import statistics
import subprocess

try:
    import speedtest
except ImportError:
    speedtest = None


PING_COUNT = 10
PING_TIME_PATTERN = re.compile(r"time[=<]\s*([\d.]+)\s*ms", re.IGNORECASE)


def _measure_connection_quality(host):
    parameter = "-n" if platform.system() == "Windows" else "-c"
    command = ["ping", parameter, str(PING_COUNT)]
    if platform.system() == "Windows":
        command.extend(["-w", "2000"])
    else:
        command.extend(["-W", "2"])
    command.append(host)

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise RuntimeError(f"Unable to measure connection quality with ping: {error}") from error

    output = f"{result.stdout}\n{result.stderr}"
    latencies = [float(value) for value in PING_TIME_PATTERN.findall(output)]
    if not latencies:
        raise RuntimeError(
            f"No ping responses were received from {host}. Check connectivity and ping availability."
        )

    jitter = (
        statistics.mean(
            abs(current - previous)
            for previous, current in zip(latencies, latencies[1:])
        )
        if len(latencies) > 1
        else 0.0
    )
    packet_loss = (PING_COUNT - len(latencies)) / PING_COUNT * 100
    return latencies, jitter, packet_loss


def run(_request=""):
    if speedtest is None:
        raise RuntimeError(
            "Internet speed testing requires speedtest-cli. Install it with: "
            "python3 -m pip install speedtest-cli"
        )

    try:
        tester = speedtest.Speedtest(secure=True)
        server = tester.get_best_server()
        download_mbps = tester.download() / 1_000_000
        upload_mbps = tester.upload() / 1_000_000
        server_ping_ms = float(tester.results.ping)
        server_host = server.get("host", "").split(":", 1)[0]
    except Exception as error:
        raise RuntimeError(f"Internet speed test failed: {error}") from error

    if not server_host:
        raise RuntimeError("The speed test did not return a test-server hostname.")

    latencies, jitter, packet_loss = _measure_connection_quality(server_host)
    average_latency = statistics.mean(latencies)

    return (
        "Internet Speed & Quality Results\n"
        f"Test server: {server.get('name', 'Unknown')} ({server_host})\n"
        f"Download: {download_mbps:.2f} Mbps\n"
        f"Upload: {upload_mbps:.2f} Mbps\n"
        f"Speed-test latency: {server_ping_ms:.2f} ms\n"
        f"Ping latency to test server: {average_latency:.2f} ms "
        f"(min {min(latencies):.2f}, max {max(latencies):.2f})\n"
        f"Jitter: {jitter:.2f} ms\n"
        f"Packet loss: {packet_loss:.0f}% ({len(latencies)}/{PING_COUNT} replies)\n\n"
        "The speed test transfers test data to and from a third-party server."
    )
