import database
from servermanager import ServerManager, ClientThread
from request import RequestHeader
import logging


class FileManager:
    DATABASE = "database.db"
    PACKET_SIZE = 16

    def __init__(self, server_port: int):
        self.database = database.Database(FileManager.DATABASE)
        self._server = ServerManager(server_port=server_port, connection_handle=self._connection_handle)

    def _parse_request(self, client_thread: ClientThread) -> RequestHeader:
        logging.info("A client has connected.")
        data = client_thread.recv(FileManager.PACKET_SIZE)
        if data:
            requestHeader = protocol.RequestHeader()
            success = False
            if not requestHeader.unpack(data):
                logging.error("Failed to parse request header!")
            else:
                if requestHeader.code in self.requestHandle.keys():
                    success = self.requestHandle[requestHeader.code](conn, data)  # invoke corresponding handle.
            if not success:  # return generic error upon failure.
                responseHeader = protocol.ResponseHeader(protocol.EResponseCode.RESPONSE_ERROR.value)
                self.write(conn, responseHeader.pack())
            self.database.setLastSeen(requestHeader.clientID, str(datetime.now()))
        self.sel.unregister(conn)
        conn.close()
    def _connection_handle(self, client_thread: ClientThread):
        request  = self._parse_request(client_thread)
        return null