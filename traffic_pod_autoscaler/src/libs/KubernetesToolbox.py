from kubernetes import client, config, watch
from kubernetes.client.rest import ApiException
from libs.LoggerToolbox import _logger


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

    def sanitize_label_selector(self, _label_selector):
        _label_selector = _label_selector.strip('"')
        _label_selector = _label_selector.strip("'")
        return _label_selector

    def create_namespaced_config_map(self, _namespace, _config_map_name):
        _logger.debug("START")

        _body = {"metadata": {
            "name": _config_map_name,
            "namespace": _namespace,
            "labels": {
                "app.kubernetes.io/name": _config_map_name
            }
        }}

        with client.ApiClient(self._configuration) as api_client:
            api_instance = client.CoreV1Api(api_client)
            api_response = api_instance.create_namespaced_config_map(
                namespace=_namespace, body=_body)
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

    def get_replica_number(self, _namespace, _label_selector):
        _logger.debug("START")
        try:
            _replica_set_parents = self.get_replica_set_parents(
                _namespace, _label_selector)
            if len(_replica_set_parents) > 0:
                _replica_set_parents = _replica_set_parents[0]

            _version_full = _replica_set_parents.api_version.split("/")
            _group = _version_full[0]
            _version = _version_full[1]
            _custom_object_name = _replica_set_parents.name
            _custom_object_kind_plural = self.get_kind_plural(
                _replica_set_parents.kind)
            api_response = self.get_namespaced_custom_object(
                _namespace, _group, _version, _custom_object_name, _custom_object_kind_plural)

        except ApiException as e:
            _logger.exception(f"{e}")

        if 'spec' in api_response and 'replicas' in api_response['spec']:
            return api_response['spec']['replicas']
        return 0

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
        try:
            with client.ApiClient(self._configuration) as api_client:
                api_instance = client.CoreV1Api(api_client)
                api_response = api_instance.read_namespaced_config_map(
                    name=_config_map_name, namespace=_namespace)
                _logger.debug(f"{api_response}")

            if _annotation in api_response.metadata.annotations:
                return api_response.metadata.annotations[_annotation]
        except ApiException as api_exception:
            if api_exception.status == 404:
                self.create_namespaced_config_map(_namespace, _config_map_name)
            else:
                _logger.exception(api_exception)

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

            return api_response

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

    def update_replica_set_number(self, _namespace, _replicas, _label_selector):
        _logger.debug("START")
        _logger.info(
            f"Updating replica number to {_replicas} due to traffic activity/inactivity")

        try:
            _replica_set_parents = self.get_replica_set_parents(
                _namespace, _label_selector)
            if len(_replica_set_parents) > 0:
                _replica_set_parents = _replica_set_parents[0]

            _body = {"spec": {"replicas": _replicas}}

            _version_full = _replica_set_parents.api_version.split("/")
            _group = _version_full[0]
            _version = _version_full[1]
            _custom_object_name = _replica_set_parents.name
            _custom_object_kind_plural = self.get_kind_plural(
                _replica_set_parents.kind)
            api_response = self.patch_namespaced_custom_object(
                _namespace, _group, _version, _custom_object_name, _custom_object_kind_plural, _body)

        except ApiException as e:
            _logger.exception(f"{e}")

    def get_kind_plural(self, _kind):
        match _kind.lower():
            case "rollout":
                _kind_plural = "rollouts"
            case "deployment":
                _kind_plural = "deployments"

        return _kind_plural

    # def update_replica_set_replica_number(self, _namespace, _replica_set_name, _replicas):
    #     _logger.debug("START")
    #     _logger.info(
    #         f"Updating replica number to {_replicas} due to traffic activity/inactivity")

    #     _replica_set_name_last = self.get_replica_set_name(
    #         _namespace, _replica_set_name)

    #     with client.ApiClient(self._configuration) as api_client:
    #         api_instance = client.AppsV1Api(api_client)

    #         _body = {"spec": {"replicas": _replicas}}
    #         try:
    #             api_response = api_instance.patch_namespaced_replica_set(
    #                 name=_replica_set_name_last, namespace=_namespace, body=_body, async_req=False)
    #         except ApiException as e:
    #             _logger.exception(f"{e =} {api_response=}")

    def patch_namespaced_custom_object(self, _namespace, _group, _version, _custom_object_name, _custom_object_kind_plural, _body):

        _logger.debug("START")
        _logger.debug(f"Patch custom object {_custom_object_name} ")
        _logger.debug(f"Patch custom object {_namespace =} ")
        _logger.debug(f"Patch custom object {_group =} ")
        _logger.debug(f"Patch custom object {_version =} ")
        _logger.debug(f"Patch custom object {_custom_object_kind_plural =} ")
        _logger.debug(f"Patch custom object {_body =} ")

        with client.ApiClient(self._configuration) as api_client:
            api_instance = client.CustomObjectsApi(api_client)

            try:
                # '/apis/{group}/{version}/namespaces/{namespace}/{plural}/{name}'
                # '/apis/apps/v1/namespaces/{namespace}/deployments/{name}'
                api_response = api_instance.patch_namespaced_custom_object(
                    namespace=_namespace, group=_group, version=_version, name=_custom_object_name, plural=_custom_object_kind_plural, body=_body)
                _logger.debug(f"Patch custom object {api_response} ")
                return api_response
            except ApiException as e:
                _logger.exception(f"{e}")

    def get_namespaced_custom_object(self, _namespace, _group, _version, _custom_object_name, _custom_object_kind_plural):

        _logger.debug("START")
        _logger.debug(f"Patch custom object {_custom_object_name} ")
        _logger.debug(f"Patch custom object {_namespace =} ")
        _logger.debug(f"Patch custom object {_group =} ")
        _logger.debug(f"Patch custom object {_version =} ")
        _logger.debug(f"Patch custom object {_custom_object_kind_plural =} ")

        with client.ApiClient(self._configuration) as api_client:
            api_instance = client.CustomObjectsApi(api_client)

            try:
                api_response = api_instance.get_namespaced_custom_object(
                    namespace=_namespace, group=_group, version=_version, name=_custom_object_name, plural=_custom_object_kind_plural, async_req=False)
                _logger.debug(f"Patch custom object {api_response} ")
                return api_response
            except ApiException as e:
                _logger.exception(f"{e}")

    def get_replica_set_name(self, _namespace, _label_selector):
        _logger.debug("START")
        _replica_set_name_last = self.get_replica_set_field(
            _namespace, "name", _label_selector)
        return _replica_set_name_last

    def get_replica_set_parents(self, _namespace, _label_selector):
        _logger.debug("START")
        _replica_set_parents = self.get_replica_set_field(
            _namespace, "parents", _label_selector)

        return _replica_set_parents

    def get_replica_set_field(self, _namespace, _field, _label_selector='', _limit=1):
        _logger.debug("START")
        _rs = None

        with client.ApiClient(self._configuration) as api_client:
            api_instance = client.AppsV1Api(api_client)

            try:
                api_response = api_instance.list_namespaced_replica_set(
                    namespace=_namespace, label_selector=_label_selector, limit=_limit, watch=False)

                for __rs in api_response.items:
                    _rs = __rs
                    break

            except ApiException as e:
                _logger.exception(f"{e =} {api_response=}")

            # _logger.info(f"find replica_set_name api_response: {api_response}")
            _logger.debug(f"find replica_set_name {_rs.metadata.name}")

            if _field == "name":
                return _rs.metadata.name
            elif _field == "parents":
                return _rs.metadata.owner_references

            return _rs

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

    def list_namespaced_pod(self, _namespace, _label_selector):
        _logger.debug("START")

        with client.ApiClient(self._configuration) as api_client:
            api_instance = client.CoreV1Api(api_client)

            api_response = api_instance.list_namespaced_pod(
                namespace=_namespace, label_selector=_label_selector, timeout_seconds=1)
            _logger.debug(f"{api_response =}")
            return api_response
