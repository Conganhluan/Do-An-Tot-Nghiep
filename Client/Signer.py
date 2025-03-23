from random import randint
from Helper import Helper

class Signer:

    def __init__(self):
        RSA_key_list = open("RSA_keys.csv", "r", encoding='UTF-8').readlines()[1:]
        chosen_RSA_key = RSA_key_list[randint(0,99)].split(', ')
        self.d = int(chosen_RSA_key[1])
        self.e = int(chosen_RSA_key[2])
        self.n = int(chosen_RSA_key[3])

    def get_public_key(self):
        return f"{self.e}_{self.n}"

    def sign(self, data: int):
        return Helper.exponent_modulo(data, self.e, self.n)