import threading
from http.server import HTTPServer as _HTTPServer
from HTTPRequestHandler import HTTPRequestHandler
from libs.LoggerToolbox import _logger
from functools import partial
from Proxy import Proxy


import threading


class HTTPServer(threading.Thread):

    _http_server_port = None
    _ping_url = None
    _metrics_url = None
    _proxy = None
    _webServer = None

    def __init__(self, _args, _proxy: Proxy):
        _logger.debug("START")

        self._proxy = _proxy
        self._http_server_port = _args.http_server_port
        self._ping_url = _args.ping_url
        self._metrics_url = _args.metrics_url

        super().__init__()
        self.stop_requested = False
        self.start()

    def run(self):
        _handler = partial(
            HTTPRequestHandler, self._ping_url, self._metrics_url, self._proxy)

        self._webServer = _HTTPServer(("", self._http_server_port), _handler)
        while not self.stop_requested:
            _logger.info(
                f"HTTP Server started on port {self._http_server_port}")
            self._webServer.serve_forever()

    def stop(self):
        _logger.info("HTTP server stopped.")
        try:
            self.stop_requested = True
            self._webServer.shutdown()
            return self.join()
            # self._webServer._stop()
        except Exception as e:
            _logger.exception(e)
