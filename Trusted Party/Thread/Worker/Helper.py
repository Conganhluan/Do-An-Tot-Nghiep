from hashlib import sha256
from Crypto.Cipher import AES
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
    def build_graph(node_num: int, neighbor_num: int) -> dict[int: list]:
    
        # Please enhance the code to ensure there is no pair of nodes having more than or equal to 'limitation' same neighbors
        # limitation = neighbor_num//2

        if node_num % 2 and neighbor_num % 2:
            raise Exception(f"There is no graph available for {node_num} nodes and each node having {neighbor_num} neighbors!")

        neighbor_list : dict[int: list] = {}
        for i in range(node_num):
            neighbor_list[i] = []

        current_check_node = 0
        current_fill_node = 0
        done_check = 0

        # Not enough nodes having enough neighbors
        while done_check < node_num:

            # If current node is full of neighbors already then pass
            if len(neighbor_list[current_fill_node]) == neighbor_num:
                current_fill_node = (current_fill_node + 1) % node_num
                done_check += 1
                continue

            # Check continous nodes to pair new neighbors for current node
            current_check_node = current_fill_node
            while len(neighbor_list[current_fill_node]) != neighbor_num:
                
                # Check the next node
                current_check_node = (current_check_node + 1) % node_num

                # If check node = current node then pass
                if current_check_node == current_fill_node:
                    continue

                # If checked node is full of neighbors already then pass
                elif len(neighbor_list[current_check_node]) == neighbor_num:
                    continue

                neighbor_list[current_fill_node].append(current_check_node)
                neighbor_list[current_check_node].append(current_fill_node)

            current_fill_node = (current_check_node + 1) % node_num
            done_check = 1

        return neighbor_list
    
    @staticmethod
    def get_env_variable(name: str) -> int | str:
        return json.load(open("../.env", "r", encoding='UTF-8'))[name]
    
    @staticmethod
    async def send_data(writer: asyncio.StreamWriter | telnetlib3.TelnetWriter, data: str | bytes) -> None:
        
        if type(data) == str:
            data = data.encode()

        # Send data_len
        data_len = len(data)
        writer.write(f"{str(data_len)}\n".encode())
        await writer.drain()

        # Send data
        writer.write(data.replace(b'\xff', b'\xff\xff'))
        await writer.drain()

    @staticmethod
    async def receive_data(reader: asyncio.StreamReader | telnetlib3.TelnetReader) -> bytes:
        
        # Receive data_len
        data_len = await reader.readuntil()
        data_len = int(data_len)

        # Receive data
        data = await reader.readexactly(data_len)
        return data