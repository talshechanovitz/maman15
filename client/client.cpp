#include "client.h"
#include <cstring>
#include <fstream>
#include <string>
#include <boost/crc.hpp>
#include <filesystem>
#include <zlib.h>
Client::Client()

{
	_sock = new NetworkManager();
	_rsaDecryptor = new RSAPrivateWrapper();
}
//Client::~Client()
//{
//    delete _fileHandler;
//    delete _sock;
//    delete _rsaDecryptor;
//}
Client::~Client()
{
	delete _sock;
}

bool Client::validateHeader(const ResponseHeader& header, const EnumResponseCode expected)
{
	if (header.opcode == RESPONSE_ERROR) {
		std::cerr << "Got error from opcode" << std::endl;
	}
	if (header.opcode != expected) {
		std::cerr << "Unexpected opcode" << std::endl;
	}
	fsize expectedSize = INIT_VAL;
	switch (header.opcode) {
		case RESPONSE_REG: {
			expectedSize = sizeof(ResponseReg) - sizeof(ResponseHeader);
			break;
		}
		case EXCHANGE_KEYS: {
			expectedSize = sizeof(ResponseSymmKey) - sizeof(ResponseHeader);
			break;
		}
		// TODO: add CRC and uploadFile
	}
	if (header.payloadSize != expectedSize) {
		std::cerr << "Unexpected payload size " << header.payloadSize << ".Expected was " << expectedSize << std::endl;
		return false;
	}
	return true;
}

bool Client::registerClient(const std::string& username)
{
	RequestReg requestReg;
	ResponseReg responseReg;

	// Check length of username
	if (username.length() >= CLIENT_NAME_SIZE) {
		std::cerr << "Invalid username length" << std::endl;
		return false;
	}

	//check if its only alphanumeric
	for (auto ch : username) {
		if (!std::isalnum(ch)) {
			std::cerr << "Invalid username, Username must contains letters and numbers only" << std::endl;
		}
	}
	//TODO: RSA?

	// Create request data
	requestReg.header.payloadSize = sizeof(requestReg.payload);
    strcpy(reinterpret_cast<char*>(requestReg.payload.clientName.name),username.c_str());
	//TODO: if pkey is added, we should also copy the key here.

	//send the data and receive response
    if (!_sock->sendReceive(reinterpret_cast<const uint8_t* const>(&requestReg), sizeof(requestReg),
                                     reinterpret_cast<uint8_t* const>(&responseReg), sizeof(responseReg)))
    {
        std::cerr << "Failed communicating with server on " << _sock;
        return false;
    }
	//checking the header
	if (!validateHeader(responseReg.header, RESPONSE_REG))
		return false;
	//setting the Client object
	_self.id = responseReg.payload;
	_self.username = username;
	std::cout << _self << std::endl;
	return true;
}
bool Client::UploadFile(const std::string& file_path) {
    std::string base_filename = file_path.substr(file_path.find_last_of("/\\") + 1);
    ResponseUploadedFile crcFile;
    RequestUploadFile uploadFile(_self.id);
    uploadFile.payload.fm.file_name_len = base_filename.length();
    strcpy(reinterpret_cast<char*>(&uploadFile.payload.fm.fileName),base_filename.c_str());
    uploadFile.payload.fn.file_size = std::filesystem::file_size(file_path);
    std::ifstream fin(file_path, std::ifstream::binary);
    std::vector<char> buffer (1024,0); //reads only the first 1024 bytes
    boost::crc_32_type result;

    while(!fin.eof()) {
       fin.read(buffer.data(), buffer.size());
          result.process_bytes(buffer.data(),fin.gcount());
        std::string ciphertext;
        ciphertext = _aesKey->encrypt(buffer.data(), sizeof(buffer.data()));
        strcpy(reinterpret_cast<char*>(&uploadFile.payload.fn.file_content),ciphertext.c_str());
        if (!_sock->sendReceive(reinterpret_cast<const uint8_t* const>(&uploadFile), sizeof(uploadFile),
                                reinterpret_cast<uint8_t* const>(&crcFile), sizeof(crcFile)))
        {
            std::cerr << "Failed communicating with server on " << _sock;
            return false;
        }
    }
    uint16_t client_crc = crcFile.payload;
    if(crcFile.payload != client_crc) {
        return false;
    }
    _self.file_name = base_filename;
    return true;
}

bool Client::registerPublicKey() {
    RequestPublicKey requestPKey(_self.id);
    ResponseSymmKey responseRegPKey;

    if (!_self.pkeySet) {
        if (!setPublicKey()) {
            std::cerr << "Failed to set public key" << std::endl;
            return false;
        }
    }
    //copy the pkey to buffer before sending it
    int i;
    for (i = 0; i < sizeof(requestPKey.payload.publicKey); i++) {
        requestPKey.payload.publicKey[i] = this->_self.pkey[i];
    }
    if (!_sock->sendReceive(reinterpret_cast<const uint8_t *const>(&requestPKey), sizeof(requestPKey),
                            reinterpret_cast<uint8_t *const>(&responseRegPKey), sizeof(responseRegPKey)))

        //checking the header
        if (!validateHeader(responseRegPKey.header, EXCHANGE_KEYS))
            return false;

    std::string decrypted_aes_key = _rsaDecryptor->decrypt(responseRegPKey.symmKey.symmKey, ENCRYPTED_DATA);
    _self.symmKeySet = true;
    _aesKey = new AESWrapper(decrypted_aes_key.c_str(),decrypted_aes_key.size());
    return true;
}

bool Client::setPublicKey()
{
	// 1. get the public key
	std::string pubkey = _rsaDecryptor->getPublicKey();
	if (pubkey.size() != PUBLIC_KEY_SIZE)
	{
		std::cerr << "Invalid public key length!" << std::endl;
		return false;
	}
	this->_self.pkey = pubkey;
	this->_self.pkeySet = true;

	return true;
}

bool Client::CrcEqual() {
    RequestCrc requestCrc;
    ResponseCrc responseCrc;
    requestCrc.header.clientId = _self.id;
    requestCrc.payload.fm.file_name_len = _self.file_name.length();
    strcpy(reinterpret_cast<char*>(&requestCrc.payload.fm.fileName),_self.file_name.c_str());
    if (!_sock->sendReceive(reinterpret_cast<const uint8_t* const>(&requestCrc), sizeof(requestCrc),
                            reinterpret_cast<uint8_t* const>(&responseCrc), sizeof(responseCrc)))
    {
        std::cerr << "Failed communicating with server on " << _sock;
        return false;
    }
    return true;
}
