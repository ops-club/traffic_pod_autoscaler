import socket
# import socks
import select
import string
import sys
import time

from libs.LoggerToolbox import _logger
from libs.Toolbox import _toolbox
from Scaler import Scaler


class Proxy(object):
    local_address: string
    local_port: int
    _annotation_last_update: int
    _last_call = None
    _update_annotation_refresh_interval: int
    _update_annotation_refresh_interval_delta: int
    metrics_server: bool = False
    metrics_port: int
    _remote_address: string
    _remote_port: int
    remote_timeout: int
    _sock_max_handle_buffer: int = 200
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
            self._remote_address = args.remote_address

        if "remote_port" in args:
            self._remote_port = args.remote_port

        if "sock_max_handle_buffer" in args:
            self._sock_max_handle_buffer = args.sock_max_handle_buffer

        if "remote_timeout" in args:
            self.remote_timeout = args.remote_timeout

        if "update_annotation_refresh_interval" in args:
            self._update_annotation_refresh_interval = args.update_annotation_refresh_interval

        _logger.info(f"Proxy local_address: {self.local_address}")
        _logger.info(f"Proxy local_port: {self.local_port}")

        _logger.info(f"Proxy remote_address: {self._remote_address}")
        _logger.info(f"Proxy remote_port: {self._remote_port}")
        _logger.info(f"Proxy remote_timeout: {self.remote_timeout}")

        if self.metrics_server:
            _logger.info(f"Proxy metrics_port: {self.metrics_port}")

        # Define n seconds as a timedelta object
        self._update_annotation_refresh_interval_delta = _toolbox.get_date_timedelta_seconds(
            self._update_annotation_refresh_interval)

    def set_scaler(self, _scaler: Scaler):
        _logger.debug("START")
        self._scaler = _scaler

    def run(self):
        _logger.debug("START")
        try:
            return self.tcp_server()
        except Exception as e:
            _logger.exception(f"Exception:Proxy_Run:{e}")

    def tcp_server(self):
        _logger.debug("START")

        try:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.setblocking(True)
                sock.bind((self.local_address, int(self.local_port)))
                sock.listen(self._sock_max_handle_buffer)

                self.lsock.append(sock)

                _logger.info(
                    f'Listening on {self.local_address}:{self.local_port}')
            except Exception as e:
                _logger.exception(
                    f"Exception:Proxy_tcp_server:{e} // Failed to listen on {self.local_address}:{self.local_port}")

            while True:
                readable, writable, exceptional = select.select(
                    self.lsock, [], [])
                for s in readable:
                    if s == sock:
                        self.hit_request()  # very important, else target will not be available to connect
                        try:
                            rserver = self.remote_conn()
                        except Exception as e:
                            _logger.error(
                                "the connection with the remote server can't be established")

                        if rserver:
                            try:

                                ########################
                                ########################
                                ########################
                                # tmp do debug
                                # from random import randrange
                                # number = randrange(10)
                                # if number % 2 == 0:
                                #     raise Exception("Sorry, 502")
                                ########################
                                ########################
                                ########################

                                client, addr = sock.accept()

                                self.stats_add_request_infos(addr[0])
                                _logger.info(
                                    f"Accepted connection from {addr[0]}:{addr[1]}")
                                self.store_sock(client, addr, rserver)
                            except Exception as e:
                                _logger.info(f"Exception:sock.accept: {e}")
                        # else:
                        #     _logger.info(
                        #         'Connection with {} is closed'.format(addr[0]))

                    try:
                        data = self.received_from(s)
                    except Exception as e:
                        _logger.exception(
                            f"Exception:Proxy_tcp_server_received_from:{e}")

                    # number = randrange(10)
                    # if number % 2 == 0:
                    #     data = ''
                    #     _logger.info('force data to empty str')
                    # _logger.trace(f"Exception:data_debug:{data}")

                    if not isinstance(data, bytes):
                        data = bytes(data, 'utf-8')

                    try:
                        self.send_data(self.msg_queue[s], data)

                    except Exception as e:
                        _logger.exception(f"Exception:send_data:{e}")

                    if len(data) == 0:
                        _logger.trace(
                            f"Exception:Proxy_tcp_server:Received 0 byte from client")
                        try:
                            self.close_sock(s)
                            # client.close()
                        except Exception as e:
                            _logger.info(f"Exception:client.close: {e}")
                    else:
                        _logger.trace(
                            f'Received {len(data)} bytes from client ')

        except KeyboardInterrupt:
            _logger.info('Ending server')
        except Exception as e:
            _logger.exception(f"Exception:Proxy_tcp_server:{e}")

    def remote_conn(self):
        _logger.debug("START")
        counter = 0
        max_attempts = 60
        while (counter < max_attempts):
            try:
                remote_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                # remote_sock.settimeout(int(self.remote_timeout))
                remote_sock.connect(
                    (self._remote_address, int(self._remote_port)))

                return remote_sock
            except Exception as e:
                counter += 1
                _logger.debug(
                    f"Sleep 1s due to connect failure ({counter}/{max_attempts}): {e}")
                time.sleep(1)

        _exception_msg = f"Exception:Proxy_remote_conn: Max connect attempts reached ({max_attempts})."
        _logger.exception(_exception_msg)

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

    def send_data(self, sock: socket.socket, _data):
        try:
            if self.sock_is_open(sock):
                # Send data over the socket
                sock.setblocking(False)
                sock.send(_data)

        except socket.error as err:
            # Handle the Errno 107 error
            if err.errno == 107:
                _logger.info("The connection was closed by the server.")
                # Re-establish the connection and try again
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                _addr = sock.getsockname()
                _logger.info(
                    f"Try to connect to the server:{_addr}")
                sock.connect(_addr)
                sock.send(_data)
            else:
                # Handle other errors
                _logger.debug("An error occurred:", err)

    def received_from(self, sock: socket.socket):
        _logger.debug("START")

        BUFF_SIZE = 4096
        _data = b""

        # sock.settimeout(int(self.remote_timeout))
        sock.setblocking(False)

        try:
            while True:
                try:
                    if self.sock_is_open(sock):
                        data = sock.recv(BUFF_SIZE)
                        _data += data
                        if not data or len(data) < BUFF_SIZE:
                            break
                    else:
                        break

                except socket.error as err:

                    if err.errno == 107:
                        _logger.debug(
                            "The connection was closed by the server.")
                        break
                    elif err.errno == 110:
                        _logger.debug(
                            "The connection was timeout by the server.")
                        break
                    else:
                        break

        except Exception as e:
            _logger.exception(f"Exception:Proxy_received_from:{e}")

        return _data

    def close_sock(self, sock):
        _logger.debug('End of connection with {}'.format(sock.getpeername()))

        self.lsock.remove(self.msg_queue[sock])
        self.lsock.remove(self.msg_queue[self.msg_queue[sock]])
        serv = self.msg_queue[sock]

        # Check the status of the socket
        if self.sock_is_open(sock):
            _logger.debug("The socket is open and connected.")
            self.msg_queue[serv].close()
            self.msg_queue[sock].close()
        else:
            _logger.debug("The socket is closed.")

        del self.msg_queue[sock]
        del self.msg_queue[serv]

    def sock_is_open(self, sock):
        # Check the status of the socket
        if sock.fileno() > 0:
            return True
        return False

    def get_stats_request(self):
        return self._stats_request

    def hit_request(self):
        _logger.debug("START")
        try:
            self._last_call = _toolbox.get_date_now_utc()
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

    def update_annotation_last_call(self):
        try:
            if self._last_call is not None:
                # use watcher to avoid updating the configmap too often
                _last_call_annotation = self._scaler.get_last_call_annotation()
                _last_call_annotation_UTC = _toolbox.get_date_utc_from_string(
                    _last_call_annotation)

                _diff = self._last_call - _last_call_annotation_UTC

                if _diff > _toolbox.get_date_timedelta_seconds(5):
                    self._scaler.update_last_call()
        except Exception as e:
            _logger.exception(e)
