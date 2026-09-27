import socket


def run(hostname):
    try:
        return f"IPv4 address for {hostname}: {socket.gethostbyname(hostname)}"
    except socket.gaierror as error:
        raise RuntimeError(f"Unable to resolve hostname {hostname}: {error}") from error
