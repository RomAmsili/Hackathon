import random
import socket
import time
import struct
import threading
import multiprocessing
from scapy.all import get_if_addr

####Style####
CEND = '\33[0m'
CBOLD = '\33[1m'
CITALIC = '\33[3m'
CBLINK = '\33[5m'
CSELECTED = '\33[7m'
####Colors####
CRED = '\33[31m'
CGREEN = '\33[32m'
CYELLOW = '\33[33m'
CBLUE = '\33[34m'
CVIOLET = '\33[35m'
CBEIGE = '\33[36m'
CWHITE = '\33[37m'
CCYAN = '\033[36m'
CORANGE = '\033[33m'
CRED2 = '\33[91m'
CGREEN2 = '\33[92m'
CYELLOW2 = '\33[93m'
CBLUE2 = '\33[94m'
CVIOLET2 = '\33[95m'
CBEIGE2 = '\33[96m'
CWHITE2 = '\33[97m'


class Server:
    def __init__(self, PORT, TEST):
        self.TEST = TEST
        self.Server_Port = PORT
        self.Server_IP = get_if_addr('eth1')
        self.broadcastAddr = '172.1.255.255'
        if TEST: self.broadcastAddr = '172.99.255.255'
        self.Game_Started = False
        self.Time_Remain = 0
        self.Players = {}
        self.teams_name = []
        self.dictLock = threading.Lock()
        self.Next_Group_Number = 1
        self.ServerUDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.ServerUDP.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.ServerUDP.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.ServerTCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ServerTCP.bind((self.Server_IP, PORT))
        self.abort = False
        self.players_needed = 2
        self.Game_Stage = False
        self.Game_start_mssg = GameOpenning = f'{CCYAN}{CBOLD}{CITALIC}Welcome to Quick Maths.{CEND}' + f'{CBLUE}{CITALIC}\nPlayer 1: %s\n{CEND}' + f'{CGREEN}{CITALIC}Player 2: %s\n{CEND}' + f'==\n' + f'{CRED}Please answer the following question as fast as you can:\n{CEND}'
        self.Game_math_ans_lock = threading.Lock()
        self.Game_math_ans = None
        self.is_answer = False
        self.Possible_Winner = None

    def broadcast(self):
        self.timeToStart = time.time() + 10  # 20 sec to start game
        while time.time() < self.timeToStart and not self.Game_Stage:
            print(f'{CCYAN}Broadcast UDP offers {int(self.timeToStart - time.time())} more seconds{CEND}')
            message = struct.pack('IbH', 0xabcddcba, 0x2, self.Server_Port)
            self.ServerUDP.sendto(message, (self.broadcastAddr, 13117))
            # print(f'sec to start: {self.timeToStart - time.time()}')
            time.sleep(1)
        if len(self.Players) != self.players_needed:
            self.abort = True

    def Collect_TCP_Players(self):
        threads = []
        while time.time() < self.timeToStart:
            self.dictLock.acquire()
            if len(self.Players) == self.players_needed:
                self.dictLock.release()
                self.Game_Stage = True
                return
            self.dictLock.release()
            try:
                self.ServerTCP.listen()
                client, addr = self.ServerTCP.accept()
                t = threading.Thread(target=self.getPlayers, args=(client, addr))
                threads.append(t)
                t.start()
                time.sleep(1)
            except:
                pass
        for thread in threads:
            thread.join()

    def getPlayers(self, player, playerAddr):
        """
        Assigning to a Player, will collect the player Team Name, and his performance
        Parameters:
            player (socket): Player socket
            playerAddr (str): Player Addr
        """
        try:
            # Players had 3 secs to send their Team Name
            player.settimeout(3)
            # Getting the player Team Name
            teamNameDecoded = player.recv(1024).decode()
            if "Timeout tERRORs" in teamNameDecoded: return
            # Saving the Player into the dict
            self.dictLock.acquire()
            if len(self.Players) < self.players_needed and teamNameDecoded not in self.teams_name:
                self.Players[player] = [teamNameDecoded, self.Next_Group_Number, 0]
                self.teams_name.append(teamNameDecoded)
                print("Team Name: ", teamNameDecoded, "has joined the game")
            self.dictLock.release()
        except:
            return

    def Game_On(self):
        first_number = random.randint(0, 6)
        second_number = random.randint(0, 3)
        self.Game_math_ans = first_number + second_number
        math = f'How much is {first_number}+{second_number}?'
        massage = (self.Game_start_mssg % (self.teams_name[0], self.teams_name[1])) + math

        for player in self.Players:
            player.sendall((massage).encode())

        Threads = []
        for player in self.Players:
            t = threading.Thread(target=self.get_ans_player, args=(player,))
            t.start()
            Threads.append(t)

        for t in Threads: t.join()

    def get_ans_player(self, player):
        while time.time() < self.End_Time and self.is_answer != True:
            try:
                msg = player.recv(1024)
                if msg:
                    self.Game_math_ans_lock.acquire()
                    if self.is_answer != True:
                        self.Players[player][2] = msg.decode()
                        self.Game_Stage = False
                        self.is_answer = True
                        self.Possible_Winner = player
                    self.Game_math_ans_lock.release()
            except:
                continue

    def publish_result(self):
        GameCloser = f'{CORANGE}{CBOLD}{CITALIC}{CSELECTED}Game over!\n{CEND}' + f'{CBLUE}{CITALIC}The correct answer was %d!\n\n{CEND}'
        if self.is_answer is False:
            GameCloser += f'{CBLUE}{CITALIC}Nobody answer in time, its a %s!\n\n'
            winners = "Draw"
        else:
            try:
                if int(self.Players[self.Possible_Winner][2]) == self.Game_math_ans:
                    GameCloser += f'{CORANGE}{CBOLD}Congratulations to the winners: %s\n'
                    winners = self.Players[self.Possible_Winner][0]
                else:
                    GameCloser += f'{CORANGE}{CBOLD}Congratulations to the winners: %s\n'
                    winners = [self.teams_name[i] for i in range(len(self.teams_name)) if
                               self.teams_name[i] != self.Players[self.Possible_Winner][0]][0]
            except:
                GameCloser += f'{CORANGE}{CBOLD}Congratulations to the winners: %s\n'
                winners = [self.teams_name[i] for i in range(len(self.teams_name)) if
                           self.teams_name[i] != self.Players[self.Possible_Winner][0]][0]
        msg_encode = (GameCloser % (self.Game_math_ans, winners)).encode()
        for player in self.Players.keys():
            player.sendall(msg_encode)
            player.close()

    def reset_server(self):
        self.Game_Started = False
        self.Time_Remain = 0
        self.Players = {}
        self.dictLock = threading.Lock()
        self.Next_Group_Number = 1
        self.abort = False
        self.Game_Stage = False
        self.Game_math_ans_lock = threading.Lock()
        self.Game_math_ans = None
        self.is_answer = False
        self.Possible_Winner = None
        self.teams_name = []

    def story_line(self):
        while True:
            try:
                self.Thread_Broadcast = threading.Thread(target=self.broadcast)
                self.Thread_Broadcast.start()
                print('Server started, listening on IP address {}'.format(self.Server_IP))

                self.Thread_Collect_Players = threading.Thread(target=self.Collect_TCP_Players)
                self.Thread_Collect_Players.start()

                self.Thread_Broadcast.join()
                self.Thread_Collect_Players.join()

                if not self.Game_Stage:
                    print(f'{CYELLOW2}There arent enough Teams to Start The Game{CEND}')
                    self.reset_server()
                    continue

                s = time.time() + 5
                while (time.time() < s):
                    print(f'{CGREEN2}Game start in {int(s - time.time())} second {CEND}')
                    time.sleep(1)
                self.End_Time = time.time() + 10

                self.Thread_Game = threading.Thread(target=self.Game_On)
                self.Thread_Game.start()
                self.Thread_Game.join()

                self.publish_result()

                self.reset_server()
                print(f'{CORANGE}Game over, sending out offer requests...{CEND}')
            except:
                print(f'{CRED}Exception occured, Reset Server{CEND}')
                self.reset_server()


PORT = 2076
HOST = None

Server(PORT, False).story_line()
