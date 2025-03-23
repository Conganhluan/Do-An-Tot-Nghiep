from random import randint
from socket import socket, AF_INET, SOCK_STREAM
from Helper import Helper

class Client_info:

    def __init__(self, round_ID: int, host: str, port: int, DH_public_key: int):
        self.round_ID = round_ID
        self.host = host
        self.port = port
        self.DH_public_key = DH_public_key

class Aggregator_info:

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

class Commitment_params:

    def __init__(self, params : tuple[int]):
        self.p = params[0]
        self.h = params[1]
        self.k = params[2]

class Signer:

    def __init__(self):
        RSA_key_list = open("RSA_keys.csv", "r", encoding='UTF-8').readlines()[1:]
        chosen_RSA_key = RSA_key_list[randint(0,99)].split(', ')
        self.d = int(chosen_RSA_key[1])
        self.e = int(chosen_RSA_key[2])
        self.n = int(chosen_RSA_key[3])

    def get_public_key(self):
        return f"{self.e}_{self.n}"

    def sign(self, data: int):
        return Helper.exponent_modulo(data, self.e, self.n)
    
class Manager:

    def __init__(self):
        
        # Get random port
        self.host = "localhost"
        while True:
            self.port = randint(30000, 60000)
            if socket(AF_INET, SOCK_STREAM).connect_ex(('localhost', self.port)):
                break
        self.signer = Signer()
        self.round_ID = None

    def set_FL_public_params(self, aggregator_host: str, aggregator_port: int, commitment_params: tuple[int]):
        self.aggregator_info = Aggregator_info(aggregator_host, aggregator_port)
        self.commitment_params = Commitment_params(commitment_params)

    def set_round_information(self, round_ID: int, neighbor_list: list[Client_info]):
        self.round_ID = round_ID
        self.neighbor_list = neighbor_list