import platform
import subprocess


def run(host):
    parameter = "-n" if platform.system() == "Windows" else "-c"
    try:
        result = subprocess.run(
            ["ping", parameter, "4", host],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise RuntimeError(f"Ping could not complete: {error}") from error

    output = result.stdout.strip() or result.stderr.strip()
    status = "Ping completed successfully." if result.returncode == 0 else "Ping failed."
    return f"{status}\n\n{output}"
