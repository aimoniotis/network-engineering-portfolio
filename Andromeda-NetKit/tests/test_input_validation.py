import unittest
from unittest.mock import patch

from network_tools import web_security, whois_lookup


class WebSecurityInputTests(unittest.TestCase):
    def test_accepts_host_and_port_without_url_scheme(self):
        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def geturl(self):
                return "https://example.com:8443"

        with patch.object(
            web_security.urllib.request, "urlopen", return_value=FakeResponse()
        ) as open_url:
            web_security.run("example.com:8443")
        self.assertEqual(open_url.call_args.args[0].full_url, "http://example.com:8443")

    def test_rejects_non_http_schemes(self):
        for address in ("file:///etc/passwd", "ftp://example.com"):
            with self.subTest(address=address), patch.object(
                web_security.urllib.request, "urlopen"
            ) as open_url:
                with self.assertRaises(ValueError):
                    web_security.run(address)
                open_url.assert_not_called()

    def test_rejects_missing_host_and_embedded_credentials(self):
        for address in ("http://", "https://user:password@example.com"):
            with self.subTest(address=address), patch.object(
                web_security.urllib.request, "urlopen"
            ) as open_url:
                with self.assertRaises(ValueError):
                    web_security.run(address)
                open_url.assert_not_called()

    def test_rejects_invalid_port(self):
        with patch.object(web_security.urllib.request, "urlopen") as open_url:
            with self.assertRaises(ValueError):
                web_security.run("https://example.com:99999")
            open_url.assert_not_called()


class WhoisInputTests(unittest.TestCase):
    def test_rejects_line_breaks_before_opening_connection(self):
        with patch.object(whois_lookup.socket, "create_connection") as connect:
            with self.assertRaises(ValueError):
                whois_lookup.run("example.com\r\nquit")
            connect.assert_not_called()

    def test_limits_response_size(self):
        class FakeConnection:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def sendall(self, _data):
                pass

            def recv(self, _size):
                return b"x" * (whois_lookup.MAX_RESPONSE_BYTES + 1)

        with patch.object(
            whois_lookup.socket, "create_connection", return_value=FakeConnection()
        ):
            with self.assertRaisesRegex(RuntimeError, "1 MiB size limit"):
                whois_lookup.run("example.com")


if __name__ == "__main__":
    unittest.main()
