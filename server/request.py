import logging
from enum import Enum
from uuid import UUID


class RequestOp(Enum):
    """
    File server operation types
    """
    REQUEST_REGISTRATION = 203
    REQUEST_PUBLIC_KEY = 204
    UPLOAD_FILE = 201
    UNKNOWN = 205
    CRC_EQUAL = 202


# region constants
USER_ID_MIN = 0
USER_ID_MAX = 0xffffffff
NAME_LEN_MIN = 1
NAME_LEN_MAX = 0xffff
PAYLOAD_SIZE_MIN = 0
PAYLOAD_SIZE_MAX = 0xffffffff
STREAM_BUFFER = 4096

# endregion


class RequestHeader:
    """
    File server request object, can store and encode request items
    """

    def __init__(self, client_uuid: UUID, client_version, request_type, payload=b''):
        self.payload = payload  # 4 bytes
        self.clientID = client_uuid
        self.version = client_version  # 1 byte
        self.request_type = request_type

    @classmethod
    def handle_registration_request(cls, client_uuid, client_version, username):
        return RequestHeader(client_uuid=client_uuid, client_version=client_version,
                             request_type=RequestOp.REQUEST_REGISTRATION, payload=username)

    @classmethod
    def exchange_keys(cls, client_uuid, client_version, public_key):
        return RequestHeader(client_uuid=client_uuid, client_version=client_version,
                             request_type=RequestOp.REQUEST_PUBLIC_KEY, payload=public_key)

    @classmethod
    def upload_file(cls, client_uuid, client_version, file_name):
        return RequestHeader(client_uuid=client_uuid, client_version=client_version,
                             request_type=RequestOp.UPLOAD_FILE, payload=file_name)

    @classmethod
    def crc_ok(cls, client_uuid, client_version):
        return RequestHeader(client_uuid=client_uuid, client_version=client_version, request_type=RequestOp.CRC_EQUAL)
