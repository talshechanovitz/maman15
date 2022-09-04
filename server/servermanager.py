import logging
import socket
from threading import Thread


class ClientThread:
    def __init__(self, client_socket: socket):
        self._client_socket = client_socket

    def send(self, data: bytes) -> None:
        return self._client_socket.sendall(data)

    def recv(self, buf_size: int) -> bytes:
        return self._client_socket.recv(buf_size)


class ServerManager:

    def __init__(self, server_port, connection_handle):
        """
        Initialize server
        :param server_port: which port to initialize the server.
        : param connection_handle: a new call to run in a new thread for .
        """
        self.port = server_port
        self._connection_handler = connection_handle

    def start(self):
        """ Start listen for connections. Contains the main loop. """
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(("", self.port))
        print("Server started")
        print("Waiting for client request..")
        while True:
            server.listen(1)
            clientsock, client_address = server.accept()
            new_thread = Thread(self._connection_handler, args=(ClientThread(clientsock),))
            new_thread.start()
