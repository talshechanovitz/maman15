#pragma once
#include <cstdint>
#include <iostream>
#include <ostream>

enum { INIT_VAL = 1};

//Common types
typedef uint16_t opcode_t;
typedef uint8_t fsize;
typedef uint8_t serverver_t;
typedef uint16_t file_crc;



// Constants, all sizes are in bytes
// Constants. All sizes are in BYTES.
constexpr serverver_t CLIENT_VERSION = 2;
constexpr size_t CLIENT_ID_SIZE = 16;
constexpr size_t CLIENT_NAME_SIZE = 127;
constexpr size_t PUBLIC_KEY_SIZE = 160;
constexpr size_t SYMMETRIC_KEY_SIZE = 16;
constexpr size_t ENCRYPTED_DATA = 128;
constexpr  size_t FILE_METADATA = 50;
constexpr size_t PACKET_CONTENT = 1024;
constexpr size_t IV_SIZE = 16;

enum EnumRequestCode {
    REQUEST_REGISTRATION = 203,
    REQUEST_PUBLIC_KEY = 204,
    REQUEST_UPLOAD_FILE = 201,
    UNKNOWN = 205,
    CRC_EQUAL = 202,
};

enum EnumResponseCode {
    RESPONSE_REG = 100,
    EXCHANGE_KEYS = 101,
    USER_ALREADY_EXIST = 102,
//    UPLOAD_FILE = 105,
//    CRC_EQUAL = 103,
    RESPONSE_ERROR = 104
//    File_IS_ALREADY_EXIST = 106
};


enum EnumMessageType {
    MSG_SYMM_KEY_REQ = 1,
    MSG_SYMM_KEY_SEND = 2,
    MSG_FILE = 3,
};

#pragma pack(push, 1)
struct ClientID {
    char uuid[CLIENT_ID_SIZE];
    ClientID() : uuid{ 0 } {}
    friend std::ostream& operator<<(std::ostream& os, const ClientID& c)
    {
        os << c.uuid << std::endl;
        return os;
    }
};
struct ClientName {
    char name[CLIENT_NAME_SIZE];
    ClientName() : name{ '\0' } {}
    friend std::ostream& operator<<(std::ostream& os, const ClientName& c)
    {
        os << c.name << std::endl;
        return os;
    }
};

struct PublicKey {
    char publicKey[PUBLIC_KEY_SIZE];
    PublicKey(): publicKey{ 0 }{}
    friend std::ostream& operator<<(std::ostream& os, const PublicKey& c)
    {
        os << c.publicKey << std::endl;
        return os;
    }
};

struct SymmKey {
    char symmKey[SYMMETRIC_KEY_SIZE];
    SymmKey() : symmKey{INIT_VAL}{}
    friend std::ostream& operator<<(std::ostream& os, const SymmKey& c)
    {
        os << c.symmKey << std::endl;
        return os;
    }
};

struct EncryptedSymm {
    char symmKey[ENCRYPTED_DATA];
    EncryptedSymm() : symmKey{ INIT_VAL } {}
    friend std::ostream& operator<<(std::ostream& os, const EncryptedSymm& c)
    {
        os << c.symmKey << std::endl;
        return os;
    }
};

struct RequestHeader
{
    ClientID       clientId;
    const serverver_t version;
    const opcode_t    code;
    fsize         payloadSize;
    RequestHeader(const opcode_t reqCode) : version(CLIENT_VERSION), code(reqCode), payloadSize(INIT_VAL) {}
    RequestHeader(const ClientID& id, const opcode_t reqCode) : clientId(id), version(CLIENT_VERSION),
    code(reqCode), payloadSize(2) {}
};

struct ResponseHeader {
    const serverver_t version;
    const opcode_t opcode;
    fsize payloadSize;
    ResponseHeader() : version(INIT_VAL), opcode(INIT_VAL), payloadSize(INIT_VAL){}
};

struct RequestReg
{
    RequestHeader header;
    struct
    {
        ClientName clientName;
    }payload;
    RequestReg() : header(REQUEST_REGISTRATION) {}
};

struct ResponseReg
{
    ResponseHeader header;
    ClientID payload;
};

struct RequestPublicKey {
    RequestHeader header;
    PublicKey payload;
    RequestPublicKey(const ClientID& id) : header(id, REQUEST_PUBLIC_KEY){}
};

struct FileMetaData
{
    uint8_t file_name_len;
    char fileName[FILE_METADATA];
    FileMetaData() : file_name_len(INIT_VAL), fileName{INIT_VAL}{}
};
struct FileContent
{
    uint16_t file_size;
    char file_content[PACKET_CONTENT]{0};
    FileContent() : file_size(INIT_VAL), file_content{INIT_VAL}{}
};
struct RequestUploadFile
{
    RequestHeader header;
    struct
    {
         FileMetaData   fm;
         char iv[IV_SIZE]{0};
        FileContent    fn;
    }payload;
    RequestUploadFile(const ClientID& id) : header(id, REQUEST_UPLOAD_FILE){}
};
struct ResponseUploadedFile
{
    ResponseHeader header;
    uint16_t payload;
};
//response of Request Public key, server sends AES key
struct ResponseSymmKey
{
    ResponseHeader header;
    EncryptedSymm symmKey;
};


struct RequestCrc
{
    RequestHeader header;
    struct
    {
        FileMetaData   fm;
    }payload;    RequestCrc() : header(CRC_EQUAL) {}
};

struct ResponseCrc
{
    ResponseHeader header;
    uint8_t payload;
};

#pragma pack(pop)
