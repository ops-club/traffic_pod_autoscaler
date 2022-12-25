from http.server import BaseHTTPRequestHandler, HTTPServer
from libs.LoggerToolbox import _logger
from Proxy import Proxy
import json

class MonitoringServer():
    _webServer = None
    _proxy = None

    def __init__(self, _args, _proxy: Proxy):
        _logger.debug("START")
        self._proxy = _proxy
        self.run_server(self._proxy, _args)

    def run_server(self, _proxy, _args):
        class ServerHandler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                return
            def do_GET(self):
                _logger.debug(f"Received request on {self.path}")
                match self.path:
                    case _args.local_ping_url:
                        _resp_code = 200
                        _resp = "pong"
                    case _args.local_monitoring_url:
                        _resp_code = 200
                        _resp = _proxy.get_stats_request()
                    case _:
                        _resp_code = 404
                        _resp = "Path not handled by monitoring"

                self.send_response(_resp_code)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                _resp = json.dumps({'response': _resp})
                _logger.debug(f"Response sent to the client: {_resp} ({_resp_code})")
                _resp = bytes(_resp, 'utf-8')
                self.wfile.write(_resp)

        self._webServer = HTTPServer(("", _args.local_monitoring_port), ServerHandler)
        _logger.info(f"Monitoring Server started on port {_args.local_monitoring_port}")
        self._webServer.serve_forever()

    def stop(self):
        self._webServer.server_close()
        _logger.info("Monitoring server stopped.")
