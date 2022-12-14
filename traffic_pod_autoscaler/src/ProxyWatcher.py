from libs.Watcher import Watcher
from libs.LoggerToolbox import _logger
from Proxy import Proxy


class ProxyWatcher(Watcher):

    def _watcher_function(self, _args, _proxy: Proxy):
        _logger.debug("START ProxyWatcher")
        _proxy.update_annotation_last_call()
