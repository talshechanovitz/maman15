import filecmp
import struct
import zlib
from datetime import datetime
from uuid import UUID, uuid4
from response import ResponseOp, Response
from Crypto.PublicKey import RSA
from database import Database, Client, File
from storage_on_memory import MemoryStorage
from request import RequestHeader, RequestOp
from networkmanager import NetworkManager, ClientThread
import logging
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Random import get_random_bytes


class ServerManager:
    DATABASE = "database.db"
    UUID_SIZE = 16
    IV_SIZE = 16
    DEFAULT_CLIENT_VERSION = 0
    SERVER_VERSION = 3
    USERNAME_LEN = 1
    CLIENT_VERSION_LEN = 1
    REQUEST_TYPE_LEN = 1
    PUBLIC_KEY_LEN = 162
    FILENAME_LEN = 1
    FILE_PATH_LOCATION = '/'
    STREAM_BUFFER = 4096

    def __init__(self, server_port: int):
        self._database = Database(ServerManager.DATABASE)
        self._server = NetworkManager(server_port=server_port, connection_handle=self._connection_handle)
        self._memory_storage = MemoryStorage()

    @staticmethod
    def _parse_request(client_thread: ClientThread) -> RequestHeader:
        logging.info("A client has connected.")
        data = client_thread.recv(ServerManager.UUID_SIZE)
        client_uuid_raw0, client_uuid_raw1 = struct.unpack('<QQ', data)
        client_uuid_raw = (client_uuid_raw0 << 64) | client_uuid_raw1
        try:
            client_uuid = UUID(int=client_uuid_raw)
            print(client_uuid)
        except ValueError:
            logging.error(f"Invalid client UUID: {client_uuid_raw}")
            return RequestHeader(UUID(int=0), ServerManager.DEFAULT_CLIENT_VERSION, RequestOp.UNKNOWN)
        data = client_thread.recv(ServerManager.CLIENT_VERSION_LEN)
        client_version = struct.unpack('<B', data)[0]
        print(f"client_Version:{client_version}")
        data = client_thread.recv(ServerManager.REQUEST_TYPE_LEN)
        request_code = struct.unpack('<B', data)[0]
        print(f"request_code:{request_code}")
        try:
            request_type = RequestOp(request_code)
        except ValueError:
            logging.error(f"Unknown request code:{request_code}")
            return RequestHeader(client_uuid, client_version, RequestOp.UNKNOWN)
        logging.info(f"new request of type {request_type.name}")
        match request_type.value:
            case RequestOp.REQUEST_REGISTRATION.value:
                username_len = int.from_bytes(client_thread.recv(ServerManager.USERNAME_LEN),
                                              byteorder='big', signed=False)
                username = client_thread.recv(username_len)
                return RequestHeader.handle_registration_request(client_uuid, client_version, username)
            case RequestOp.REQUEST_PUBLIC_KEY.value:
                public_key = client_thread.recv(ServerManager.PUBLIC_KEY_LEN)
                return RequestHeader.exchange_keys(client_uuid, client_version, public_key)
            case RequestOp.UPLOAD_FILE.value:
                filename_len = int(client_thread.recv(ServerManager.FILENAME_LEN))
                filename = client_thread.recv(filename_len)
                return RequestHeader.upload_file(client_uuid, client_version, filename)
            case RequestOp.CRC_EQUAL.value:
                return RequestHeader.crc_ok(client_uuid, client_version)

    def _handle_registration(self, request: RequestHeader):
        username = request.payload.decode()
        if self._memory_storage.user_is_exist(username):
            logging.error(f"Cannot register this user {username} with uuid {request.clientID} "
                          f"because he is already registered")
            return Response(ServerManager.SERVER_VERSION, ResponseOp.USER_ALREADY_EXIST, payload=b'')
        logging.info(f"Register new user {username}:{request.clientID}")
        uuid = uuid4()
        self._memory_storage.add_user_to_memory(username=username, client_uuid=uuid)
        client = Client(cid=uuid, cname=username, public_key=None,
                        last_seen=datetime.now(), aes_key=None)
        self._database.store_client(clnt=client)
        logging.info("Registered new Client to DB")
        return Response.register_success(ServerManager.SERVER_VERSION, uuid)

    def _handle_request_key(self, request: RequestHeader):
        aes_key = get_random_bytes(16)
        rsa_key = RSA.importKey(request.payload)
        cipher_rsa = PKCS1_OAEP.new(rsa_key)
        encrypte = cipher_rsa.encrypt(aes_key)
        self._database.store_public_key(client_id=request.clientID, public_key=request.payload, aes_key=aes_key)
        logging.info(f"Update public key:{request.payload} in table: Clients")
        return Response.exchange_keypair(ServerManager.SERVER_VERSION, aes_key)

    def _handle_upload_file(self, request: RequestHeader, c: ClientThread):
        file_name = request.payload
        file_path = fr'{request.clientID}\{file_name}'
        file_obj = File(request.clientID, file_name=file_name, path_name=file_path, verified=False)
        self._database.store_file(file_obj)
        iv = c.recv(ServerManager.IV_SIZE)
        aes_key = self._database.find_aes_key(client_id=request.clientID)
        cipher = AES.new(aes_key, AES.MODE_CBC, iv)
        next_data = None
        prev_crc = 0


    def _connection_handle(self, client_thread: ClientThread):

        request = self._parse_request(client_thread)
        res = None
        match request.request_type:
            case RequestOp.REQUEST_REGISTRATION:
                res = self._handle_registration(request)
            case RequestOp.REQUEST_PUBLIC_KEY:
                res = self._handle_request_key(request)
            case RequestOp.UPLOAD_FILE:
                res = self._handle_upload_file(request, client_thread)
            # case RequestOp.CRC_EQUAL:
            #     self._handle_crc_equal(request)
        print(res.response_status())
        self._send_response(res, client_thread)

    @staticmethod
    def _send_response(res: Response, client_thread: ClientThread):
        client_thread.send(res.to_buffer())
        client_thread.close()

    def start(self):
        self._database.initialize()
        self._memory_storage.update_memory(self._database.update_memory_status())
        self._server.start()
