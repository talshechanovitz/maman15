import socket
import threading

import database


class ClientThread(threading.Thread):
    def __init__(self, client_address, client_socket):
        threading.Thread.__init__(self)
        self.client_address = client_address
        self.client_socket = client_socket
        print("New connection added: ", client_address)

    def run(self):
        print("Connection from : ", self.client_address)
        while True:
            data = self.client_socket.recv(2048)
            msg = data.decode()
            if msg == 'bye':
                break
            print("from client", msg)
            self.client_socket.send(bytes(msg, 'UTF-8'))
        print("Client at ", self.client_address, " disconnected...")


class Server:
    DATABASE = "database.db"

    def __init__(self, server_port, host):
        """
        Initialize server
        :param server_port: which port to initialize the server
        :param host:
        """
        self.port = server_port
        self.host = host
        self.database = database.Database(Server.DATABASE)

    def start(self):
        """ Start listen for connections. Contains the main loop. """
        self.database.initialize()
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((self.host, self.port))
        print("Server started")
        print("Waiting for client request..")
        while True:
            server.listen(1)
            clientsock, client_address = server.accept()
            new_thread = ClientThread(client_address, clientsock)
            new_thread.start()
