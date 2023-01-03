from threading import Timer
from libs.LoggerToolbox import _logger


class Watcher(object):

    def __init__(self, interval, *args, **kwargs):
        _logger.debug("START")
        self._timer = None
        self.interval = interval
        self.args = args
        self.kwargs = kwargs
        self.is_running = False
        self.start()

    def _run(self):
        _logger.debug("START")
        self.is_running = False
        self.start()
        self._watcher_function(*self.args, **self.kwargs)

    def start(self):
        _logger.debug("START")
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        _logger.info("Watcher stopped.")
        self._timer.cancel()
        self.is_running = False

    def _watcher_function(self, _args, _kwargs):
        _logger.debug("START")
        pass
