import string
from uuid import UUID


class MemoryStorage:
    def __init__(self):
        self._storage_on_memory = {}

    def add_user_to_memory(self, username: string, client_uuid: UUID):
        self._storage_on_memory[username] = client_uuid

    def update_memory(self, clients_data):
        if len(clients_data) > 0:
            self.parse_clients_data(clients_data)

    def parse_clients_data(self, clients_data: list):
        for data_client in clients_data:
            self._storage_on_memory[data_client[0]] = data_client[1]

    def user_is_exist(self, username: string) -> bool:
        if username in self._storage_on_memory.values():
            return True
        return False
