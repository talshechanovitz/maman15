import string
from uuid import UUID


class MemoryStorage:
    def __init__(self):
        self._storage_on_memory = {}

    def add_user_to_memory(self, username: string, client_uuid: UUID):
        self._storage_on_memory[username] = client_uuid

    def user_is_exist(self, username: string) -> bool:
        if username in self._storage_on_memory:
            return True
        return False
