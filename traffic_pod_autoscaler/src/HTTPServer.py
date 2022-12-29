import threading
from http.server import HTTPServer as _HTTPServer
from HTTPRequestHandler import HTTPRequestHandler
from libs.LoggerToolbox import _logger
from functools import partial
from Proxy import Proxy


class HTTPServer(object):
    _webServer = None

    def __init__(self, _args, _proxy: Proxy):
        _logger.debug("START")

        _http_server_port = _args.http_server_port

        self.run_server(_http_server_port, _proxy, _args)

    def run_server(self, _http_server_port,  _proxy, _args):

        _ping_url = _args.ping_url
        _metrics_url = _args.metrics_url
        _handler = partial(
            HTTPRequestHandler, _ping_url, _metrics_url, _proxy)

        self._webServer = threading.Thread(target=_HTTPServer(
            ("", _http_server_port), _handler).serve_forever)
        self._webServer.start()
        _logger.info(f"HTTP Server started on port {_http_server_port}")

    def stop(self):
        self._webServer.server_close()
        _logger.info("HTTP server stopped.")
