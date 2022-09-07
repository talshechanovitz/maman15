import sqlite3
from sqlite3 import Error


class Client:
    """ Represents a client entry """

    def __init__(self, cid, cname, public_key, last_seen):
        self.ID = bytes.fromhex(cid)  # Unique client ID, 16 bytes.
        self.Name = cname  # Client's name, null terminated ascii string, 255 bytes.
        self.PublicKey = public_key  # Client's public key, 160 bytes.
        self.LastSeen = last_seen  # The Date & time of client's last request.


class Database:
    CLIENTS = "clients"
    FILES = "files"

    def __init__(self, name):
        self._name = name

    def initialize(self):
        # create clients table
        self.executescript(f""" CREATE TABLE {Database.CLIENTS}(
              ID CHAR(16) NOT NULL PRIMARY KEY,
              Name CHAR(127) NOT NULL,
              PublicKey CHAR(160) NOT NULL,
              LastSeen DATE,
              keyAES CHAR(256) 
            );
            """)
        # Try to create Files table
        self.executescript(f"""
                   CREATE TABLE {Database.FILES}(
                     ID INTEGER PRIMARY KEY,
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

    def storeClient(self, clnt: Client):
        """ Store a client into database """
        return self.execute(f"INSERT INTO {Database.CLIENTS} VALUES (?, ?, ?, ?)",
                            [clnt.ID, clnt.Name, clnt.PublicKey, clnt.LastSeen], True)

    def client_id_exists(self, client_id) -> bool:
        """ Check whether an client ID already exists within database """
        results = self.execute(f"SELECT * FROM {Database.CLIENTS} WHERE ID = ?", [client_id])
        if not results:
            return False
        return len(results) > 0

