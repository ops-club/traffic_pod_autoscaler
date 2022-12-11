from threading import Timer
from LoggerToolbox import _logger
from proxy import Proxy
from toolbox import _toolbox
from kubernetes_toolbox import KubernetesToolbox




class ProxyWatcher(object):
    _k8s: KubernetesToolbox


    def __init__(self, *args, **kwargs, ):
        _logger.debug("START")
        self._k8s = KubernetesToolbox()
        self._timer = None
        self.args = args
        self.kwargs = kwargs
        self.is_running = False
        self.start()

    def _run(self):
        _logger.debug("START")
        self.is_running = False
        self.start()

        self.update_configmap_if_needed(*self.args, **self.kwargs)

    def start(self):
        _logger.debug("START")
        if not self.is_running:
            self._timer = Timer(self.args.configmap_refresh_interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        _logger.debug("START")
        self._timer.cancel()
        self.is_running = False

    def update_configmap_if_needed(self, _args, _proxy: Proxy):
        _logger.debug("START")
        _last_proxy_call_timestamp = _proxy.get_last_call_timestamp()
        _last_call_annotation = self._k8s.get_last_call_annotation()
        _last_call_annotation_timestamp = _toolbox.get_date_utc_from_string(_last_call_annotation)
        if _last_proxy_call_timestamp > _last_call_annotation_timestamp:
            self._k8s.update_config_map_annotation( )
