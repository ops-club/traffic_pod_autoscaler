from http.server import BaseHTTPRequestHandler
from libs.LoggerToolbox import _logger
import json


class HTTPRequestHandler(BaseHTTPRequestHandler):

    _ping_url = ""
    _metrics_url = ""
    _proxy = None

    def __init__(self, _ping_url, _metrics_url, _proxy, *args, **kwargs):

        self._ping_url = _ping_url
        self._metrics_url = _metrics_url
        self._proxy = _proxy

        super().__init__(*args, **kwargs)

    def do_GET(self):
        _logger.debug(f"Received request on {self.path}")
        match self.path:
            case self._ping_url:
                _resp_code = 200
                _resp_key = 'response'
                _resp = "pong"

            case self._metrics_url:
                _resp_code = 200
                _resp_key = 'metrics'
                _resp = self._proxy.get_stats_request()
            case _:
                _resp_code = 404
                _resp_key = 'message'
                _resp = "Path not handled by HTTP server"

        _resp_string = json.dumps({_resp_key: _resp}, default=str)
        response_body = _resp_string.encode(encoding='utf_8')

        self.send_response(_resp_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header("Content-Length", str(len(response_body)))
        self.end_headers()
        self.wfile.write(response_body)
