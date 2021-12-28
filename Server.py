import socket
from socket import *
from scapy.all import *
import time
import struct
import random


class Server:
    def __init__(self):
        self.server_ip = get_if_addr("eth1")
        print("MY IP:",self.server_ip)
        self.server_port = 2076
        self.server_socket_udp = None
        self.server_socket_tcp = None
        self.clients_sockets_dict = None
        self.tcp_members = 0
        self.game_start = False

    def story_line(self):
        self.server_socket_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.server_socket_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket_tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_thread = Thread(target=self.initial_udp())
        self.tcp_thread = Thread(target=self.initial_tcp())
        self.udp_thread.start()
        # self.tcp_thread.start()
        # self.initial_game()

    def initial_udp(self):
        massage = struct.pack('Ibh', 0xabcddcba, 0x2, self.server_port)
        self.server_socket_udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket_udp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        print(f'Server started, listening on IP address {self.server_ip}')
        while self.tcp_members<2:
            print("check...")
            self.server_socket_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            self.server_socket_udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket_udp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.server_socket_udp.sendto(massage, (self.server_ip, 13117))
            self.server_socket_udp.close()
            time.sleep(1)
    
    def initial_tcp(self):
        self.server_socket_tcp.bind(('', self.server_port))
        self.server_socket_tcp.listen(1)
        self.server_socket_tcp.setblocking(False)

        while self.game_start:
            try:
                connection_socket, addr = self.server_socket_tcp.accept()
                msg = connection_socket.recv(1024)
                print("the team connected is:", ' >> ', msg.decode(UNICODE))
                client_name = msg.decode(UNICODE)
                self.clients_sockets.append(connection_socket)
                self.clients_sockets_dict[client_name] = connection_socket
                self.game_participants.append(client_name)
                self.tcp_members+=1
            except Exception as ex:
                if str(ex) == "[Errno 35] Resource temporarily unavailable":
                    continue
                time.sleep(1)




    def initial_game(self): pass




server = Server()
server.story_line()

# print(get_if_addr("eth1"))
