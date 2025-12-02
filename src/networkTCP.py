# networkTCP.py
# Simple TCP helper for a 1-to-1 connection with newline-delimited messages.
# Usage:
#   server = TCPServer(port, on_message_callback)
#   client = TCPClient(host, port, on_message_callback)
#
# on_message_callback(msg_str) will be called on a background thread; GUI should marshal to main thread.

import socket
import threading
from typing import Callable, Optional

BUFFER_SIZE = 4096


class TCPConnection:
    def __init__(self, sock: socket.socket, on_message: Callable[[str], None]):
        self.sock = sock
        self.on_message = on_message
        self._running = True
        self._thread = threading.Thread(target=self._recv_loop, daemon=True)
        self._thread.start()

    def _recv_loop(self):
        buffer = ""
        try:
            while self._running:
                data = self.sock.recv(BUFFER_SIZE)
                if not data:
                    break
                buffer += data.decode('utf-8', errors='replace')
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if line:
                        try:
                            self.on_message(line)
                        except Exception:
                            # swallow exceptions in callback to keep loop alive
                            pass
        except Exception:
            pass
        finally:
            self.close()

    def send(self, msg: str):
        if not msg.endswith('\n'):
            msg = msg + '\n'
        try:
            self.sock.sendall(msg.encode('utf-8'))
        except Exception:
            # connection might be dead; ignore for now
            self.close()

    def close(self):
        if self._running:
            self._running = False
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            try:
                self.sock.close()
            except Exception:
                pass


# Server: listens for a single connection; when client connects, returns TCPConnection
class TCPServer:
    def __init__(self, port: int, on_message: Callable[[str], None], on_client_connected: Optional[Callable[[], None]] = None):
        self.port = port
        self.on_message = on_message
        self.on_client_connected = on_client_connected
        self._server_sock = None
        self._thread = threading.Thread(target=self._listen_thread, daemon=True)
        self._connection: Optional[TCPConnection] = None
        self._thread.start()

    def _listen_thread(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(('', self.port))
            s.listen(1)
            self._server_sock = s
            client_sock, addr = s.accept()
            # create connection object
            self._connection = TCPConnection(client_sock, self.on_message)
            if self.on_client_connected:
                try:
                    self.on_client_connected()
                except Exception:
                    pass
        except Exception:
            pass
        finally:
            # server socket is no longer needed after accept
            try:
                if self._server_sock:
                    self._server_sock.close()
            except Exception:
                pass
            self._server_sock = None

    def send(self, msg: str):
        if self._connection:
            self._connection.send(msg)

    def close(self):
        if self._connection:
            self._connection.close()
            self._connection = None
        try:
            if self._server_sock:
                self._server_sock.close()
        except Exception:
            pass


# Client: connects to server and returns TCPConnection via callback
class TCPClient:
    def __init__(self, host: str, port: int, on_message: Callable[[str], None], on_connected: Optional[Callable[[], None]] = None):
        self.host = host
        self.port = port
        self.on_message = on_message
        self.on_connected = on_connected
        self._connection: Optional[TCPConnection] = None
        self._thread = threading.Thread(target=self._connect_thread, daemon=True)
        self._thread.start()

    def _connect_thread(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.host, self.port))
            self._connection = TCPConnection(s, self.on_message)
            if self.on_connected:
                try:
                    self.on_connected()
                except Exception:
                    pass
        except Exception:
            # could not connect
            pass

    def send(self, msg: str):
        if self._connection:
            self._connection.send(msg)

    def close(self):
        if self._connection:
            self._connection.close()
            self._connection = None
