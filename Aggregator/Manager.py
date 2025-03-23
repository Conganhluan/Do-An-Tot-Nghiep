import sys, os
sys.path.append(os.path.abspath(".."))
from BaseModels import CNNModel
from random import randint
from socket import socket, AF_INET, SOCK_STREAM

class Client_info:

    def __init__(self, round_ID: int, host: str, port: int, RSA_public_key: tuple[int], DH_public_key: int, neighbor_list: list):
        self.round_ID = round_ID
        self.host = host
        self.port = port
        self.RSA_public_key = RSA_public_key
        self.DH_public_key = DH_public_key
        self.neighbor_list = neighbor_list

class Commitment_params:

    def __init__(self, params : tuple[int]):
        self.p = params[0]
        self.h = params[1]
        self.k = params[2]

class Manager:

    def __init__(self):
        self.global_model = CNNModel()
        self.client_list = None
        self.host = "localhost"
        while True:
            self.port = randint(30000, 60000)
            if socket(AF_INET, SOCK_STREAM).connect_ex(('localhost', self.port)):
                break
    
    def set_commitment_params(self, commitment_params: tuple[int]):
        self.commitment_params = Commitment_params(commitment_params)

    def set_round_information(self, client_list: list[Client_info]):
        self.client_list = client_list

    def get_global_state_dict(self) -> dict:
        return self.global_model.state_dict()