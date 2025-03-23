from hashlib import sha256
from Crypto.Cipher import AES
from json import load

class Helper:

    @staticmethod
    def exponent_modulo(b: int, e: int, m: int) -> int:
        """
        Fast exponent modulo function
        -------
        Return b^e mod m
        """
        if m == 1:
            return 0
        
        result = 1
        while e > 0:
            if e % 2:
                b, e, result = (b * b) % m, e // 2, (b * result) % m
            else:
                b, e, result = (b * b) % m, e // 2, result
        return result
    
    @staticmethod
    def PRNG(seed: int, num_bytes: int):
        """
        Pseudo random generator using AES-CTR.
        ------
        Return a random integer of size `num_bytes`
        """
        key = sha256(str(seed).encode()).digest()[:16]
        cipher = AES.new(key, AES.MODE_CTR, nonce = key[:12])
        random_bytes = cipher.encrypt(b'\x00' * num_bytes)

        return int.from_bytes(random_bytes, "big")
    
    @staticmethod
    def get_env_variable(name: str) -> int | str:
        return load(open("../.env", "r", encoding='UTF-8'))[name]