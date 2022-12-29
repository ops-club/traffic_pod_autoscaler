from libs.Watcher import Watcher
from libs.LoggerToolbox import _logger
from libs.KubernetesToolbox import KubernetesToolbox
from Scaler import Scaler


class PodsWatcher(Watcher):

    def _watcher_function(self, _args,  _scaler: Scaler):
        _logger.debug("START ScalerWatcher")
        _k8s = KubernetesToolbox()
        _pods = _k8s.list_namespaced_pod(
            _scaler._namespace, _scaler._rs_label_selector)
        _replicas = _scaler.set_replica_number(len(_pods.items))

        _logger.debug(f"_replicas: {_replicas}")
