"""
MessageU Server
Python 3.9.13
main.py: Entry point of the Server.
"""

import utils
import servermanager
PORT_INFO = 'port.info'


def get_port_info() -> int:
    """
    Parses PORT_INFO into TCP port
    :return: int, containing TCP port of file server
    """
    try:
        with open(PORT_INFO, 'r') as fd:
            return int(fd.read())
    except FileNotFoundError:
        return 1234


if __name__ == '__main__':
    port = get_port_info()
    if port is None:
        utils.stopServer(f"Failed to parse int port from '{PORT_INFO}")

    server.ServerManager(server_port=port, host="").start()
