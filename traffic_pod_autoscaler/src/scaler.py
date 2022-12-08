
from time import sleep
from LoggerToolbox import _logger
from toolbox import _toolbox
from kubernetes_toolbox import KubernetesToolbox
from datetime import datetime, timezone, timedelta


class Scaler(object):
    _k8s: KubernetesToolbox
    _last_call_at_annotation = 'traffic-pod-autoscaler/last-call-at'
    _scale_down_at_annotation = 'traffic-pod-autoscaler/last-scale-down-at'

    _namespace = ""
    _deployment_name = ""
    _replica_set_name = ""
    # _rollout_api = ""
    _target_kind = ""
    _config_map_name = "traffic-pod-autoscaler-cm"
    _endpoint_name = ""
    _expiration_time: int = 1800
    _replicas = None
    _min_replicas: int = 1
    _max_retry: int = 30
    _waiting_time: int = 1000
    _factor = 1  # timeout series: 1s, 2s, 3s.... 10m

    def __init__(self, args):
        _logger.debug("START")

        if "expiration_time" in args:
            self._expiration_time = args.expiration_time

        if "namespace" in args:
            self._namespace = args.namespace

        if "deployment" in args:
            self._deployment_name = args.deployment

        if "replica_set" in args:
            self._replica_set_name = args.replica_set

        # if "rollout_api" in args:
        #     self._rollout_api = args.rollout_api

        if "target_kind" in args:
            self._target_kind = args.target_kind

        if "config_map" in args:
            self._config_map_name = args.config_map

        if "endpoint" in args:
            self._endpoint_name = args.endpoint

        if "waiting_time" in args:
            self._waiting_time = args.waiting_time

        if "max_retry" in args:
            self._max_retry = args.max_retry

        if "min_replicas" in args:
            self._min_replicas = args.min_replicas

        _logger.info(f"Watching namespace: {self._namespace}")
        _logger.info(f"Watching deployment: {self._deployment_name}")
        _logger.info(f"Watching config_map: {self._config_map_name}")
        _logger.info(f"Watching replica_set: {self._replica_set_name}")
        # _logger.info(f"Watching rollout_api: {self._rollout_api}")
        _logger.info(f"Watching target_kind: {self._target_kind}")
        _logger.info(f"Watching endpoint: {self._endpoint_name}")
        _logger.info(
            f"Traffic expiration time: {self._expiration_time} (in seconds)")
        _logger.info(
            f"Time between 2 checks): {self._waiting_time} (in ms)")
        _logger.info(f"Max retries: {self._max_retry}")

        self._k8s = KubernetesToolbox()

    def get_target_kind(self):
        if self._target_kind == "deployment":
            return "deployment"
        elif self._target_kind == "replica_set":
            return "replica_set"

    def get_replica_number(self):
        _logger.debug("START")
        if self.get_target_kind() == "deployment":
            self._replicas = self._k8s.get_deployment_replica_number(
                self._namespace, self._deployment_name)
        else:
            self._replicas = self._k8s.get_replica_set_replica_number(
                self._namespace, self._replica_set_name)

        return self._replicas

    def update_replica_number(self, _replica=0):
        if self.get_target_kind() == "deployment":
            self._k8s.update_deployment_replica_number(
                self._namespace, self._deployment_name, _replica)
        else:
            self._k8s.update_replica_number(
                self._namespace, self._replica_set_name, _replica)

    def scale_down(self, _replica=0):
        _logger.debug("START")
        self.update_scale_down()
        self.update_replica_number(_replica)

    def update_scale_down(self):
        _logger.debug("START")
        return self._update_annotation_call(self._scale_down_at_annotation)

    def update_last_call(self):
        _logger.debug("START")
        return self._update_annotation_call(self._last_call_at_annotation)

    def _update_annotation_call(self, _annotation):
        _logger.debug("START")
        _now_UTC = _toolbox.get_date_now_utc()
        _updated_annotation = self._k8s.update_config_map_annotation(
            self._namespace, self._config_map_name, _annotation, _now_UTC.isoformat())
        return _updated_annotation

    def get_last_call_annotation(self):
        _last_call_annotation = self._k8s.get_config_map_annotation(
            self._namespace, self._config_map_name, self._last_call_at_annotation)
        _logger.debug(f"_last_call_annotation {_last_call_annotation}")
        return _last_call_annotation

    def is_expired(self):
        _logger.debug("START")
        _last_call_annotation = self.get_last_call_annotation()

        if _last_call_annotation is None:
            self.update_last_call()
            _last_call_annotation = self.get_last_call_annotation()

        _last_call_UTC = _toolbox.get_date_utc_from_string(
            _last_call_annotation)

        _now_UTC = _toolbox.get_date_now_utc()

        if (_last_call_UTC + timedelta(seconds=self._expiration_time)) < _now_UTC:
            return True

        return False

    def make_target_available(self):
        _logger.debug("START")
        self.get_replica_number()

        _logger.debug(f"Current replica number: {self._replicas}")

        if self._replicas == 0 or self._replicas is None:
            self.update_replica_number(self._min_replicas)
            # wait endpoint is available
            __waiting_time_ms = self._waiting_time
            for i in range(1, self._max_retry):
                _endpoint_status = self._k8s.check_endpoint_available(
                    self._namespace, self._endpoint_name)
                if _endpoint_status:
                    return True
                else:
                    __timer = (__waiting_time_ms/1000)
                    _logger.debug(f"Wait {__timer}s before next retry")
                    sleep(__timer)
                    __waiting_time_ms = __waiting_time_ms * self._factor
            return False
