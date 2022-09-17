#pragma once
#include "protocol.h"
#include "NetworkManager.h"
#include "RSAWrapper.h"
#include "Base64Wrapper.h"
#include "FileHandler.h"
#include <vector>
#include "AESWrapper.h"

constexpr auto CLIENT_INFO = "me.info";
constexpr auto SERVER_INFO = "server.info";

class NetworkManager;

struct SClient {
	ClientID id;
    std::string file_name;
	std::string username;
	std::string pkey;
    bool pkeySet = false;
	SymmKey symmKey;
    uint32_t crc;
	bool symmKeySet = false;
	
	friend std::ostream& operator<<(std::ostream& os, const SClient& c)
	{
		os << "ClientID: " << c.id.uuid << std::endl;
		os << "Username: " << c.username << std::endl;
		return os;
	}
};
struct SMessage {
	std::string username;
	std::string content;
};

class Client {
private:
	SClient _self;
	RSAPrivateWrapper* _rsaDecryptor;
    AESWrapper* _aesKey;

public:
	NetworkManager* _sock;
	Client();
	~Client();
	bool validateHeader(const ResponseHeader&, const EnumResponseCode);
	bool registerClient(const std::string&);
	bool registerPublicKey();
	bool setPublicKey();
    bool UploadFile(const std::string&);
    bool CrcEqual();

};