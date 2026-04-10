import ipaddress
import socket
import sys

from django.conf import settings
from urllib3.connection import HTTPConnection, HTTPSConnection
from urllib3.connectionpool import HTTPConnectionPool, HTTPSConnectionPool
from urllib3.exceptions import (
    ConnectTimeoutError,
    HTTPError,
    LocationParseError,
    NameResolutionError,
    NewConnectionError,
)
from urllib3.util.connection import (
    _TYPE_SOCKET_OPTIONS,
    _set_socket_options,
    allowed_gai_family,
)
from urllib3.util.timeout import _DEFAULT_TIMEOUT


def monkeypatch_urllib3_ssrf_protection():
    """
    Venueless allows HTTP requests to untrusted URLs through link previous in chat. This is dangerous since
    it can allow access to private networks that should not be reachable by users ("server-side request forgery", SSRF).
    Validating URLs at submission is not sufficient, since with DNS rebinding an attacker can make a domain name pass
    validation and then resolve to a private IP address on actual execution. Unfortunately, there seems no clean solution
    to this in Python land, so we monkeypatch urllib3's connection management to check the IP address to be external
    *after* the DNS resolution.

    This does not work when a global http(s) proxy is used, but in that scenario the proxy can perform the validation.

    This does NOT affect aiohttp which is used for BBB/DigitalSamba integration.
    """
    if getattr(settings, "ALLOW_HTTP_TO_PRIVATE_NETWORKS", False):
        # Settings are not supposed to change during runtime, so we can optimize performance and complexity by skipping
        # this if not needed.
        return

    def create_connection(
        address: tuple[str, int],
        timeout=_DEFAULT_TIMEOUT,
        source_address: tuple[str, int] | None = None,
        socket_options: _TYPE_SOCKET_OPTIONS | None = None,
    ) -> socket.socket:
        # This is copied from urllib3.util.connection v2.3.0
        host, port = address
        if host.startswith("["):
            host = host.strip("[]")
        err = None

        # Using the value from allowed_gai_family() in the context of getaddrinfo lets
        # us select whether to work with IPv4 DNS records, IPv6 records, or both.
        # The original create_connection function always returns all records.
        family = allowed_gai_family()

        try:
            host.encode("idna")
        except UnicodeError:
            raise LocationParseError(f"'{host}', label empty or too long") from None

        for res in socket.getaddrinfo(host, port, family, socket.SOCK_STREAM):
            af, socktype, proto, canonname, sa = res

            if not getattr(settings, "ALLOW_HTTP_TO_PRIVATE_NETWORKS", False):
                ip_addr = ipaddress.ip_address(sa[0])
                if ip_addr.is_multicast:
                    raise HTTPError(f"Request to multicast address {sa[0]} blocked")
                if ip_addr.is_loopback or ip_addr.is_link_local:
                    raise HTTPError(f"Request to local address {sa[0]} blocked")
                if ip_addr.is_private:
                    raise HTTPError(f"Request to private address {sa[0]} blocked")

            sock = None
            try:
                sock = socket.socket(af, socktype, proto)

                # If provided, set socket level options before connecting.
                _set_socket_options(sock, socket_options)

                if timeout is not _DEFAULT_TIMEOUT:
                    sock.settimeout(timeout)
                if source_address:
                    sock.bind(source_address)
                sock.connect(sa)
                # Break explicitly a reference cycle
                err = None
                return sock

            except OSError as _:
                err = _
                if sock is not None:
                    sock.close()

        if err is not None:
            try:
                raise err
            finally:
                # Break explicitly a reference cycle
                err = None
        else:
            raise OSError("getaddrinfo returns an empty list")

    class ProtectionMixin:
        def _new_conn(self) -> socket.socket:
            # This is 1:1 the version from urllib3.connection.HTTPConnection._new_conn v2.3.0
            # just with a call to our own create_connection
            try:
                sock = create_connection(
                    (self._dns_host, self.port),
                    self.timeout,
                    source_address=self.source_address,
                    socket_options=self.socket_options,
                )
            except socket.gaierror as e:
                raise NameResolutionError(self.host, self, e) from e
            except socket.timeout as e:
                raise ConnectTimeoutError(
                    self,
                    f"Connection to {self.host} timed out. (connect timeout={self.timeout})",
                ) from e

            except OSError as e:
                raise NewConnectionError(
                    self, f"Failed to establish a new connection: {e}"
                ) from e

            sys.audit("http.client.connect", self, self.host, self.port)
            return sock

    class ProtectedHTTPConnection(ProtectionMixin, HTTPConnection):
        pass

    class ProtectedHTTPSConnection(ProtectionMixin, HTTPSConnection):
        pass

    HTTPConnectionPool.ConnectionCls = ProtectedHTTPConnection
    HTTPSConnectionPool.ConnectionCls = ProtectedHTTPSConnection


def monkeypatch_all_at_ready():
    monkeypatch_urllib3_ssrf_protection()
