from kubernetes import client, config, watch
from kubernetes.client.rest import ApiException
from LoggerToolbox import _logger


class KubernetesToolbox(object):

    _in_cluster: bool
    _configuration: config

    def __init__(self, _in_cluster=True):
        _logger.debug("START")
        self._in_cluster = _in_cluster
        self.load_kube_config()

    def load_kube_config(self):
        _logger.debug("START")
        if self._in_cluster:
            self._configuration = config.load_incluster_config()
        else:
            self._configuration = config.load_kube_config()

    # Deployments
    def get_deployment_annotation(self, _namespace, _deployment_name, _annotation):
        _logger.debug("START")
        with client.ApiClient(self._configuration) as api_client:
            api_instance = client.AppsV1Api(api_client)
            api_response = api_instance.read_namespaced_deployment(
                name=_deployment_name, namespace=_namespace)

        if _annotation in api_response.metadata.annotations:
            return api_response.metadata.annotations[_annotation]
        else:
            return None

    def get_deployment_status(self, _namespace, _deployment_name):
        _logger.debug("START")
        with client.ApiClient(self._configuration) as api_client:
            api_instance = client.AppsV1Api(api_client)
            api_response = api_instance.read_namespaced_deployment(
                name=_deployment_name, namespace=_namespace)

            if api_response.status.available_replicas > 0:
                return True

        return False

    def get_deployment(self, _namespace, _deployment_name):
        _logger.debug("START")
        with client.ApiClient(self._configuration) as api_client:
            api_instance = client.AppsV1Api(api_client)

            try:
                api_response = api_instance.read_namespaced_deployment(
                    name=_deployment_name, namespace=_namespace)
            except ApiException as e:
                _logger.exception(e)

            return api_response

    def get_deployment_replica_number(self, _namespace, _deployment_name):
        _logger.debug("START")
        with client.ApiClient(self._configuration) as api_client:
            api_instance = client.AppsV1Api(api_client)
            api_response = api_instance.read_namespaced_deployment(
                name=_deployment_name, namespace=_namespace)

            if api_response.status.available_replicas is None:
                return 0
            return api_response.status.available_replicas

    def get_replica_set_replica_number(self, _namespace, _replica_set_name):
        _logger.debug("START")

        _replica_set_name_last = self.get_replica_set_name(
            _namespace, _replica_set_name)

        with client.ApiClient(self._configuration) as api_client:
            api_instance = client.AppsV1Api(api_client)
            api_response = api_instance.read_namespaced_replica_set(
                name=_replica_set_name_last, namespace=_namespace)

            if api_response.status.available_replicas is None:
                return 0
            return api_response.status.available_replicas

    def update_deployment_annotation(self, _namespace, _deployment_name, _annotation, _annotation_value):
        _logger.debug("START")
        with client.ApiClient(self._configuration) as api_client:
            api_instance = client.AppsV1Api(api_client)

            _body = {"metadata": {"annotations": {
                f"{_annotation}": _annotation_value}}}

            try:
                api_response = api_instance.patch_namespaced_deployment(
                    name=_deployment_name, namespace=_namespace, body=_body, async_req=False)
            except ApiException as e:
                _logger.exception(e)

    def get_config_map_annotation(self, _namespace, _config_map_name, _annotation):
        _logger.debug("START")
        with client.ApiClient(self._configuration) as api_client:
            api_instance = client.CoreV1Api(api_client)
            api_response = api_instance.read_namespaced_config_map(
                name=_config_map_name, namespace=_namespace)

        if _annotation in api_response.metadata.annotations:
            return api_response.metadata.annotations[_annotation]
        else:
            return None

    def update_config_map_annotation(self, _namespace, _config_map_name, _annotation, _annotation_value):
        _logger.debug("START")
        with client.ApiClient(self._configuration) as api_client:
            api_instance = client.CoreV1Api(api_client)

            _body = {"metadata": {"annotations": {
                f"{_annotation}": _annotation_value}}}

            try:
                api_response = api_instance.patch_namespaced_config_map(
                    name=_config_map_name, namespace=_namespace, body=_body, async_req=False)
            except ApiException as e:
                _logger.exception(e)

    def update_deployment_replica_number(self, _namespace, _deployment_name, _replicas):
        _logger.debug("START")
        _logger.info(
            f"Updating replica number to {_replicas} due to traffic activity/inactivity")

        with client.ApiClient(self._configuration) as api_client:
            api_instance = client.AppsV1Api(api_client)

            _body = {"spec": {"replicas": _replicas}}
            try:
                api_response = api_instance.patch_namespaced_deployment(
                    name=_deployment_name, namespace=_namespace, body=_body, async_req=False)
            except ApiException as e:
                _logger.exception(f"{e =} {api_response=}")

    def update_replica_set_replica_number(self, _namespace, _replica_set_name, _replicas):
        _logger.debug("START")
        _logger.info(
            f"Updating replica number to {_replicas} due to traffic activity/inactivity")

        _replica_set_name_last = self.get_replica_set_name(
            _namespace, _replica_set_name)

        with client.ApiClient(self._configuration) as api_client:
            api_instance = client.AppsV1Api(api_client)

            _body = {"spec": {"replicas": _replicas}}
            try:
                api_response = api_instance.patch_namespaced_replica_set(
                    name=_replica_set_name_last, namespace=_namespace, body=_body, async_req=False)
            except ApiException as e:
                _logger.exception(f"{e =} {api_response=}")

    def get_replica_set_name(self, _namespace, _replica_set_name):
        _logger.debug("START")
        _replica_set_name_last = ''

        with client.ApiClient(self._configuration) as api_client:
            api_instance = client.AppsV1Api(api_client)
            limit = 1
            label_selector = ''

            try:
                api_response = api_instance.list_namespaced_replica_set(
                    namespace=_namespace, label_selector=label_selector, limit=limit, watch=False)
                for rs in api_response.items:
                    _rs_name = rs.metadata.name
                    if _rs_name.startswith(_replica_set_name):
                        _replica_set_name_last = _rs_name

            except ApiException as e:
                _logger.exception(f"{e =} {api_response=}")

            # _logger.info(f"find replica_set_name api_response: {api_response}")
            _logger.info(f"find replica_set_name {_replica_set_name_last}")
            return _replica_set_name_last

    # Endpoints
    def check_endpoint_available(self, _namespace, _endpoint_name):
        _logger.debug("START")
        with client.ApiClient(self._configuration) as api_client:
            api_instance = client.CoreV1Api(api_client)
            api_response = api_instance.read_namespaced_endpoints(
                name=_endpoint_name, namespace=_namespace)

            if hasattr(api_response, 'subsets'):
                if api_response.subsets:
                    _logger.debug(f"found subsets")
                    for subset in api_response.subsets:
                        _logger.debug(f"subset: {subset}")
                        if hasattr(subset, 'addresses'):
                            if subset.addresses is not None:
                                for address in subset.addresses:
                                    if hasattr(address, 'ip'):
                                        _logger.debug(
                                            f"IP address: {address.ip}")
                                        return True
                            else:
                                _logger.debug(
                                    "subset.addresses was set to None")
            else:
                _logger.debug("subsets not found")
            return False
