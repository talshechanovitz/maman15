#define WIN32_LEAN_AND_MEAN

#include <iostream>
#include "client.h"
#include <string>
#include <fstream>
#include <string>
using namespace std;
// Need to link with Ws2_32.lib, Mswsock.lib, and Advapi32.lib
#pragma comment (lib, "Ws2_32.lib")


#define DEFAULT_BUFLEN 1024
#define DEFAULT_PORT 1234

int main() {
	std::string ipAddress = "127.0.0.1";
	Client* newClient = new Client();
	newClient->_sock->setSocketInfo(ipAddress, "1234");
    newClient->_sock->connect();
	newClient->registerClient("Testingthispp");
	newClient->registerPublicKey();
    bool crc_equal = newClient->UploadFile("/Users/Ofekatriel/tal_read.txt");
    if(crc_equal)
    {
        newClient->CrcEqual();
    }
	return 0;
}