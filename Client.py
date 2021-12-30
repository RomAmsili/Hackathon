from socket import *
from scapy.all import *
import struct
import sys
import select
import traceback
import getch

class Client:
    def __init__(self, name):
        """
        Constructor
        :param name: Client group name
        :return: None
        """
        self.team_name = name
        self.client_socket = None
        self.server_socket = None

    def look_for_host(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        print("Client started, listening for offer requests...")
        self.client_socket.bind(('172.1.255.255', 13117))
        while True:
            try:
                data_rcv, addr = self.client_socket.recvfrom(1024)
                # if addr[0] != '172.1.0.76':
                #     continue
                data = struct.unpack('Ibh', data_rcv)
                if hex(data[0]) == "0xabcddcba" and hex(data[1]) == "0x2":
                    print(f'Received offer from {addr[0]}, attempting to connect...')
                self.activate_client_tcp(addr[0], int(data[2]))
                return
            except struct.error:
                pass
            except Exception as err:
                print(err)


    def activate_client_tcp(self, server_name, server_port):
        """
        Connecting to a server with TCP
        :param server_name: Server to connect name
        :param server_port: Server to connect port
        :return: None
        """
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.connect((server_name, server_port))
        self.server_socket.send(str(self.team_name + '\n').encode())
        self.wait_for_game_start()

    def wait_for_game_start(self):
        """
        Waiting for game to begin - Until message from Server arrives.
        :return: None
        """
        welcome = ""
        # self.server_socket.setblocking(False)
        while not welcome:
            try:
                sentence = self.server_socket.recv(1024)
                welcome = sentence.decode(UNICODE)
                if welcome:
                    print(welcome)
                else:
                    continue
            except Exception as ex:
                print("No Welcome Message has been received")
                continue
            self.PlayGame()
            print('Server disconnected, listening for offer requests...')

    def PlayGame(self):
        char = getch.getch()
        self.server_socket.sendall(char.encode())
        data = None
        try:
            data = self.server_socket.recv(1024)
        except:
            pass
        if data is None:
            print(f"{CBOLD}{CGREY}{CSELECTED}No GameOver Message, but it's over..{CEND}")
        else:
            print(data.decode())

while True:
    cl = Client('Rom & Ory')
    cl.look_for_host()

