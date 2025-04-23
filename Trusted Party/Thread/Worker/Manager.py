from Thread.Worker.Helper import Helper
from Thread.Worker.BaseModel import *           # This can be removed
import random, numpy, time, threading
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
        self.accuracy_ratio = 0

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

class Commiter:

    def __init__(self):
        self.p = randprime(1 << 7, 1 << 8)
        self.h = primitive_root(self.p)
        self.k = random.randint(1 << 7, 1 << 8)
        self.r = None

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
        class END_ROUND:
            # When gather enough client result or out of timer
            pass

    def __init__(self):
        # FL parameters
            # Communication
        self.client_list : list[Client_info] = list()
        self.aggregator_info = None
            # Public parameters
        self.commiter = Commiter()
        self.current_round = 0
        self.last_commitment: numpy.ndarray[numpy.int64] = None
        self.old_gs_mask = 1
        self.new_gs_mask = random.randint(1, 2 ** 64)
            # Controller
        self.flag = self.FLAG.NONE
        self.stop_message = ""
        # Round parameters
        self.round_manager : Round_Manager = None

    def end_round(self) -> bool:
        
        # Check information between clients and Aggregator
        checked = all([all(self.last_commitment == another_commit) for another_commit in self.round_manager.received_commit[1:]])
        if not checked:
            self.stop("The parameters between clients are not the same")
            return False
        
        # Check the accuracy evaluation from the client
        accuracy_list = [client.accuracy_ratio for client in self.round_manager.client_list if client.accuracy_ratio]
        avg_accuracy = sum(accuracy_list)/len(accuracy_list)
        print(f"Average accuracy from client: {avg_accuracy}")
        valid_accuracy = sum([1 if accuracy >= 90 else 0 for accuracy in accuracy_list])
        if valid_accuracy >= 0.8 * len(self.round_manager.client_list):
            self.stop("There are more than 80% of client have more than 90% accuracy on the aggregated global model")
            return False

        # Update information
        self.current_round += 1
        self.old_gs_mask = self.new_gs_mask
        self.new_gs_mask = random.randint(1, 2 ** 64)
        del self.round_manager

        # Return TRUE when there is next round
        return True

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
        self.last_commitment = None

    def register_aggregator(self, host: str, port: int, public_key: RSA_public_key, base_model_class: type):
        self.aggregator_info = Aggregator_info(host, port, public_key, base_model_class)

    def set_last_model_commitment(self, model_commitment: numpy.ndarray[numpy.int64]):
        self.last_commitment = model_commitment

    def calculate_choosibility(self, round_attendees: list[Client_info]):
        chosen_ones = list()
        for attendee in round_attendees:
            client = self.__get_client_by_ID__(attendee.ID)
            client.choose_possibility -= 25
            chosen_ones.append(client)
        for client in self.client_list:
            if client not in chosen_ones:
                client.choose_possibility += 25

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

    def get_commiter(self) -> Commiter:
        return self.commiter
    
    def choose_clients(self, available_client_list: list[Client_info], client_num: int) -> list[Client_info]:
        """
        This function gets a list of availabe client and number of desired chosen clients
        It chooses a subset of clients, which then be removed from the available client list 'directly', and returned as the output of the function
        """
        
        return_list = list()
        for i in range(client_num):
            chosen_one = random.choices(available_client_list, weights=[max(client.choose_possibility, 0) for client in available_client_list])[0]
            available_client_list.remove(chosen_one)
            return_list.append(chosen_one)
        return return_list
    
    def end_timer(self):
        self.timeout = True
        self.timeout_time = time.time()
        self.set_flag(self.FLAG.END_ROUND)
        self.checker = None

    def the_checker(self):
        while True:
            if self.timeout:
                return
            elif len(self.round_manager.received_commit) == len(self.round_manager.client_list):
                print("There are enough clients sending their round result")
                self.timer.cancel()
                self.end_timer()
                return
            time.sleep(10)

    def start_timer(self, timeout_seconds: int = 60):
        self.timeout = False
        self.timer = threading.Timer(timeout_seconds, self.end_timer)
        self.timer.start()

        self.checker = threading.Thread(target=self.the_checker)
        self.checker.start()

class Round_Manager():

    def __init__(self, client_list: list[Client_info], round_number: int, commiter: Commiter):
        self.client_list = client_list
        self.round_number = round_number
        self.received_commit = list()
        
        # Create graph and add round information for clients
        # Please insert here to specify the neighbor_num more useful
        neighbor_num = min(30, len(self.client_list)-1)

        graph = Helper.build_graph(len(self.client_list), neighbor_num)
        for round_ID in range(len(self.client_list)):
            self.client_list[round_ID].set_round_information(round_ID, graph[round_ID])

        self.commiter = commiter
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