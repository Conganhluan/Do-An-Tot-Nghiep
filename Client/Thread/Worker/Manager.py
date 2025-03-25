from Thread.Worker.Helper import Helper
from torch.nn.utils import parameters_to_vector, vector_to_parameters
from Thread.Worker.Masker import Masker
from Thread.Worker.BaseModel import *
import random, torch

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

class Commiter:

    def __init__(self, params : tuple[int]):
        self.p = params[0]
        self.h = params[1]
        self.k = params[2]
        self.r = None

    def commit(self, data) -> int:
        assert self.r
        data = int(data)
        return (Helper.exponent_modulo(self.h, data, self.p) * Helper.exponent_modulo(self.k, self.r, self.p)) % self.p

    def check_commit(self, data: list, commit: list) -> bool:
        assert self.r
        assert len(data) == len(commit)
        return all(self.commit(data[idx]) == commit[idx] for idx in range(len(data)))

    def set_secret(self, r: int):
        self.r = r

class RSA_public_key:
    
    def __init__(self, e, n):
        self.e = e
        self.n = n

class Signer:

    def __init__(self):
        RSA_key_list = open("Thread/Worker/RSA_keys.csv", "r", encoding='UTF-8').readlines()[1:]
        chosen_RSA_key = RSA_key_list[random.randint(0,99)].split(', ')
        self.d = int(chosen_RSA_key[1])
        self.e = int(chosen_RSA_key[2])
        self.n = int(chosen_RSA_key[3])

    def get_public_key(self):
        return RSA_public_key(self.e, self.n)

    def sign(self, data: int):
        return Helper.exponent_modulo(data, self.d, self.n)
    
class Trainer:

    def __init__(self, model_type: type):
        self.local_model: CNNModel = model_type()

    def load_parameters(self, parameters: list):
        tensor = torch.tensor(parameters, requires_grad=True)
        vector_to_parameters(tensor, self.local_model._parameters)

    def train(self, data: list):
        # Please input here
        pass

    def get_parameters(self) -> list:
        return parameters_to_vector(self.local_model.parameters()).detach().numpy().tolist()
    
class Manager:

    class FLAG:
        class NONE:
            # Default value
            pass
        class RE_REGISTER:
            # When commander wants to re-register
            pass
        class ABORT:
            # Used to send abort signal to Trusted party
            pass
        class STOP:
            # Used to stop processing
            pass

    def __init__(self):
        # FL parameters
            # Communication
        self.host = "localhost"
        self.port = Helper.get_available_port()
        self.aggregator_info = None
            # Public parameters
        self.commiter = None
        self.accuracy = 1
            # Controller
        self.flag = self.FLAG.NONE
        self.abort_message = ""
            # Trainer
        self.trainer = None
            # Signer
        self.signer = Signer()

        # Round parameters
        self.last_commit = None
        self.round_ID = None
        self.neighbor_list = None
        self.masker = None

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

    def set_FL_public_params(self, aggregator_host: str, aggregator_port: int, commiter: Commiter, accuracy: int, model_type: type):
        self.aggregator_info = Aggregator_info(aggregator_host, aggregator_port)
        self.commiter = commiter
        self.accuracy = accuracy
        self.trainer = Trainer(model_type)

    def set_round_information(self, round_number: int, round_ID: int, neighbor_list: list[Client_info]):
        self.round_number = round_number
        self.round_ID = round_ID
        self.neighbor_list = neighbor_list
    
    def set_masker(self, g: int, q: int):
        self.masker = Masker(g, q)
    
    def set_last_commit(self, commit: list):
        self.last_commit = commit

    def abort(self, message: str):
        self.abort_message = message
        self.set_flag(self.FLAG.ABORT)