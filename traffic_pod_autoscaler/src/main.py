import argparse

from LoggerToolbox import _logger
from proxy import Proxy
from scale_down_watcher import ScaleDownWatcher
from proxy_watcher import ProxyWatcher
from scaler import Scaler


def parse_args():
    _logger.debug("START")

    parser = argparse.ArgumentParser()

    parser.add_argument("--namespace", help="", required=True)
    parser.add_argument(
        "--deployment", help="Name of Deployment to scale", required=False)
    parser.add_argument(
        "--replica-set", help="Name of ReplicaSet to scale", required=False)
    # parser.add_argument(
    #     "--rollout-api", help="Name of Rollout api version", default='argoproj.io/v1alpha1', required=False)
    parser.add_argument(
        "--config-map", help="Name of ConfigMap to store annotation", required=False)
    parser.add_argument(
        "--config-map-refresh-interval", help="Configmap refresh interval, in seconds", required=False, default=10)
    parser.add_argument(
        "--endpoint", help="Name of Endpoints to watch for ready addresses", required=True)
    parser.add_argument(
        "--target-kind", help="Name of kind where to save annotation: deployment or replica_set", default='replica_set', required=False)

    parser.add_argument("--local-address",   help="Proxy listen address",
                        default='',  required=False)
    parser.add_argument("--local-port", help="Proxy listen port",
                        type=int, default=80, required=False)

    parser.add_argument("--min-replicas", help="Number of replicas to start",
                        type=int, default=1, required=False)

    parser.add_argument("--target-address", help="target address to which requests should be proxied (typically the Service name)",
                        dest="remote_address", required=True)
    parser.add_argument("--target-port", help="Target listen port",
                        dest="remote_port", type=int, default=80, required=False)

    parser.add_argument("--check-interval", help="Time between two checks (for the scaler to trigger scale down)",
                        dest="check_interval", type=int, default=60, required=False)
    parser.add_argument("--expiration-time", help="Traffic inactivity duration before scaling to zero (in seconds)",
                        dest="expiration_time", type=int, default=1800, required=False)

    parser.add_argument("--log-level", help="Set log level(DEBUG|INFO|WARNING|ERROR|CRITICAL)",
                        default="INFO", required=False)
    parser.add_argument("--max-retry", help="Number of attempts to wait for the endpoint to be available",
                        dest="max_retry", type=int, default=30, required=False)
    parser.add_argument("--waiting-time", help="Waiting time in ms before 2 retries if endpoint is not yet available",
                        dest="waiting_time", type=int, default=1000, required=False)

    _args = parser.parse_args()

    return _args

def main():
    _args = parse_args()
    _logger.set_level(_args.log_level)
    _logger.debug("START")
    _logger.debug(f"{_args =}")

    try:
        _scaler = Scaler(_args)
        _scale_down_watcher = ScaleDownWatcher(_args, _scaler)

        _proxy = Proxy(_args)
        _proxy_watcher = ProxyWatcher(_args, _proxy)
        #_proxy.set_scaler(_scaler)
        #_proxy.run()
    finally:
        _logger.info("STOP WATCHER")
        _scale_down_watcher.stop()
        _proxy_watcher.stop()
       # _proxy.stop() ??? maybe implements this?


if __name__ == "__main__":
    main()
