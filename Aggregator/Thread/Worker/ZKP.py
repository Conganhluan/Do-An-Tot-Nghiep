import multiprocessing, time
import pysnark.runtime
from Thread.Worker.Manager import Manager, Client_info
from Thread.Worker.Helper import Helper


pysnark.runtime.bitlength = 64

def create_ZKP(manager: Manager):

    # Information preparation
    the_client_list : list[Client_info] = sorted(manager.client_list, key=lambda client:client.round_ID)

    client_num = len(the_client_list)
    neighbor_num = len(the_client_list[0].neighbor_list)
    parameter_num = len(the_client_list[0].local_parameters)

    client_masked_params = [[int(param) for param in client.local_parameters] for client in the_client_list]
    client_committed_params = [[int(param) for param in client.committed_parameters] for client in the_client_list]
    client_local_r = [client.local_r for client in the_client_list]
    client_public_keys = [(client.RSA_public_key.e, client.RSA_public_key.n) for client in the_client_list]
    client_points = [[(point.x, point.y) for point in client.secret_points] for client in the_client_list]
    client_point_num = [len(points) for points in client_points]
    client_availibility = [1 if client.is_online else 0 for client in the_client_list]
    client_local_num = [client.local_datanum for client in the_client_list]
    total_parameters = [0 for _ in range(parameter_num)]

    @pysnark.runtime.snark
    def ZKP_exponent_modulo(base: int, exponent: int, modulo: int) -> int:
        result = 1
        while exponent.value > 0: 
            if exponent.value % 2:
                base, exponent, result = (base * base) % modulo, exponent // 2, (base * result) % modulo
            else:
                base, exponent, result = (base * base) % modulo, exponent // 2, result
        return result

    def check_each_param(shared_resouces, h, p, secret_commit, masked_param, committed_param):
        (ZKP_exponent_modulo(h, masked_param, p) * secret_commit) % p - committed_param
        shared_resouces.value += 1

    def check_each_client(shared_resouces, h, k, r, p, parameter_num, client_masked_params, client_committed_params, client_idx):
        secret_commit = ZKP_exponent_modulo(k, r, p)
        threads: list[multiprocessing.Process] = list()
        for param_idx in range(parameter_num):
            threads.append(multiprocessing.Process(target=check_each_param, args= (shared_resouces, h, p, secret_commit, client_masked_params[param_idx], client_committed_params[param_idx], )))
            threads[param_idx].start()
        for param_idx in range(parameter_num):
            threads[param_idx].join()

    # Calculate the secrets
    @Helper.timing
    def ZKP(h, k, p,
            client_num, neighbor_num, parameter_num, client_local_r, client_local_num,
            client_point_num, client_availibility, client_public_keys,
            client_masked_params, client_committed_params, 
            client_points):
        
        shared_resouces = multiprocessing.Value('i', 0)
        total_parameter_num = client_num * parameter_num

        threads: list[multiprocessing.Process] = list()
        for client_idx in range(client_num):
            threads.append(multiprocessing.Process(target=check_each_client, args=(shared_resouces, h, k, client_local_r[client_idx], p, parameter_num, client_masked_params[client_idx], client_committed_params[client_idx], client_idx, )))
            threads[client_idx].start()
        time_started = time.time()
        while multiprocessing.active_children():
            print(f"There are {shared_resouces.value}/{total_parameter_num} parameters checked\tTime elapsed: {time.time() - time_started} seconds")
            time.sleep(1.5)

    ZKP(manager.commiter.h, manager.commiter.k, manager.commiter.p, 
        client_num, neighbor_num, parameter_num, client_local_r, client_local_num,
        client_point_num, client_availibility, client_public_keys,
        client_masked_params, client_committed_params,
        client_points)