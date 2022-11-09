import socket
# import socks
import select
import string
import sys
import time


from LoggerToolbox import _logger
from toolbox import _toolbox
from scaler import Scaler


class Proxy(object):
    local_address: string
    local_port: int
    metrics_server: bool = False
    metrics_port: int
    remote_address: string
    remote_port: int
    lsock: list = []
    msg_queue: dict = {}
    _scaler: Scaler

    _stats_request: list = []

    def __init__(self, args):
        _logger.debug("START")

        if "local_address" in args:
            self.local_address = args.local_address

        if "local_port" in args:
            self.local_port = args.local_port

        if "metrics_port" in args:
            self.metrics_port = args.metrics_port

        if "remote_address" in args:
            self.remote_address = args.remote_address

        if "remote_port" in args:
            self.remote_port = args.remote_port

        _logger.info(f"Proxy local_address: {self.local_address}")
        _logger.info(f"Proxy local_port: {self.local_port}")
        if self.metrics_server:
            _logger.info(f"Proxy metrics_port: {self.metrics_port}")
        _logger.info(f"Proxy remote_address: {self.remote_address}")
        _logger.info(f"Proxy remote_port: {self.remote_port}")

        # super(ClassName, self).__init__(*args))

    def set_scaler(self, _scaler: Scaler):
        _logger.debug("START")
        self._scaler = _scaler

    def run(self):
        _logger.debug("START")
        try:
            return self.tcp_server()
        except Exception as e:
            _logger.exception(e)

    def tcp_server(self):
        _logger.debug("START")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.setblocking(0)
            sock.bind((self.local_address, int(self.local_port)))
            sock.listen(3)
            self.lsock.append(sock)

            _logger.info(
                f'Listening on {self.local_address}:{self.local_port}')

            while True:
                readable, writable, exceptional = select.select(
                    self.lsock, [], [])
                for s in readable:
                    if s == sock:
                        self.hit_request()  # very important, else target will not be available to connect
                        rserver = self.remote_conn()
                        if rserver:
                            client, addr = sock.accept()
                            self.stats_add_request_infos(addr[0])
                            _logger.info('Accepted connection from {0}:{1}'.format(
                                addr[0], addr[1]))
                            self.store_sock(client, addr, rserver)
                            break
                        else:
                            _logger.error('the connection with the remote server can\'t be \
                            established')
                            _logger.info(
                                'Connection with {} is closed'.format(addr[0]))
                            client.close()
                    data = self.received_from(s, 3)
                    self.msg_queue[s].send(data)
                    if len(data) == 0:
                        self.close_sock(s)
                        break
                    else:
                        _logger.debug(
                            'Received {} bytes from client '.format(len(data)))
                        # here if we want to update reponse
        except KeyboardInterrupt:
            _logger.info('Ending server')
        except Exception as e:
            _logger.debug(f"Failed to listen on {self.local_address}:{self.local_port}")
            _logger.exception(f"Exception::{e}")
            sys.exit(0)
            # return 1
        # finally:
            # sys.exit(0)
            # return 1

    def remote_conn(self):
        _logger.debug("START")
        counter = 0
        max_attempts = 60
        while (counter < max_attempts):
            try:
                remote_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                remote_sock.connect((self.remote_address, int(self.remote_port)))
                return remote_sock
            except Exception as e:
                counter += 1
                _logger.debug(f"Sleep 1s due to connect failure ({counter}/{max_attempts}): {e}")
                time.sleep(1)
        _logger.exception(f"Max connect attempts reached ({max_attempts}).")
        return False

    def store_sock(self, client, addr, rserver):
        _logger.debug("START")
        self.lsock.append(client)
        self.lsock.append(rserver)

        try:
            self.msg_queue[client] = rserver
            self.msg_queue[rserver] = client
        except Exception as e:
            _logger.exception(e)

    def received_from(self, sock, timeout):
        _logger.debug("START")
        data = ""
        sock.settimeout(timeout)
        try:
            while True:
                data = sock.recv(4096)
                if not data:
                    break
                data = + data
        except:
            pass
        return data

    def close_sock(self, sock):
        _logger.debug('End of connection with {}'.format(sock.getpeername()))
        self.lsock.remove(self.msg_queue[sock])
        self.lsock.remove(self.msg_queue[self.msg_queue[sock]])
        serv = self.msg_queue[sock]
        self.msg_queue[serv].close()
        self.msg_queue[sock].close()
        del self.msg_queue[sock]
        del self.msg_queue[serv]

    def get_stats_request(self):
        return self._stats_request

    def hit_request(self):
        _logger.debug("START")
        try:
            self._scaler.update_last_call()
            self._scaler.make_target_available()
        except Exception as e:
            _logger.exception(e)

    def stats_add_request_infos(self, _from=""):
        _logger.debug("START")
        self._stats_request.append(
            {
                'from': _from,
                'when': _toolbox.get_date_now_utc()
            }
        )
