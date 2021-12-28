from socket import *
from scapy.all import *
import struct
import sys
import select
import traceback

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
        self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        print("Client started, listening for offer requests...")
        self.client_socket.bind(('', 13117))
        while True:
            try:
                data_rcv, addr = self.client_socket.recvfrom(1024)
                if addr[0] != '172.1.0.76': 
                    print(addr[0])
                    continue
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
        self.server_socket.send(str(self.team_name).encode())
        self.wait_for_game_start()
        try:
            self.game_in_progress()
        except Exception as e:
            os.system("stty -raw echo")
            traceback.print_exc()
        self.game_ended()

    def wait_for_game_start(self):
        """
        Waiting for game to begin - Until message from Server arrives.
        :return: None
        """
        modified_sentence = ""
        self.server_socket.setblocking(False)
        while not modified_sentence:
            try:
                sentence = self.server_socket.recv(MESSAGE_SIZE)
                modified_sentence = sentence.decode(UNICODE)
                if modified_sentence:
                    print(modified_sentence)
            except Exception as ex:
                if str(ex) == "[Errno 35] Resource temporarily unavailable":
                    time.sleep(0)
                    continue
                time.sleep(0.2)


# interfaces = socket.getaddrinfo(host=socket.gethostname(), port=None, family=socket.AF_INET)
# ip = [ip[-1][0] for ip in interfaces][1]
cl = Client('Rom & Ory Team')
cl.look_for_host()

