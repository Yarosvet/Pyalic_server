"""HTTP server for testing purposes"""
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler
import typing
import json


@dataclass
class HTTPRequest:
    """HTTP request model"""
    method: typing.Literal["GET", "POST", "PUT", "DELETE"]
    url: str
    request_data: dict

    def __hash__(self):
        return hash((self.method, self.url, json.dumps(self.request_data)))


@dataclass
class HTTPResponse:
    """HTTP response model"""
    response_data: dict
    response_code: int = 200

    def __hash__(self):
        return hash((self.response_data, self.response_code))


class PreconfiguredHTTPRequestHandler(BaseHTTPRequestHandler):
    """Handle HTTP requests with preconfigured responses"""
    _mapping = {}
    fail_first = False

    @classmethod
    def set_response(cls, request: HTTPRequest, response: HTTPResponse):
        """Set response for HTTP request"""
        cls._mapping[request] = response

    @classmethod
    def clear_mapping(cls):
        """Clear all responses mapping"""
        cls._mapping = {}

    def process_request(self, method: typing.Literal["GET", "POST", "PUT", "DELETE"]):
        """Process request of any method"""
        if self.fail_first:
            self.send_response(500)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.__class__.fail_first = False
            return
        content_length = int(self.headers.get('content-length', "0"))
        content = json.loads(self.rfile.read(content_length).decode('utf-8'))
        for req, resp in self._mapping.items():
            if req.method == method and \
                    req.url == self.path and \
                    json.loads(json.dumps(req.request_data)) == content:
                self.send_response(resp.response_code)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(json.dumps(resp.response_data).encode('utf-8'))
                return
        self.send_response(404)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        print(self._mapping)

    def do_GET(self):  # pylint: disable=invalid-name  # noqa
        """Handle GET request"""
        self.process_request("GET")

    def do_POST(self):  # pylint: disable=invalid-name  # noqa
        """Handle POST request"""
        self.process_request("POST")

    def do_PUT(self):  # pylint: disable=invalid-name  # noqa
        """Handle PUT request"""
        self.process_request("PUT")

    def do_DELETE(self):  # pylint: disable=invalid-name  # noqa
        """Handle DELETE request"""
        self.process_request("DELETE")


def preconfigured_handler_factory() -> type[PreconfiguredHTTPRequestHandler]:
    """Create new preconfigured HTTP request handler"""

    class _Handler(PreconfiguredHTTPRequestHandler):
        _mapping = {}
        fail_first = False

    return _Handler
