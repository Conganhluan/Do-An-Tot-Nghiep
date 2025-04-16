from Thread.Worker.Helper import Helper
from Thread.Worker.BaseModel import *           # This can be removed
import random, numpy
from sympy import randprime, primitive_root
from copy import deepcopy

class RSA_public_key:
    
    def __init__(self, e, n):
        self.e = e
        self.n = n

class Client_info:
        
    def __init__(self, ID: int, host: str, port: int, rsa_public_key: RSA_public_key):
        # Unique attributes
        self.ID = ID
        self.host = host
        self.port = port
        self.RSA_public_key = rsa_public_key
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

    def __init__(self, host: str, port: int, public_key: RSA_public_key, base_model_class: type):
        self.host = host
        self.port = port
        self.RSA_public_key = public_key
        self.base_model_class = base_model_class

# class Commiter:

#     def __init__(self):
#         self.p = randprime(1 << 63, 1 << 64)
#         self.h = primitive_root(self.p)
#         self.k = random.randint(1 << 63, 1 << 64)
#         self.r = None

class DH_params:

    def __init__(self):
        DH_param_list = open("Thread/Worker/Data/DH_params.csv", "r", encoding="UTF-8").readlines()[1:]
        DH_param_pair = DH_param_list[random.randint(0, len(DH_param_list)-1)].split(",")
        self.q, self.g = int(DH_param_pair[1]), int(DH_param_pair[2])

class Manager():

    class FLAG:
        class NONE:
            # Default value
            pass
        class START_ROUND:
            # When get initiation signal user
            pass
        class STOP:
            # Used to indicate situation that needs process stopping
            pass

    def __init__(self):
        # FL parameters
            # Communication
        self.client_list : list[Client_info] = list()
        self.aggregator_info = None
            # Public parameters
        # self.commiter = Commiter()
        self.current_round = 0
        # self.last_commitment: numpy.ndarray[numpy.int64] = None
        self.gs_mask = random.randint(1, 2 ** 64)
            # Controller
        self.flag = self.FLAG.NONE
        self.stop_message = ""
        # Round parameters
        self.round_manager : Round_Manager = None

    def stop(self, message: str):
        self.stop_message = message
        self.set_flag(self.FLAG.STOP)

    def get_flag(self) -> type:
        if self.flag == Manager.FLAG.NONE:
            return Manager.FLAG.NONE
        print(f"Get flag of {self.flag.__name__}")
        return_flag = self.flag
        self.flag = Manager.FLAG.NONE
        return return_flag

    def set_flag(self, flag: type) -> None:
        self.flag = flag
        print(f"Set flag to {self.flag.__name__}")

    def clear_client(self) -> None:
        self.client_list.clear()
    
    def clear_aggregator(self) -> None:
        self.aggregator_info = None
        # self.last_commitment = None

    def register_aggregator(self, host: str, port: int, public_key: RSA_public_key, base_model_class: type):
        self.aggregator_info = Aggregator_info(host, port, public_key, base_model_class)

    # def set_last_model_commitment(self, model_commitment: numpy.ndarray[numpy.int64]):
    #     self.last_commitment = model_commitment

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

    def add_client(self, client_id: int, host: str, port: int, rsa_public_key: RSA_public_key) -> None:
        self.client_list.append(Client_info(client_id, host, port, rsa_public_key))

    def get_current_round(self) -> int:
        return self.current_round

    # def get_commiter(self) -> Commiter:
    #     return self.commiter
    
    def choose_clients(self, client_num: int) -> list[Client_info]:
        if client_num > len(self.client_list):
            client_num = len(self.client_list)
        return_list = list()
        client_list = deepcopy(self.client_list)
        for i in range(client_num):
            chosen_one = random.choices(client_list, weights=[max(client.choose_possibility, 0) for client in client_list])[0]
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

    def get_neighbor_information(self, client_id: int) -> list:
        
        client = self.__get_client_by_ID__(client_id)
        neighbor_information = list()
        for neighbor_round_id in client.neighbor_list:
            neighbor = self.__get_client_by_round_ID__(neighbor_round_id)
            neighbor_information.append((neighbor_round_id, neighbor.host, neighbor.port, neighbor.DH_public_key))
        return neighbor_information