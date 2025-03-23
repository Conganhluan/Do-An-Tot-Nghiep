from hashlib import sha256
from Crypto.Cipher import AES

class Helper:

    @staticmethod
    def PRNG(seed: int, num_bytes: int = 8):
        """
        Pseudo random generator using AES-CTR.
        ------
        Return a random integer of size `num_bytes`
        """
        key = sha256(str(seed).encode()).digest()[:16]
        cipher = AES.new(key, AES.MODE_CTR, nonce = key[:12])
        random_bytes = cipher.encrypt(b'\x00' * num_bytes)

        return int.from_bytes(random_bytes, "big")