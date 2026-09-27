try:
    import dns.resolver
except ImportError:
    dns = None


RECORD_TYPES = ("A", "AAAA", "CAA", "CNAME", "MX", "NAPTR", "NS", "PTR", "SOA", "SRV", "TXT")


def run(domain):
    if dns is None:
        raise RuntimeError(
            "Advanced DNS records require dnspython. Install it with: "
            "python3 -m pip install dnspython"
        )

    results = []
    for record_type in RECORD_TYPES:
        try:
            answers = dns.resolver.resolve(domain, record_type)
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers):
            continue
        except dns.exception.DNSException as error:
            results.append(f"{record_type}: Query failed ({error})")
            continue
        results.append(f"{record_type}:\n" + "\n".join(f"  {answer}" for answer in answers))

    return "\n\n".join(results) if results else f"No supported DNS records found for {domain}."
