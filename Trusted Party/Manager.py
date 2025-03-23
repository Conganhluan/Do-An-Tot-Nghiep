from Helper import Helper
from random import randint, choices
from sympy import randprime, primitive_root
from copy import deepcopy

class Client_info:
        
    def __init__(self, ID: int, host: str, port: int, RSA_public_key: tuple[int]):
        # Unique attributes
        self.ID = ID
        self.host = host
        self.port = port
        self.RSA_pulic_key = RSA_public_key
        self.choose_possibility = 100
        # Round attributes
        self.round_ID = 0
        self.DH_public_key = 0
        self.neighbor_list = None

    def set_DH_public_key(self, DH_public_key: int):
        self.DH_public_key = DH_public_key

    def set_round_information(self, client_round_ID: int, neighbor_round_ID_list: list[int]):
        self.round_ID = client_round_ID
        self.neighbor_list = neighbor_round_ID_list

class Aggregator_info:

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

class Commitment_params:

    def __init__(self):
        self.p = randprime(1 << 63, 1 << 64)
        self.h = primitive_root(self.p)
        self.k = randint(1 << 63, 1 << 64)

class DH_params:

    def __init__(self):
        DH_param_list = open("DH_params.csv", "r", encoding="UTF-8").readlines()[1:]
        DH_param_pair = DH_param_list[randint(0, len(DH_param_list)-1)].split(",")
        self.q, self.g = int(DH_param_pair[1]), int(DH_param_pair[2])

class FL_Manager():

    def __init__(self):
        self.client_list = list()
        self.commitment_params = Commitment_params()
        self.current_round = 0
        self.global_weight_commitment = list()

    def register_aggregator(self, host: str, port: int):
        self.aggregator_info = Aggregator_info(host, port)

    def __get_client_by_ID__(self, client_ID: int) -> Client_info | None:
        for client_info in self.client_list:
            if client_info.ID == client_ID:
                return client_info
        return None
    
    def __get_client_by_round_ID__(self, client_round_ID: int) -> Client_info | None:
        for client_info in self.client_list:
            if client_info.round_ID == client_round_ID:
                return client_info
        return None

    def add_client(self, client_id: int, host: str, port: int, RSA_public_key: tuple[int]) -> None:
        self.client_list.append(Client_info(client_id, host, port, RSA_public_key))

    def get_commitment_params(self) -> Commitment_params:
        return self.commitment_params
    
    def choose_clients(self, client_num: int) -> list[Client_info]:
        if client_num > len(self.client_list):
            client_num = len(self.client_list)
        return_list = list()
        client_list = deepcopy(self.client_list)
        for i in range(client_num):
            chosen_one = choices(client_list, weights=[max(client.choose_possibility, 0) for client in client_list])[0]
            client_list.remove(chosen_one)
            return_list.append(chosen_one)
        return return_list
    
class Round_Manager():

    def __init__(self, client_list: list[Client_info], round_number: int):
        self.client_list = client_list
        self.round_number = round_number
        
        # Create graph and add round information for clients
        # Please insert here to specify the neighbor_num more useful
        neighbor_num = min(30, len(self.client_list)-1)

        graph = Helper.build_graph(len(self.client_list), neighbor_num)
        for round_ID in range(len(self.client_list)):
            self.client_list[round_ID].set_round_information(round_ID, graph[round_ID])

        self.commitment_params = Commitment_params()
        self.dh_params = DH_params()

    def get_DH_params(self) -> DH_params:
        return self.dh_params
    
    def set_DH_public_key(self, client_ID: int, DH_public_key: int) -> None:
        self.__get_client_by_ID__(client_ID).set_DH_public_key(DH_public_key)

    def __get_client_by_ID__(self, client_ID: int) -> Client_info | None:
        for client_info in self.client_list:
            if client_info.ID == client_ID:
                return client_info
        return None
    
    def __get_client_by_round_ID__(self, client_round_ID: int) -> Client_info | None:
        for client_info in self.client_list:
            if client_info.round_ID == client_round_ID:
                return client_info
        return None

    def get_needed_info_for_client(self, client_id: int) -> dict:
        
        client = self.__get_client_by_ID__(client_id)
        needed_information = {
            "Round ID": client.round_ID,
            "Neighbors": list()
        }
        for neighbor_round_id in client.neighbor_list:
            neighbor = self.__get_client_by_round_ID__(neighbor_round_id)
            needed_information["Neighbors"].append((neighbor_round_id, neighbor.host, neighbor.port, neighbor.DH_public_key))

        return needed_information