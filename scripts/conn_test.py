import socket
import struct

SRV_IP = '100.125.0.30'
SRV_PORT = 8005
SRV_ADDR = (SRV_IP, SRV_PORT)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(SRV_ADDR)

client.sendall(b'PING')
response = client.recv(1024)
print(response)

client.close()
