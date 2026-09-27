import platform
import shutil
import subprocess


def run(destination):
    system = platform.system()
    if system == "Windows":
        command = shutil.which("tracert")
    else:
        command = shutil.which("traceroute")
        if not command and system == "Linux":
            command = shutil.which("tracepath")

    if not command:
        raise RuntimeError("No traceroute utility was found on this system.")

    try:
        result = subprocess.run(
            [command, destination],
            capture_output=True,
            text=True,
            timeout=45,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise RuntimeError(f"Traceroute could not complete: {error}") from error

    output = result.stdout.strip() or result.stderr.strip()
    if result.returncode != 0:
        raise RuntimeError(output or "Traceroute did not complete successfully.")
    return output or "Traceroute completed with no output."
