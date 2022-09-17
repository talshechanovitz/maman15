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
    USERNAME_LEN = 2
    CLIENT_VERSION_LEN = 1
    FILE_SIZE = 2
    REQUEST_TYPE_LEN = 1
    PUBLIC_KEY_LEN = 160
    FILENAME_LEN = 1
    FILE_NAME_STREAM_LEN = 50
    FILE_PATH_LOCATION = '/'
    STREAM_BUFFER = 1024

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
                data = client_thread.recv(ServerManager.USERNAME_LEN)
                username_len = struct.unpack(">H", data)
                data = client_thread.recv(username_len[0])
                user_name = struct.unpack(f"<127s", data)[0]
                user_name_pre = str(user_name.partition(b'\0')[0].decode('utf-8'))
                return RequestHeader.handle_registration_request(client_uuid, client_version, user_name_pre)
            case RequestOp.REQUEST_PUBLIC_KEY.value:
                payload = client_thread.recv(2)
                public_key = client_thread.recv(ServerManager.PUBLIC_KEY_LEN)
                return RequestHeader.exchange_keys(client_uuid, client_version, public_key)
            case RequestOp.UPLOAD_FILE.value:
                payload = client_thread.recv(2)
                filename_len = int.from_bytes(client_thread.recv(ServerManager.FILENAME_LEN),
                                              byteorder='big', signed=False)
                data = client_thread.recv(ServerManager.FILE_NAME_STREAM_LEN)
                file_name = struct.unpack(f"<{ServerManager.FILE_NAME_STREAM_LEN}s", data)[0]
                file_name_pre = str(file_name.partition(b'\0')[0].decode('utf-8'))
                return RequestHeader.upload_file(client_uuid, client_version, file_name_pre)
            case RequestOp.CRC_EQUAL.value:
                payload = client_thread.recv(2)
                filename_len = int.from_bytes(client_thread.recv(ServerManager.FILENAME_LEN),
                                              byteorder='big', signed=False)
                data = client_thread.recv(ServerManager.FILE_NAME_STREAM_LEN)
                file_name = struct.unpack(f"<{ServerManager.FILE_NAME_STREAM_LEN}s", data)[0]
                file_name_pre = str(file_name.partition(b'\0')[0].decode('utf-8'))
                return RequestHeader.crc_ok(client_uuid, client_version, file_name_pre)

    def _handle_registration(self, request: RequestHeader):
        username = request.payload
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

    def _handle_crc_equal(self, request: RequestHeader):
        self._database.update_crc(request.clientID, request.payload)
        if request.request_type.value is RequestOp.CRC_EQUAL.value:
            return Response.general_success(ServerManager.SERVER_VERSION)

    def _handle_request_key(self, request: RequestHeader):
        aes_key = get_random_bytes(16)
        rsa_key = RSA.importKey(request.payload)
        cipher_rsa = PKCS1_OAEP.new(rsa_key)
        encrypte = cipher_rsa.encrypt(aes_key)
        self._database.store_public_key(client_id=request.clientID, public_key=request.payload, aes_key=aes_key)
        logging.info(f"Update public key:{request.payload} in table: Clients")
        return Response.exchange_keypair(ServerManager.SERVER_VERSION, encrypte)

    def _handle_upload_file(self, request: RequestHeader, c: ClientThread):
        file_name = request.payload
        file_path = fr'\files\{request.clientID}\{file_name}'
        file_obj = File(request.clientID, file_name=file_name, path_name=file_path, verified=0)
        if not self._database.store_file(file_obj):
            logging.error(f'Cannot loading file {file_name} for the use {request.clientID}')
            return Response.general_error(ServerManager.SERVER_VERSION)
        iv = c.recv(ServerManager.IV_SIZE)

        aes_key = self._database.find_aes_key(client_id=request.clientID)
        cipher = AES.new(aes_key[0][0], AES.MODE_CBC, iv)
        crc = 0
        file_size = c.recv(ServerManager.FILE_SIZE)
        read_bytes_left = struct.unpack('<H', file_size)[0]
        data = ''
        try:
            with open(file_path, 'wb') as f:
                while len(data) <= read_bytes_left:
                    data = c.recv(ServerManager.STREAM_BUFFER)
                    decrypte_data = cipher.decrypt(data)
                    decrypte_data = decrypte_data[:read_bytes_left]
                    f.write(decrypte_data)
                    crc = zlib.crc32(decrypte_data)
                    read_bytes_left -= len(decrypte_data)
                    logging.info(f"Bytes left to read:{read_bytes_left}")
        except Exception as e:
            pass
        return crc

    def _connection_handle(self, client_thread: ClientThread):
        request = self._parse_request(client_thread)
        res = None
        match request.request_type:
            case RequestOp.REQUEST_REGISTRATION:
                res = self._handle_registration(request)
            case RequestOp.REQUEST_PUBLIC_KEY:
                res = self._handle_request_key(request)
            case RequestOp.UPLOAD_FILE:
                crc = self._handle_upload_file(request, client_thread)
                crc_bytes = struct.pack('<I', crc)
                res = Response(ServerManager.SERVER_VERSION, ResponseOp.UPLOAD_FILE, crc_bytes)
            case RequestOp.CRC_EQUAL:
                res = self._handle_crc_equal(request)
        self._send_response(res, client_thread)

    @staticmethod
    def _send_response(res: Response, client_thread: ClientThread):
        client_thread.send(res.to_buffer())
        client_thread.close()

    def start(self):
        self._database.initialize()
        self._memory_storage.update_memory(self._database.update_memory_status())
        self._server.start()
