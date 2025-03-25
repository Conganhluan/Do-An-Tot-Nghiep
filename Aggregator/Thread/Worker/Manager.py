from Thread.Worker.BaseModel import *
import random
from Thread.Worker.Helper import Helper
from torch.nn.utils import parameters_to_vector, vector_to_parameters

class RSA_public_key:

    def __init__(self, e, n):
        self.e = e
        self.n = n

class Client_info:

    def __init__(self, round_ID: int, host: str, port: int, RSA_public_key: RSA_public_key, DH_public_key: int, neighbor_list: list):
        
        # Before training
        self.round_ID = round_ID
        self.host = host
        self.port = port
        self.RSA_public_key = RSA_public_key
        self.DH_public_key = DH_public_key
        self.neighbor_list = neighbor_list

        # After training
        self.is_online = True
        self.local_statedict = None
        self.signed_statedict = None
        self.local_datanum = 0
        self.signed_datanum = 0
        self.secret_points = None

class Commiter:

    def __init__(self, params : tuple[int]):
        self.p = params[0]
        self.h = params[1]
        self.k = params[2]
        self.r = None
    
    def gen_new_secret(self) -> None:
        self.r = random.randint(1, 2147483648)

    def get_secret(self) -> int:
        return self.r

    def commit(self, data) -> int:
        assert self.r
        data = int(data)
        return (Helper.exponent_modulo(self.h, data, self.p) * Helper.exponent_modulo(self.k, self.r, self.p)) % self.p

class Manager:

    class FLAG:
        class NONE:
            # Default value
            pass
        class START_ROUND:
            # When get initiation signal from Trusted party
            pass
        class RE_REGISTER:
            # When commander wants to re-register with the Trusted party
            pass
        class ABORT:
            # Used to send abort signal to Trusted party
            pass
        class STOP:
            # Used to stop processing
            pass

    def __init__(self, model_type: type):
        # FL parameters
            # Communication
        self.host = "localhost"
        self.port = Helper.get_available_port()
            # Public parameters
        self.commiter = None
        self.round_number = 0
            # Controller
        self.flag = Manager.FLAG.NONE
        self.abort_message = ""
            # Aggregator
        self.global_model : CNNModel = model_type()
        self.model_type = model_type
        
        # Round parameters
        self.client_list = None
    
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

    def set_public_parameters(self, commiter: Commiter):
        self.commiter = commiter

    def set_round_information(self, client_list: list[Client_info]):
        self.client_list = client_list

    def get_model_parameters(self) -> list:
        return parameters_to_vector(self.global_model.parameters()).detach().numpy().tolist()

    def set_commiter(self, commiter: Commiter) -> None:
        self.commiter = commiter

    def get_model_commit(self) -> list:
        arr : list = self.get_model_parameters()
        for idx in range(len(arr)):
            arr[idx] = self.commiter.commit(int(arr[idx]))
        return arr
    
    def abort(self, message: str):
        self.abort_message = message
        self.set_flag(self.FLAG.ABORT)