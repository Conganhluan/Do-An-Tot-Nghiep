from Helper import Helper

class Manager: 

    class Client_info:
            
        def __init__(self, ID: int, host: str, port: int, RSA_public_key: tuple[int]):
            # Unique attributes
            self.ID = ID        # Permanent for FL_Manager, temporary for Round_Manager
            self.host = host
            self.port = port
            self.RSA_pulic_key = RSA_public_key
            # Round attributes
            self.round_ID = 0
            self.DH_public_key = 0
            self.neighbor_list = 0

        def set_DH_public_key(self, DH_public_key: int):
            self.DH_public_key = DH_public_key

        def set_round_information(self, client_round_ID: int, neighbor_round_ID_list: list[int]):
            self.round_ID = client_round_ID
            self.neighbor_list = neighbor_round_ID_list

    class Commitment_params:

        def __init__(self):
            # Please create h, k, p here
            self.h = 0
            self.k = 0
            self.p = 0

    class DH_params:

        def __init__(self):
            # Please create g, q here
            self.g = 0
            self.q = 0

class FL_Manager(Manager):

    def __init__(self):
        self.client_list = list()
        self.commitment_params = self.Commitment_params()

    def __get_client_by_ID__(self, client_ID: int) -> Manager.Client_info | None:
        for client_info in self.client_list:
            if client_info.ID == client_ID:
                return client_info
        return None
    
    def __get_client_by_round_ID__(self, client_round_ID: int) -> Manager.Client_info | None:
        for client_info in self.client_list:
            if client_info.round_ID == client_round_ID:
                return client_info
        return None

    def add_client(self, client_id: int, host: str, port: int, RSA_public_key: tuple[int]) -> None:
        self.client_list.append(self.Client_info(client_id, host, port, RSA_public_key))

    def get_commitment_params(self) -> Manager.Commitment_params:
        return self.commitment_params
    
    def choose_clients(self, client_num: int) -> list[Manager.Client_info]:
        # Please insert the client selection algorithm here
        pass
    
class Round_Manager(Manager):

    def __init__(self, client_list: list[Manager.Client_info], commitment_params: Manager.Commitment_params):
        self.client_list = client_list
        
        # Create graph and add round information for clients
        # Please insert here to specify the neighbor_num more useful
        neighbor_num = min(29, len(self.client_list)-1)
        graph = Helper.build_graph(len(self.client_list), neighbor_num)
        for round_ID in range(len(self.client_list)):
            self.client_list[round_ID].set_round_information(round_ID, graph[round_ID])

        self.commitment_params = commitment_params
        self.dh_params = Manager.DH_params()

    def get_DH_params(self) -> tuple[int]:
        return (self.dh_params.g, self.dh_params.q)
    
    def set_DH_public_key(self, client_ID: int, DH_public_key: int) -> None:
        self.__get_client_by_ID__(client_ID).set_DH_public_key(DH_public_key)

    def __get_client_by_ID__(self, client_ID: int) -> Manager.Client_info | None:
        for client_info in self.client_list:
            if client_info.ID == client_ID:
                return client_info
        return None
    
    def __get_client_by_round_ID__(self, client_round_ID: int) -> Manager.Client_info | None:
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