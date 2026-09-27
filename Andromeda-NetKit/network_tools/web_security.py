import re
import urllib.error
import urllib.request
from urllib.parse import urlsplit


def run(site):
    site = site.strip()
    scheme_match = re.match(r"^([A-Za-z][A-Za-z0-9+.-]*):", site)
    if scheme_match and scheme_match.group(1).lower() not in ("http", "https"):
        remainder = site[scheme_match.end():]
        if not re.match(r"^\d+(?:[/?#]|$)", remainder):
            raise ValueError("Only HTTP and HTTPS website addresses are supported.")

    url = (
        site
        if site.lower().startswith(("http://", "https://"))
        else f"http://{site}"
    )
    try:
        parsed_url = urlsplit(url)
        _ = parsed_url.port
    except ValueError as error:
        raise ValueError(f"Enter a valid website address: {error}") from error
    if (
        parsed_url.scheme not in ("http", "https")
        or not parsed_url.hostname
        or parsed_url.username is not None
        or parsed_url.password is not None
    ):
        raise ValueError("Enter a valid HTTP or HTTPS website address without credentials.")

    try:
        request = urllib.request.Request(
            url, headers={"User-Agent": "AndromedaNetKit/1.0"}
        )
        with urllib.request.urlopen(request, timeout=10) as response:
            final_url = response.geturl()
    except (urllib.error.URLError, ValueError) as error:
        raise RuntimeError(f"Unable to connect to {site}: {error}") from error

    if final_url.startswith("https://"):
        return f"HTTPS is enabled.\nFinal URL: {final_url}"
    return f"The site did not redirect to HTTPS.\nFinal URL: {final_url}"
