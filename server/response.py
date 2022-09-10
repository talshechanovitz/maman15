import struct
from enum import Enum
from typing import Optional
from uuid import UUID
max_int64 = 0xFFFFFFFFFFFFFFFF


class ResponseOp(Enum):
    SUCCESSFUL_REGISTRATION = 100
    EXCHANGE_KEYS = 101
    USER_ALREADY_EXIST = 102
    UPLOAD_FILE = 105
    CRC_EQUAL = 103
    RESPONSE_ERROR = 104
    File_IS_ALREADY_EXIST = 106


class Response:
    def __init__(self, server_version: int, response_status: ResponseOp, payload: Optional[bytes] = b''):
        self._server_version = server_version
        self._response_status = response_status
        self._payload = payload

    def to_buffer(self) -> bytes:
        buffer = struct.pack('<B', self._server_version)
        buffer += struct.pack('<B', self._response_status.value)
        buffer += self._payload
        return buffer

    @classmethod
    def register_success(cls, server_version: int, uuid: UUID):
        uuid = struct.pack('<QQ', (uuid.int >> 64) & max_int64, uuid.int & max_int64)
        return Response(server_version, ResponseOp.SUCCESSFUL_REGISTRATION, uuid)

    @classmethod
    def user_already_exists(cls, server_version: int):
        return Response(server_version, ResponseOp.USER_ALREADY_EXIST)

    @classmethod
    def exchange_keypair(cls, server_version: int, aes_key: bytes):
        print(len(aes_key))
        return Response(server_version, ResponseOp.EXCHANGE_KEYS, aes_key)

    @classmethod
    def verify_file_crc(cls, server_version: int, crc: int):
        crc = struct.pack('<I', crc)
        return Response(server_version, ResponseOp.CRC_EQUAL, crc)

    @classmethod
    def general_error(cls, server_version: int):
        return Response(server_version, ResponseOp.RESPONSE_ERROR)

    @classmethod
    def general_success(cls, server_version: int):
        return Response(server_version, ResponseOp.RESPONSE_ERROR)

    def response_status(self) -> ResponseOp:
        return self._response_status

    def server_version(self) -> int:
        return self._server_version

    def payload(self) -> bytes:
        return self._payload
