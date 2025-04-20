from pysnark.runtime import snark
import pysnark.runtime
from Thread.Worker.Manager import Manager

#pysnark.runtime.bitlength = 32

def create_ZKP(manager: Manager):

    # Information preparation
    client_num = len(manager.client_list)
    neighbor_num = len(manager.client_list[0].neighbor_list)
    parameter_num = len(manager.global_parameters)
    client_public_keys = [(client.RSA_public_key.e, client.RSA_public_key.n) for client in manager.client_list]

    # Round information
    @snark
    def add_round_information_into_public_inputs(client_num, neighbor_num):
        pass

    # Verify the signatures

        # The local model parameters

        # The secret points

    # Calculate the secrets

    # Aggregate

    # Create commit