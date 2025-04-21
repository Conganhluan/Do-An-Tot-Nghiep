from tqdm import tqdm
import pysnark.runtime
from Thread.Worker.Manager import Manager, Client_info
from Thread.Worker.Helper import Helper


pysnark.runtime.bitlength = 16

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

    def ZKP_exponent_modulo(base: int, exponent: int, modulo: int) -> int:
        result = 1
        while exponent.value > 0: 
            if exponent.value % 2:
                base, exponent, result = (base * base) % modulo, exponent // 2, (base * result) % modulo
            else:
                base, exponent, result = (base * base) % modulo, exponent // 2, result
        return result

    # Calculate the secrets
    @pysnark.runtime.snark
    @Helper.timing
    def ZKP(h, k, p,
            client_num, neighbor_num, parameter_num, client_local_r, client_local_num,
            client_point_num, client_availibility, client_public_keys,
            client_masked_params, client_committed_params, 
            client_points):
        total_check = 0

        # Check committed information received from client
        for idx in tqdm(range(client_num.value), unit=" client"):
            secret_commit = ZKP_exponent_modulo(k, client_local_r[idx], p)
            for param_idx in tqdm(range(parameter_num.value), leave=False, unit=" param"):
                total_check += (ZKP_exponent_modulo(h, client_masked_params[idx][param_idx], p) * secret_commit) % p - client_committed_params[idx][param_idx]
        return total_check
    
    ZKP(manager.commiter.h, manager.commiter.k, manager.commiter.p, 
        client_num, neighbor_num, parameter_num, client_local_r, client_local_num,
        client_point_num, client_availibility, client_public_keys,
        client_masked_params, client_committed_params,
        client_points)