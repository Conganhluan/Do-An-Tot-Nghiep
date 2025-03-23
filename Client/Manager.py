from random import randint
from socket import socket, AF_INET, SOCK_STREAM

class Client_info:

    def __init__(self, round_ID: int, host: str, port: int, DH_public_key: int):
        self.round_ID = round_ID
        self.host = host
        self.port = port
        self.DH_public_key = DH_public_key
        
class Manager:

    def __init__(self):
        
        # Get random port
        while True:
            self.port = randint(60000, 65535)
            if socket(AF_INET, SOCK_STREAM).connect_ex(('localhost', self.port)):
                break

    def set_round_information(self, round_ID: int, neighbor_list: list[Client_info]):
        self.round_ID = round_ID
        self.neighbor_list = neighbor_list

    