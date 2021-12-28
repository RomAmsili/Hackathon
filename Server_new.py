from socket import *
from scapy.all import *
import time
import struct
import random
from Statistics import Statistics
from Constants import *


class Server:

    def __init__(self, statistics, flag=True):
        self.server_socket_udp = None
        self.server_socket_tcp = None
        self.server_port = SERVER_PORT
        self.server_ip = get_if_addr("eth1")
        self.broadcast_flag = flag
        self.game_participants = []
        self.game_participants_dict = {}
        self.clients_sockets = []
        self.clients_sockets_dict = {}
        self.client_threads = []
        self.game_started = False
        self.start_game_msg = ""
        self.udp_thread = None
        self.tcp_thread = None
        self.first_list = []
        self.second_list = []
        self.score_dictionary = {GROUP_NAME_1: 0, GROUP_NAME_2: 0}
        self.winner_message = ""
        self.statistics = statistics

    def initiate_server(self):
        """
        Initialize the server, starts TCP tread and UDP thread for getting and sending messages
        :return: None
        """
        try:
            print(f'Server started, listening on IP address {self.server_ip}')
            self.server_socket_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            self.server_socket_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket_tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.udp_thread = Thread(target=self.activate_server_udp)
            self.tcp_thread = Thread(target=self.activate_server_tcp)
            self.udp_thread.start()
            self.tcp_thread.start()
            self.udp_thread.join()
            self.tcp_thread.join()
            self.initiate_game()
            self.close_connections_with_clients()
            time.sleep(0.5)
            self.reset_server()
        except Exception as e:
            print(e)
            time.sleep(1)
            self.server_socket_tcp.close()

    def activate_server_udp(self):
        """
        Opens UDP socket to send messages to broadcast
        :return: None
        """
        self.server_socket_udp.settimeout(SECONDS_WAITING_FOR_CLIENTS)
        message = struct.pack('Ibh', 0xfeedbeef, 0x2, self.server_port)
        time_started = time.time()

        while True:
            if time.time() > time_started + SECONDS_WAITING_FOR_CLIENTS:
                print(SECONDS_WAITING_FOR_CLIENTS,"second passed")
                self.broadcast_flag = False
                return
            self.server_socket_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            self.server_socket_udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            self.server_socket_udp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.server_socket_udp.bind(('', 50005))
            self.server_socket_udp.sendto(message, (BROADCAST_IP, BROADCAST_PORT))
            self.server_socket_udp.close()
            time.sleep(1)

    def activate_server_tcp(self):
        """
        Open TCP connection to get clients responses, Collecting Clients.
        :return: None
        """
        print(f'opened tcp on {self.server_ip} with port num {self.server_port}')
        self.server_socket_tcp.bind(('', self.server_port))
        # self.server_socket_tcp.bind((self.server_ip, self.server_port))
        self.server_socket_tcp.listen(1)
        self.server_socket_tcp.setblocking(False)
        while self.broadcast_flag:
            try:
                connection_socket, addr = self.server_socket_tcp.accept()

                msg = connection_socket.recv(MESSAGE_SIZE)

                print("the team connected is:", ' >> ', msg.decode(UNICODE))
                client_name = msg.decode(UNICODE)
                self.clients_sockets.append(connection_socket)
                self.clients_sockets_dict[client_name] = connection_socket
                self.game_participants.append(client_name)
            except Exception as ex:
                if str(ex) == "[Errno 35] Resource temporarily unavailable":
                    continue
                time.sleep(1)

    def initiate_game(self):
        """
        Initialize game for every client connected, every client is a thread.
        :return:
        """
        self.first_list, self.second_list = self.split_participants()

        for client_socket in self.clients_sockets_dict:
            self.game_participants_dict[client_socket] = 0
            client_thread = Thread(target=self.new_game_for_client,
                                   args=(self.clients_sockets_dict[client_socket], client_socket))
            client_thread.start()
            self.client_threads.append(client_thread)

        for client_thread in self.client_threads:
            client_thread.join()

        self.game_started = True

    def split_participants(self):
        """
        Splits all participates to two groups
        :return: Two lists of participants
        """
        random.shuffle(self.game_participants)
        list_size = len(self.game_participants)
        first_list = self.game_participants[:list_size // 2]
        second_list = self.game_participants[list_size // 2:]
        return first_list, second_list

    def new_game_for_client(self, client_socket, client_name):
        """
        Sends welcome message to a client and starts the game for the client.
        :param client_socket: The Client socket
        :param client_name: The Client name
        :return: None
        """
        print("connected")
        msg = Colors.TITLE + "Welcome to Keyboard Spamming Battle Royale." + Colors.END_COLOR + '\n'
        msg += Colors.GROUP_1_TITLE + "Group1:" + Colors.END_COLOR + '\n'
        msg += Colors.GROUP_1_TITLE + '==' + Colors.END_COLOR + '\n'
        msg += "".join(
            [Colors.GROUP_1_TITLE + str(group_name) + Colors.END_COLOR for group_name in self.first_list]) + '\n'
        msg += Colors.GROUP_2_TITLE + "Group2:" + Colors.END_COLOR + '\n'
        msg += Colors.GROUP_2_TITLE + '==' + Colors.END_COLOR + '\n'
        msg += Colors.GROUP_2_TITLE + "".join([str(group_name) for group_name in self.second_list]) + Colors.END_COLOR
        msg += '\n' + Colors.TITLE + "Start pressing keys on your keyboard as fast as you can!!" + Colors.END_COLOR
        msg += '\n'

        client_socket.send(msg.encode())

        self.run_game(client_name, client_socket)

    def run_game(self, client_name, client_socket):
        """
        Getting and counting messages from clients
        :param client_name:
        :param client_socket:
        :return:
        """
        client_socket.setblocking(0)
        time_started_game = time.time()
        while time.time() < time_started_game + 10:
            try:
                msg = client_socket.recv(1024)
                if client_name in self.first_list:
                    self.score_dictionary[GROUP_NAME_1] += len(msg)
                else:
                    self.score_dictionary[GROUP_NAME_2] += len(msg)
            except Exception as ex:
                if str(ex) == "[Errno 35] Resource temporarily unavailable" or \
                        "[Errno 11] Resource temporarily unavailable":
                    time.sleep(0.5)
                    continue
                else:
                    print(ex)
                time.sleep(0.5)

        self.game_over_message()

    def game_over_message(self):
        """
        Initiate and setting winner message
        :return: None
        """
        winner = max(self.score_dictionary.items(), key=operator.itemgetter(1))[0]
        self.statistics.update(self.get_winner_participants(str(winner)), self.score_dictionary[winner])
        looser = min(self.score_dictionary.items(), key=operator.itemgetter(1))[0]
        winner_msg = ""
        winner_msg += self.color_text(str(winner), str(self.score_dictionary[winner]))
        winner_msg += self.color_text(str(looser), str(self.score_dictionary[looser]))
        winner_msg += self.print_winner_team(str(winner)) + '\n'
        winner_msg += '\t' + Colors.TITLE + "Congratulations to the winners:" + Colors.END_COLOR + '\n'
        winner_msg += '\t\t\t' + Colors.TITLE + "==" + Colors.END_COLOR + '\n'
        winner_msg += self.print_winners(winner)
        winner_msg += self.print_high_scores()
        self.winner_message = winner_msg

    def get_winner_participants(self, winner):
        """
        Getting all participants name of the winning group
        :param winner: The winning group name
        :return: List of participants names
        """
        if winner == GROUP_NAME_1:
            return [str(player) for player in self.first_list]
        else:
            return [str(player) for player in self.second_list]

    def print_winner_team(self, winner):
        """
        Formatting nicely the winner team
        :param winner: The winning team name
        :return: String of the winning team
        """
        winner_msg = ""
        if winner == GROUP_NAME_1:
            winner_msg += '\n\t\t' + Colors.GROUP_1_TITLE + str(winner) + " wins!" + Colors.END_COLOR
        else:
            winner_msg += '\n\t\t' + Colors.GROUP_2_TITLE + str(winner) + " wins!" + Colors.END_COLOR
        return winner_msg + '\n'

    def print_winners(self, winner):
        """
        Formatting nicely the winner team participants
        :param winner: The winning team name
        :return: String of the winning team participants
        """
        msg = ""
        if winner == GROUP_NAME_1:
            for player in self.first_list:
                r = random.randint(41, 47) #Randoming color for each player
                msg += '\t\t' + '\x1b[1;' + str(r) + ';40m' + str(player) + Colors.END_COLOR + '\n'
        else:
            for player in self.second_list:
                r = random.randint(30, 37)
                msg += '\t\t' + '\x1b[1;' + str(r) + ';40m' + str(player) + Colors.END_COLOR + '\n'
        return msg

    def color_text(self, group_name, number_chars):
        """
        Formatting nicely the scores of a team
        :param group_name: String containing group name
        :param number_chars: Number of chars sent by the group
        :return: String formatted message
        """
        num_chars_msg = Colors.NUM_CHARS + str(number_chars) + Colors.END_COLOR
        if group_name == GROUP_NAME_1:
            typed_in_msg = Colors.GROUP_1_TITLE + " typed in " + Colors.END_COLOR
            characters_msg = Colors.GROUP_1_TITLE + " characters." + Colors.END_COLOR
            group_name_msg = Colors.GROUP_1_TITLE + str(group_name) + Colors.END_COLOR
        else:
            typed_in_msg = Colors.GROUP_2_TITLE + " typed in " + Colors.END_COLOR
            characters_msg = Colors.GROUP_2_TITLE + " characters." + Colors.END_COLOR
            group_name_msg = Colors.GROUP_2_TITLE + str(group_name) + Colors.END_COLOR
        return group_name_msg + typed_in_msg + num_chars_msg + characters_msg + "\n"

    def print_high_scores(self):
        return Colors.GROUP_1_TITLE + "Best group ever is " + self.statistics.best_team + \
               " with " + str(self.statistics.best_score) + " points!" + Colors.END_COLOR + '\n'

    def reset_server(self):
        """
        Resetting the game
        :return: None
        """
        self.game_started = False
        self.broadcast_flag = True
        self.start_game_msg = ""

    def close_connections_with_clients(self):
        """
        Sends winning message to all client and close their sockets.
        :return: None
        """
        for client_sock in self.clients_sockets:
            client_sock.send(self.winner_message.encode())
            client_sock.close()


def main():
    """
    Main function, initialize server and starting games
    :return:
    """
    statistics = Statistics()
    while True:
        server = Server(statistics)
        server.initiate_server()
        time.sleep(3)


if __name__ == "__main__":
    main()
