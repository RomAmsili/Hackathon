import socket
from socket import *
from scapy.all import *
import time
import struct
import random


class Server:
    def __init__(self):
        self.server_ip = get_if_addr(conf.iface)
        self.server_UDP_port = 2110
        self.server_socket_udp = None

    def story_line(self):
        self.initial_udp()

    def initial_udp(self):
        massage = struct.pack('Ibh', 0xabcddcba, 0x2, self.server_UDP_port)
        massage = str.encode("Oryan the king")
        self.server_socket_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        # self.server_socket_udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket_udp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.server_socket_udp.bind(('',50005))
        print("Server started, listening on IP address 172.1.0.4")
        while True:
            self.server_socket_udp.sendto(massage, ("255.255.255.255", 13117))
            time.sleep(1)








server = Server()
server.initial_udp()

# print(get_if_addr("eth1"))
