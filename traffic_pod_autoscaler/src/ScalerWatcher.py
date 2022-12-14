from libs.Watcher import Watcher
from libs.LoggerToolbox import _logger
from Scaler import Scaler


class ScalerWatcher(Watcher):

    def _watcher_function(self, _args,  _scaler: Scaler):
        _logger.debug("START ScalerWatcher")
        is_expired = _scaler.is_expired()
        _logger.debug(f"is_expired: {is_expired}")
        if is_expired:
            _replica = _scaler.get_replica_number()
            if _replica > 0:
                _scaler.scale_down()
