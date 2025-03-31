from Thread.Worker.BaseModel import *
import random, numpy, time, struct, threading
from Thread.Worker.Helper import Helper
from torch.nn.utils import parameters_to_vector, vector_to_parameters

class RSA_public_key:

    def __init__(self, e, n):
        self.e = e
        self.n = n

class Receipt:

    def __init__(self, received_time: float, signed_received_data: int):
        self.received_time = received_time
        self.signed_received_data = signed_received_data

class Signer:

    def __init__(self):
        self.d = 129357748760673500352691599801356668193
        self.e = 65537
        self.n = 141744169545699033667390251374615762519

    def get_public_key(self):
        return RSA_public_key(self.e, self.n)

    def sign(self, data: int) -> int:
        return Helper.exponent_modulo(data, self.d, self.n)
    
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
        self.is_online = False
        self.local_parameters : numpy.ndarray[numpy.int64] = None
        self.signed_parameters : int = 0
        self.local_datanum : int = 0
        self.signed_datanum : int = 0
        self.secret_points = None
        self.receipt = None
    
    def set_trained_data(self, data_number: int, signed_data_number: int, signed_parameters: int, parameters: numpy.ndarray[numpy.int64]) -> None:
        self.local_datanum = data_number
        self.signed_datanum = signed_data_number
        self.signed_parameters = signed_parameters
        self.local_parameters = parameters

    def create_receipt(self, signer: Signer):
        received_time = time.time()
        received_data = int.from_bytes(struct.pack('f', received_time) + self.local_datanum.to_bytes(5) + self.local_parameters.tobytes())
        self.receipt = Receipt(received_time, signer.sign(received_data))

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

    def commit(self, data) -> numpy.int64:
        assert self.r
        data = int(data)
        return Helper.PRNG((Helper.exponent_modulo(self.h, data, self.p) * Helper.exponent_modulo(self.k, self.r, self.p)) % self.p, 8)

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
        self.signer = Signer()
            # Public parameters
        self.commiter = None
        self.round_number = 0
            # Controller
        self.flag = Manager.FLAG.NONE
        self.abort_message = ""
        self.timeout = True
        self.timeout_time = 0
            # Aggregator
        self.global_model : CNNModel_MNIST = model_type()
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

    def get_model_parameters(self) -> numpy.ndarray[numpy.float32 | numpy.int64]:
        return parameters_to_vector(self.global_model.parameters()).detach().numpy()

    def set_commiter(self, commiter: Commiter) -> None:
        self.commiter = commiter

    def get_model_commit(self) -> numpy.ndarray[numpy.int64]:
        param_arr = self.get_model_parameters()
        commit_arr = numpy.zeros((len(param_arr), ), dtype=numpy.int64)
        for idx in range(len(param_arr)):
            commit_arr[idx] = self.commiter.commit(param_arr[idx])
        return commit_arr
    
    def abort(self, message: str):
        self.abort_message = message
        self.set_flag(self.FLAG.ABORT)

    def receive_trained_data(self, client_ID: int, data_number: int, signed_data_number: int, signed_parameters: int, parameters: numpy.ndarray[numpy.int64]) -> None:
        for client in self.client_list:
            if client.round_ID == client_ID:
                client.is_online = True
                client.set_trained_data(data_number, signed_data_number, signed_parameters, parameters)
                client.create_receipt(self.signer)
                return

    def get_receipt(self, client_ID: int) -> Receipt:
        for client in self.client_list:
            if client.round_ID == client_ID:
                return client.receipt

    def end_timer(self):
        self.timeout = True
        self.timeout_time = time.time()

    def start_timer(self, timeout_seconds: int = 60):
        self.timeout = False
        self.timer = threading.Timer(timeout_seconds, self.end_timer)
        self.timer.start()