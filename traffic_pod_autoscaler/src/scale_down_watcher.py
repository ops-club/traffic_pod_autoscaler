from threading import Timer
from LoggerToolbox import _logger
from scaler import Scaler



class ScaleDownWatcher(object):

    def __init__(self, *args, **kwargs):
        _logger.debug("START")
        self._timer = None
        self.args = args
        self.kwargs = kwargs
        self.is_running = False
        self.start()

    def _run(self):
        _logger.debug("START")
        self.is_running = False
        self.start()

        self.check_scale_down(*self.args, **self.kwargs)

    def start(self):
        _logger.debug("START")
        if not self.is_running:
            self._timer = Timer(self.args.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        _logger.debug("START")
        self._timer.cancel()
        self.is_running = False

    def check_scale_down(_args, _scaler: Scaler):
        _logger.debug("START")
        is_expired = _scaler.is_expired()
        _logger.debug(f"is_expired: {is_expired}")
        if is_expired:
            _replica = _scaler.get_replica_number()
            if _replica > 0:
                _scaler.scale_down()
