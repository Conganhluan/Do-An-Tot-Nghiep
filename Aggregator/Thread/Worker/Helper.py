from hashlib import sha256
from Crypto.Cipher import AES
from scipy.interpolate import lagrange
import json, time, random, asyncio, telnetlib3
from socket import socket, AF_INET, SOCK_STREAM

class Helper:
    
    @staticmethod
    def timing(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            print(f"Function {func.__name__} executed in {end_time - start_time:.6} seconds")
            return result
        return wrapper

    @staticmethod
    def exponent_modulo(base: int, exponent: int, modulo: int) -> int:
        if modulo == 1:
            return 0
        
        result = 1
        while exponent > 0: 
            if exponent % 2:
                base, exponent, result = (base * base) % modulo, exponent // 2, (base * result) % modulo
            else:
                base, exponent, result = (base * base) % modulo, exponent // 2, result
        return result

    @staticmethod
    def get_polynomial(point_list: list[tuple[int, int]]) -> tuple[int]:
        X, Y = [], []
        for x, y in point_list:
            X.append(x)
            Y.append(y)
        return tuple([int(coeff) for coeff in lagrange(X, Y).coefficients.round()])
    
    @staticmethod
    def PRNG(seed: int, num_bytes: int):
        key = sha256(str(seed).encode()).digest()[:16]
        cipher = AES.new(key, AES.MODE_CTR, nonce = key[:12])
        random_bytes = cipher.encrypt(b'\x00' * num_bytes)
        return int.from_bytes(random_bytes, "big")

    @staticmethod
    def get_env_variable(name: str) -> int | str:
        return json.load(open("../.env", "r", encoding='UTF-8'))[name]

    @staticmethod
    def get_available_port() -> int:
        while True:
            port = random.randint(30000, 60000)
            if socket(AF_INET, SOCK_STREAM).connect_ex(('localhost', port)):
                return port
            
    @staticmethod
    async def send_data(writer: asyncio.StreamWriter | telnetlib3.TelnetWriter, data: str | bytes, chunk_size: int = 4096) -> None:
        if type(data) == str:
            data = data.encode()
        try:
            assert type(data) == bytes
        except:
            print(f"The data to send have abnormal type! - {type(data)}")
            print(data)
        data_len = len(data)
        start_idx = 0
        while start_idx < data_len:
            writer.write(data[start_idx: start_idx + chunk_size].replace(b'\xff', b'\xff\xff') + b'|||||')
            start_idx += chunk_size
            await writer.drain()
        writer.write(b'|||||')

    @staticmethod
    async def receive_data(reader: asyncio.StreamReader | telnetlib3.TelnetReader) -> bytes:
        data = b''
        while True:
            receiv = await reader.readuntil(b'|||||')
            # print(receiv)
            if receiv == b'|||||':
                return data
            data += receiv.removesuffix(b'|||||').replace(b'\xff\xff', b'\xff')