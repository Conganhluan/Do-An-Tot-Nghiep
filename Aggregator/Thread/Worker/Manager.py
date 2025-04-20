from Thread.Worker.BaseModel import *
import random, numpy, time, struct, threading
from Thread.Worker.Helper import Helper
from Thread.Worker.Unmasker import Unmasker
from Thread.Worker import Unmask_Module
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

class Secret_Point:

    def __init__(self, x: int, y: int, x_signed: int, y_signed: int, neighbor_ID: int):
        self.x = x
        self.y = y
        self.x_signed = x_signed
        self.y_signed = y_signed
        self.neighbor_ID = neighbor_ID

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
        self.secret_points = list()
        self.receipt = None

        # Aggregation
        self.ss = 0
        self.ps = 0
        self.unmasked_parameters : numpy.ndarray[numpy.int64] | int = None
    
    def set_trained_data(self, data_number: int, signed_data_number: int, signed_parameters: int, parameters: numpy.ndarray[numpy.int64]) -> None:
        self.local_datanum = data_number
        self.signed_datanum = signed_data_number
        self.signed_parameters = signed_parameters
        self.local_parameters = parameters

    def create_receipt(self, signer: Signer):
        received_time = time.time()
        received_data = int.from_bytes(struct.pack('f', received_time) + self.local_datanum.to_bytes(5) + self.local_parameters.tobytes())
        self.receipt = Receipt(received_time, signer.sign(received_data))

    def add_secret_points(self, x: int, y: int, x_signed: int, y_signed: int, neighbor_ID: int) -> None:
        self.secret_points.append(Secret_Point(x, y, x_signed, y_signed, neighbor_ID))

    def check_signature(self, data: int, signature: int) -> None:
        return Helper.exponent_modulo(signature, self.RSA_public_key.e, self.RSA_public_key.n) == data % self.RSA_public_key.n

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

    def commit(self, data: int | float) -> numpy.uint64:
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
        class AGGREGATE:
            # Used to indicate that not to receive any local model from clients
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
        self.received_data = 0
            # Aggregator
        self.global_model : CNNModel_MNIST | None = model_type()
        self.model_type = model_type
        self.global_parameters = None
        
        # Round parameters
        self.client_list = None
        self.q = 0
    
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

    def set_commiter(self, commiter: Commiter) -> None:
        self.commiter = commiter

    def get_global_model_parameters(self) -> numpy.ndarray[numpy.float32]:
        return parameters_to_vector(self.global_model.parameters()).detach().numpy()

    def get_global_commit(self, param_arr: numpy.ndarray[numpy.uint64 | numpy.float32]) -> numpy.ndarray[numpy.uint64]:
        commit_arr = numpy.zeros((len(param_arr), ), dtype=numpy.uint64)
        for idx in range(len(param_arr)):
            commit_arr[idx] = self.commiter.commit(param_arr[idx])
        return commit_arr
    
    def abort(self, message: str):
        self.abort_message = message
        self.set_flag(self.FLAG.ABORT)

    def get_client_by_ID(self, client_ID: int) -> Client_info:
        for client in self.client_list:
            if client.round_ID == client_ID:
                return client

    def receive_trained_data(self, client: Client_info, data_number: int, signed_data_number: int, signed_parameters: int, parameters: numpy.ndarray[numpy.int64]) -> None:
        client.is_online = True
        client.set_trained_data(data_number, signed_data_number, signed_parameters, parameters)
        client.create_receipt(self.signer)

    def get_receipt(self, client: Client_info) -> Receipt:
        return client.receipt

    def end_timer(self):
        self.timeout = True
        self.timeout_time = time.time()
        self.set_flag(self.FLAG.AGGREGATE)
        self.checker = None

    def the_checker(self):
        while True:
            if self.timeout:
                return
            elif self.received_data == len(self.client_list):
                print("There are enough clients sending their data")
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
            
    @Helper.timing
    def aggregate(self) -> None:
        
        total_parameters = [0 for _ in range(len(self.client_list[0].local_parameters))]

        for client in self.client_list:
            
            if client.is_online:
                client.ss = Unmasker.get_secret([(point.x, point.y) for point in client.secret_points])
                client.unmasked_parameters = numpy.zeros((len(client.local_parameters),), dtype=numpy.int64)
                Unmask_Module.unmask_ss(client.local_parameters, client.unmasked_parameters, Unmasker.get_PRNG_ss(client.ss))

                for idx in range(len(total_parameters)):
                    total_parameters[idx] += int(client.unmasked_parameters[idx])

            else:
                client.ps = Unmasker.get_secret([(point.x, point.y) for point in client.secret_points])
                neighbor_list = list()
                for neighbor_ID in client.neighbor_list:
                    neighbor_list.append((neighbor_ID, self.get_client_by_ID(neighbor_ID).DH_public_key))
                client.unmasked_parameters = Unmasker.get_PRNG_ps(client.round_ID, client.ps, self.q, neighbor_list) >> 1

                for idx in range(len(total_parameters)):
                    total_parameters[idx] += client.unmasked_parameters

        total_data_num = sum([client.local_datanum for client in self.client_list if client.is_online])
        self.global_parameters = numpy.array([param//total_data_num for param in total_parameters], dtype=numpy.int64)
        self.global_model = None