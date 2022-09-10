from uuid import UUID
import struct
import socket
from socket import socket as sock

from Crypto.Cipher import AES, PKCS1_OAEP

from server.request import RequestOp
from Crypto.PublicKey import RSA

from zlib import crc32

max_int64 = 0xFFFFFFFFFFFFFFFF
client_uuid = UUID(int=0)
client_uuid_bytes = struct.pack('<QQ', (client_uuid.int >> 64) & max_int64, client_uuid.int & max_int64)
client_version = struct.pack('<B', 3)
request_type = struct.pack('<B', RequestOp.REQUEST_REGISTRATION.value)

username = b'another 71'


def uuid_to_buffer(uuid: UUID) -> bytes:
    return struct.pack('<QQ', (uuid.int >> 64) & max_int64,
                       uuid.int & max_int64)


def encrypt(data, key):
    bs = AES.block_size
    finished = False
    curr_ptr = 0
    enc_data = b''
    cipher = AES.new(key, AES.MODE_CBC)
    while not finished:

        chunk = data[curr_ptr:curr_ptr + 4096]
        if len(chunk) == 0 or len(chunk) % bs != 0:  # final block/chunk is padded before encryption
            padding_length = (bs - len(chunk) % bs) or bs
            print(f'Padding with {padding_length} bytes')
            chunk += str.encode(padding_length * chr(padding_length))
            finished = True
        enc_chunk = cipher.encrypt(chunk)
        enc_data += enc_chunk
        curr_ptr += len(chunk)
    return cipher.iv, enc_data


buffer = client_uuid_bytes + client_version + request_type + len(username).to_bytes(1, byteorder='big') + username

s = sock(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('127.0.0.1', 1234))
s.sendall(buffer)

buffer = b''
while True:
    data = s.recv(1024)
    if not data:
        break
    buffer += data
s.close()
print(buffer)

a, b = struct.unpack('<QQ', buffer[2:])
client_uuid_bytes = UUID(int=((a << 64) | b))
print(f'uuid = {client_uuid_bytes}')

key = RSA.generate(1024)

request_type = struct.pack('<B', RequestOp.REQUEST_PUBLIC_KEY.value)
buffer = uuid_to_buffer(client_uuid_bytes) + client_version + request_type + key.public_key().export_key(format='DER')

s = sock(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('127.0.0.1', 1234))
s.sendall(buffer)

buffer = b''
while True:
    data = s.recv(1024)
    if not data:
        break
    buffer += data
s.close()
print(buffer)

aes_key_enc = buffer[2:]
cipher_rsa = PKCS1_OAEP.new(key)
aes_key = cipher_rsa.decrypt(aes_key_enc)
print(f'{aes_key=}')

request_type = struct.pack('<B', RequestOp.UPLOAD_FILE.value)
file_name = 'cool_file.txt'
filename_len = struct.pack('<B', len(file_name))
with open(file_name, 'rb') as fd:
    data = fd.read()
crc = crc32(data)
print(f"crc_client:{crc}")
iv, ciphertext = encrypt(data, aes_key)
print(f'{iv=}')

print(f'Data size = {len(data)}')
print(f'Ciphertext size = {len(ciphertext)}')
file_size = struct.pack('<I', len(ciphertext))

buffer = uuid_to_buffer(client_uuid_bytes) + client_version + request_type + \
         filename_len + file_name.encode() + iv + file_size + ciphertext

s = sock(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('127.0.0.1', 1234))
s.sendall(buffer)

buffer = b''
while True:
    data = s.recv(1024)
    if not data:
        break
    buffer += data
s.close()
print(buffer)

server_crc = struct.unpack('<I', buffer[2:])[0]

print(f'client crc = {crc}')
print(f'server crc = {server_crc}')
print(f'crc match = {crc == server_crc}')


if crc == server_crc:
    print(f'Sending CRC OK request')
    request_type = struct.pack('<B', RequestOp.CRC_EQUAL.value)
    buffer = uuid_to_buffer(client_uuid_bytes) + client_version + request_type + filename_len + file_name.encode()
    s = sock(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('127.0.0.1', 1234))
    s.sendall(buffer)

    buffer = b''
    while True:
        data = s.recv(1024)
        if not data:
            break
        buffer += data
    s.close()
    print(buffer)