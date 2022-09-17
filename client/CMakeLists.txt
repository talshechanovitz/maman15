cmake_minimum_required(VERSION 3.23)
project(Client)

set(CMAKE_CXX_STANDARD 17)

include_directories(.)

add_executable(Client AESWrapper.cpp Base64Wrapper.cpp client.cpp FileHandler.cpp main.cpp NetworkManager.cpp RSAWrapper.cpp)
# Set Boost library
set(BOOST_ROOT "/usr/local/Cellar/boost/1.79.0_2")
set(BOOST_INCLUDE_DIR "/usr/local/Cellar/boost/1.79.0_2/include")
set(BOOST_LIBRARY_DIR "/usr/local/Cellar/boost/1.79.0_2/lib")
find_package(Boost 1.79.0)
include_directories(${BOOST_INCLUDE_DIR})
target_link_libraries(Client ${BOOST_LIBRARY_DIR}/libboost_filesystem.a)


set(CRYPTOPP_INCLUDE_DIR "/Users/Ofekatriel/maman15/Client/cryptopp870")
set(CRYPTOPP_INCLUDE_DIR "/Users/Ofekatriel/maman15/Client/cryptopp870")
include_directories(${CRYPTOPP_INCLUDE_DIR})
target_link_libraries(Client ${CRYPTOPP_INCLUDE_DIR}/libcryptopp.a)


set(CRYPTOPP_INCLUDE_DIR "/Users/Ofekatriel/Downloads/zip-master")
set(CRYPTOPP_INCLUDE_DIR "/Users/Ofekatriel/Downloads/zip-master")
include_directories(${CRYPTOPP_INCLUDE_DIR})



set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR})

