#pragma once
#include <string>
#include <cstdint>
#include <ostream>
#include <boost/asio/ip/tcp.hpp>

using boost::asio::ip::tcp;
using boost::asio::io_context;

constexpr size_t PACKET_SIZE = 1024;   // Better be the same on server side.

class NetworkManager
{
public:
    NetworkManager();
    virtual ~NetworkManager();

    // do not allow
    NetworkManager(const NetworkManager& other)                = delete;
    NetworkManager(NetworkManager&& other) noexcept            = delete;
    NetworkManager& operator=(const NetworkManager& other)     = delete;
    NetworkManager& operator=(NetworkManager&& other) noexcept = delete;

    friend std::ostream& operator<<(std::ostream& os, const NetworkManager* socket) {
        if (socket != nullptr)
            os << socket->_address << ':' << socket->_port;
        return os;
    }
    friend std::ostream& operator<<(std::ostream& os, const NetworkManager& socket) {
        return operator<<(os, &socket);
    }

    // validations
    static bool isValidAddress(const std::string& address);
    static bool isValidPort(const std::string& port);

    // logic
    bool setSocketInfo(const std::string& address, const std::string& port);
    bool connect();
    void close();
    bool receive(uint8_t* const buffer, const size_t size) const;
    bool send(const uint8_t* const buffer, const size_t size) const;
    bool sendReceive(const uint8_t* const toSend, const size_t size, uint8_t* const response, const size_t resSize);


private:
    std::string    _address;
    std::string    _port;
    io_context*    _ioContext;
    tcp::resolver* _resolver;
    tcp::socket*   _socket;
    bool           _bigEndian;
    bool           _connected;  // indicates that socket has been open and connected.

    void swapBytes(uint8_t* const buffer, size_t size) const;

};