from enum import Enum
from typing import Optional


class RequestOp(Enum):
    """
    File server operation types
    """
    REQUEST_REGISTRATION = 1000  # uuid ignored.
    REQUEST_PUBLIC_KEY = 1002
    SAVE_FILE = 100
    GET_FILE = 200
    DELETE_FILE = 201
    GET_DIRLIST = 202


# region constants
USER_ID_MIN = 0
USER_ID_MAX = 0xffffffff
NAME_LEN_MIN = 1
NAME_LEN_MAX = 0xffff
PAYLOAD_SIZE_MIN = 0
PAYLOAD_SIZE_MAX = 0xffffffff


# endregion


class RequestHeader:
    """
    File server request object, can store and encode request items
    """

    def __init__(self, user_id: int, version: int, op: RequestOp, filename: Optional[str] = '',
                 payload: Optional[bytes] = b''):
        self._user_id = user_id
        self._version = version
        self._op = op
        self._filename = filename
        self._payload = payload
