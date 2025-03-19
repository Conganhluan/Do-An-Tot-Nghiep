from Manager import FL_Manager, Round_Manager
from time import time

class Controller:
    
    def __init__(self, FL_manager: FL_Manager):
        self.FL_manager = FL_manager
        self.round_manager: None | Round_Manager = None

    def register_client(self, host: str, port: int, RSA_public_key: tuple[int]):
        self.FL_manager.add_client(int(time()*1000), host, port, RSA_public_key)

    def init_round(self, client_num: int):
        client_list = self.FL_manager.choose_clients(client_num)
        self.round_manager = Round_Manager(client_list, self.FL_manager.commitment_params)
        # Please insert code here
            # using self.round_manager.get_DH_params to send DH params to clients
            # using self.round_manager.set_DH_public_key to assign DH public keys for each client
            # using self.round_manager.get_needed_info_for_client to send needed information for each client