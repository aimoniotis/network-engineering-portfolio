import socket


MAX_RESPONSE_BYTES = 1_048_576


def run(domain, server="whois.iana.org"):
    domain = domain.strip()
    if (
        not domain
        or len(domain) > 253
        or any(not character.isprintable() or character.isspace() for character in domain)
    ):
        raise ValueError("Enter a valid domain name without spaces or control characters.")

    try:
        with socket.create_connection((server, 43), timeout=10) as connection:
            connection.sendall(f"{domain}\r\n".encode("utf-8"))
            response = bytearray()
            while True:
                data = connection.recv(4096)
                if not data:
                    break
                if len(response) + len(data) > MAX_RESPONSE_BYTES:
                    raise RuntimeError("WHOIS response exceeded the 1 MiB size limit.")
                response.extend(data)
    except OSError as error:
        raise RuntimeError(f"WHOIS lookup failed: {error}") from error

    whois_data = response.decode("utf-8", errors="replace").strip()
    if not whois_data:
        return f"No WHOIS information was returned for {domain}."

    relevant_lines = [
        line
        for line in whois_data.splitlines()
        if line.lower().startswith(
            ("domain", "organisation", "created", "changed", "status", "whois", "nserver")
        )
    ]
    return "\n".join(relevant_lines) if relevant_lines else whois_data[:4000]
