import struct
from datetime import datetime
from uuid import UUID

from database import Database,Client
from storage_on_memory import MemoryStorage
from request import RequestHeader, RequestOp
from servermanager import ServerManager, ClientThread
import logging


class FileManager:
    DATABASE = "database.db"
    UUID_SIZE = 16
    DEFAULT_CLIENT_VERSION = 0
    USERNAME_LEN = 1
    CLIENT_VERSION_LEN = 1
    REQUEST_TYPE_LEN = 1
    PUBLIC_KEY_LEN = 127
    FILENAME_LEN = 1

    def __init__(self, server_port: int):
        self._database = Database(FileManager.DATABASE)
        self._server = ServerManager(server_port=server_port, connection_handle=self._connection_handle)
        self._memory_storage = MemoryStorage()

    def _parse_request(self, client_thread: ClientThread) -> RequestHeader:
        logging.info("A client has connected.")
        data = client_thread.recv(FileManager.UUID_SIZE)
        client_uuid_raw0, client_uuid_raw1 = struct.unpack('<QQ', data)
        client_uuid_raw = (client_uuid_raw0 << 64) | client_uuid_raw1
        try:
            client_uuid = UUID(client_uuid_raw)
        except ValueError:
            logging.error(f"Invalid client UUID: {client_uuid_raw}")
            return RequestHeader(UUID(int=0), FileManager.DEFAULT_CLIENT_VERSION, RequestOp.UNKNOWN)
        data = client_thread.recv(FileManager.CLIENT_VERSION_LEN)
        client_version = struct.unpack('<B', data)[0]
        data = client_thread.recv(FileManager.REQUEST_TYPE_LEN)
        request_code = struct.unpack('<B', data)[0]
        try:
            request_type = RequestOp(request_code)
        except ValueError:
            logging.error(f"Unknown request code:{request_code}")
            return RequestHeader(client_uuid, client_version, RequestOp.UNKNOWN)
        logging.info(f"new request of type {request_type.name}")
        match request_type:
            case RequestOp.REQUEST_REGISTRATION:
                username_len = int.from_bytes(client_thread.recv(FileManager.USERNAME_LEN),
                                              byteorder='big', signed=False)
                username = client_thread.recv(username_len)
                return RequestHeader.handle_registration_request(client_uuid, client_version, username)
            case RequestOp.REQUEST_PUBLIC_KEY:
                public_key = client_thread.recv(FileManager.PUBLIC_KEY_LEN)
                return RequestHeader.exchange_keys(client_uuid, client_version, public_key)
            case RequestOp.UPLOAD_FILE:
                filename_len = int(client_thread.recv(FileManager.FILENAME_LEN))
                filename = client_thread.recv(filename_len)
                return RequestHeader.upload_file(client_uuid, client_version, filename)
            case RequestOp.CRC_EQUAL:
                return RequestHeader.crc_ok(client_uuid, client_version)

    def _handle_registration(self, request: RequestHeader):
        username = request.payload.decode()
        if self._memory_storage.user_is_exist(username):
            logging.error(f"Cannot register this user {username} with uuid {request.clientID} "
                          f"because he is already registered")
            return
        logging.info(f"Register new user {username}:{request.clientID}")
        self._memory_storage.add_user_to_memory(username=username,client_uuid=request.clientID)
        if not self._database.client_username_exists(username=username):
            client = Client(cid=request.clientID, cname=username, public_key=None, last_seen=str(datetime.now()))
            self._database.storeClient(clnt=client)
            logging.info("Registered new Client to DB")
        return

    def _handle_request_key(self, request: RequestHeader):
        pass

    def _handle_upload_file(self, request):
        pass

    def _handle_crc_equal(self, request):
        pass

    def _connection_handle(self, client_thread: ClientThread):
        request = self._parse_request(client_thread)
        match request.request_type:
            case RequestOp.REQUEST_REGISTRATION:
                self._handle_registration(request)
            case RequestOp.REQUEST_PUBLIC_KEY:
                self._handle_request_key(request)
            case RequestOp.UPLOAD_FILE:
                self._handle_upload_file(request)
            case RequestOp.CRC_EQUAL:
                self._handle_crc_equal(request)