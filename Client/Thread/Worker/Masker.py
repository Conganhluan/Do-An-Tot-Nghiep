from Thread.Worker.Helper import Helper
from Thread.Worker import Mask_Module
from random import randint
import numpy

class Masker:
    
    def __init__(self, g: int, q: int, secret_min_limit: int = 0, secret_max_limit: int = 10000000):
        self.g, self.q = g, q
        self.ss = randint(secret_min_limit, secret_max_limit)
        self.ps = randint(secret_min_limit, secret_max_limit)

    def get_DH_public_key(self) -> int:
        return Helper.exponent_modulo(self.g, self.ps, self.q)

    def get_PRNG_ss(self) -> int:
        return abs(Helper.PRNG(self.ss, 8))
    
    def get_PRNG_ps(self, self_ID: int, neighbor_ps: list[tuple[int, int]]) -> int:
        total = 0.0
        for neighbor_ID, neighbor_public_key in neighbor_ps:
            if neighbor_ID > self_ID:
                total += Helper.PRNG(Helper.exponent_modulo(neighbor_public_key, self.ps, self.q), 7)
            elif neighbor_ID < self_ID:
                total -= Helper.PRNG(Helper.exponent_modulo(neighbor_public_key, self.ps, self.q), 7)
            else:
                raise Exception("There is something wrong here!")
        return total
    
    def get_PRNG_gs(self, global_mask) -> int:
        return abs(Helper.PRNG(global_mask, 4))

    def __share_secret__(self, secret: int, neighbor_num: int, share_limit: int, coeff_limit: int) -> list[tuple[int, int]]:
        """
        Create a polynomial with the secret as free coefficient, then share points of it
        ------
        Return list of 'neighbor_num' number of (X, Y)
        """
        
        # Set the range for share_limit
        if share_limit <= 0:
            share_limit = neighbor_num//2 + 1
        elif share_limit <= neighbor_num//2:
            raise Exception("Share limit is not enough to prevent Aggregator playing 2 faces")
        if share_limit > 15:
            raise Exception("The value Y of the highest point is out of Int128, please lower the share limit")

        # Define random coefficients for the polynomial
        coeffs = [secret] + [randint(-coeff_limit, coeff_limit)*2+1 for i in range(share_limit-1)]

        # Get the smallest possible |x| without 0
        x_list = list(range(-neighbor_num//2-1, neighbor_num//2+3))
        x_list.remove(0)
        x_list = x_list[:neighbor_num]

        # Make point_list((x1,y1), (x2, y2))
        point_list = []
        for x in x_list:
            parameter = 1
            y = 0
            for i in range(share_limit):
                y += parameter*coeffs[i]
                parameter *= x
            point_list.append((x, y))
        
        # Detect errors if there is any
        if len(point_list) != neighbor_num:
            raise Exception("There aren't enough points to share with neighbors")

        return point_list
    
    def share_ss(self, neighbor_num: int, share_limit: int = 0, coeff_limit: int = 5) -> list[tuple[int, int]]:
        return self.__share_secret__(self.ss, neighbor_num, share_limit, coeff_limit)
    
    def share_ps(self, neighbor_num: int, share_limit: int = 0, coeff_limit: int = 5) -> list[tuple[int, int]]:
        return self.__share_secret__(self.ps, neighbor_num, share_limit, coeff_limit)

    def mask_params(self, params: numpy.ndarray[numpy.float32], global_mask: int, self_ID: int, neighbor_ps: list[tuple[int]]) -> numpy.ndarray[numpy.int64]:
        masked_params = numpy.zeros((len(params), ), dtype=numpy.int64)
        Mask_Module.get_masked(params, masked_params, self.get_PRNG_ss(), self.get_PRNG_ps(self_ID, neighbor_ps), self.get_PRNG_gs(global_mask))
        return masked_params
    
    def unmask_params(self, masked_params: numpy.ndarray[numpy.int64], global_mask: int) -> numpy.ndarray[numpy.float32]:
        unmasked_params = numpy.zeros((len(masked_params), ), dtype=numpy.float32)
        Mask_Module.get_unmasked(masked_params, unmasked_params, self.get_PRNG_gs())
        return unmasked_params