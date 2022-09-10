import sqlite3
from datetime import datetime
from sqlite3 import Error
import string
from uuid import UUID


class Client:
    """ Represents a client entry """

    def __init__(self, cid: UUID, cname, public_key, last_seen, aes_key):
        self.ID = cid.bytes  # Unique client ID, 16 bytes.
        self.Name = cname  # Client's name, null terminated ascii string, 255 bytes.
        self.PublicKey = public_key  # Client's public key, 160 bytes.
        self.last_seen = last_seen
        self.aes_key = aes_key
        # The Date & time of client's last request.


class File:
    """
    Represents a File entry
    """
    def __init__(self, cid: UUID, file_name: string, path_name: string, verified: bool):
        self.id = cid.bytes  # Unique client ID, 16 bytes.
        self.file_name = file_name
        self.path_name = path_name
        self.verified = verified


class Database:
    CLIENTS = "clients"
    FILES = "files"

    def __init__(self, name):
        self._name = name

    def initialize(self):
        # create clients table
        self.executescript(f""" CREATE TABLE {Database.CLIENTS}(
              ID BLOB(16) NOT NULL PRIMARY KEY,
              Name CHAR(127),
              PublicKey BLOB(162),
              LastSeen DATE,
              KeyAES BLOB(16) 
            );
            """)
        # Try to create Files table
        self.executescript(f"""
                   CREATE TABLE {Database.FILES}(
                     ID BLOB(16) PRIMARY KEY,
                     FileName CHAR(255) NOT NULL,
                     FilePath CHAR(255) NOT NULL,
                     Verified BOOLEAN NOT NULL CHECK (Verified IN (0, 1)
                   );
                   """)

    def create_connection(self):
        """ create a database connection to a SQLite database """
        conn = None
        try:
            conn = sqlite3.connect(self._name)
        except Error as e:
            print(e)
        return conn

    def executescript(self, script):
        conn = self.create_connection()
        try:
            conn.executescript(script)
            conn.commit()
        except:
            pass  # table might exist already
        conn.close()

    def execute(self, query, args, commit=False):
        conn = self.create_connection()
        results = None
        try:
            cur = conn.cursor()
            cur.execute(query, args)
            if commit:
                conn.commit()
                results = True
            else:
                results = cur.fetchall()
        except Exception as e:
            print(f"failed execute query {e}")
        conn.close()
        return results

    def client_username_exists(self, username):
        """ Check whether a username already exists within database """
        results = self.execute(f"SELECT * FROM {Database.CLIENTS} WHERE Name = ?", [username])
        if not results:
            return False
        return len(results) > 0

    def store_client(self, clnt: Client):
        """ Store a client into database """
        return self.execute(f"INSERT INTO {Database.CLIENTS} VALUES (?, ?, ?, ?, ?)",
                            [clnt.ID, clnt.Name, clnt.PublicKey, clnt.last_seen, clnt.aes_key], True)

    def store_public_key(self, client_id: UUID, public_key, aes_key):
        return self.execute(f"Update {Database.CLIENTS} set PublicKey = ?, KeyAES = ?, LastSeen = ? where id = ?",
                            [public_key, aes_key, datetime.now(), client_id.bytes], True)

    def find_public_key_by_id(self, client_id):
        return self.execute(f"select PublicKey from {Database.CLIENTS} where id = ?", [client_id])

    def find_aes_key(self, client_id):
        return self.execute(f"select KeyAES from {Database.CLIENTS} where id = ?", [client_id])

    def store_file(self, file: File):
        """ Store a client into database """
        return self.execute(f"INSERT INTO {Database.FILES} VALUES (?, ?, ?, ?)",
                            [file.id, file.file_name, file.path_name, file.verified], True)

    def client_id_exists(self, client_id) -> bool:
        """ Check whether an client ID already exists within database """
        results = self.execute(f"SELECT * FROM {Database.CLIENTS} WHERE ID = ?", [client_id])
        if not results:
            return False
        return len(results) > 0

    def update_memory_status(self):
        return self.execute(f"SELECT ID, Name FROM {Database.CLIENTS}", [])

