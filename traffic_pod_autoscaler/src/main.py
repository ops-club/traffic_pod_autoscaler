import argparse

from libs.LoggerToolbox import _logger
from Proxy import Proxy
from ProxyWatcher import ProxyWatcher
from Scaler import Scaler
from ScalerWatcher import ScalerWatcher
from PodsWatcher import PodsWatcher
from HTTPServer import HTTPServer


def parse_args():
    _logger.debug("START")

    parser = argparse.ArgumentParser()

    parser.add_argument("--namespace", help="", required=True)

    parser.add_argument(
        "--endpoint", help="Name of Endpoints to watch for ready addresses", required=True)

    parser.add_argument(
        "--rs-label-selector", help="Label Selector on replicaset", required=True)

    parser.add_argument("--target-address", help="target address to which requests should be proxied (typically the Service name)",
                        dest="remote_address", required=True)
    parser.add_argument("--target-port", help="Target listen port",
                        dest="remote_port", type=int, default=80, required=False)

    parser.add_argument("--min-replicas", help="Number of replicas to start",
                        type=int, default=1, required=False)

    parser.add_argument(
        "--config-map", help="Name of ConfigMap to store annotation", default="traffic-pod-autoscaler-cm", required=False)

    parser.add_argument("--local-address",   help="Proxy listen address",
                        default='',  required=False)
    parser.add_argument("--local-port", help="Proxy listen port",
                        type=int, default=80, required=False)

    parser.add_argument("--sock-max-handle-buffer", help="TCP Sock Proxy number of connection can be handle before rejected",
                        type=int, default=200, required=False)

    parser.add_argument("--update-annotation-refresh-interval", help="time delta in seconds between two updates of the last call annotation",
                        type=int, default=20, required=False)

    parser.add_argument("--check-interval", help="Time between two checks (for the scaler to trigger scale down)",
                        dest="check_interval", type=int, default=60, required=False)
    parser.add_argument("--pods-check-interval", help="Time between two checks on pods number",
                        dest="pods_check_interval", type=int, default=5, required=False)
    parser.add_argument("--expiration-time", help="Traffic inactivity duration before scaling to zero (in seconds)",
                        dest="expiration_time", type=int, default=1800, required=False)

    parser.add_argument("--log-level", help="Set log level(DEBUG|INFO|WARNING|ERROR|CRITICAL)",
                        default="INFO", required=False)
    parser.add_argument("--max-retry", help="Number of attempts to wait for the endpoint to be available",
                        dest="max_retry", type=int, default=30, required=False)
    parser.add_argument("--waiting-time", help="Waiting time in ms before 2 retries if endpoint is not yet available",
                        dest="waiting_time", type=int, default=1000, required=False)

    parser.add_argument("--http-server-port", help="HTTP server listen port",
                        type=int, default=8080, required=False)
    parser.add_argument("--metrics-url", help="HTTP server metrics URL",
                        default="/metrics", required=False)
    parser.add_argument("--ping-url", help="HTTP server ping URL",
                        default="/ping", required=False)

    _args = parser.parse_args()

    return _args


def main():
    _args = parse_args()
    _logger.set_level(_args.log_level)
    _logger.debug("START")
    _logger.debug(f"{_args =}")

    try:
        _scaler = Scaler(_args)
        _scaler_watcher = ScalerWatcher(_args.check_interval, _args, _scaler)
        _pods_watcher = PodsWatcher(_args.pods_check_interval, _args, _scaler)

        _proxy = Proxy(_args)
        _proxy.set_scaler(_scaler)
        _proxy_watcher = ProxyWatcher(
            _args.update_annotation_refresh_interval, _args, _proxy)

        _httpserver = HTTPServer(_args, _proxy)

        _proxy.run()
    except Exception as e:
        _logger.exception(f"Exception:main_main:{e}")
    finally:
        _logger.info("STOP WATCHER")
        _httpserver.stop()
        _scaler_watcher.stop()
        _proxy_watcher.stop()
        _pods_watcher.stop()


if __name__ == "__main__":
    main()
