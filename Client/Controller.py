import asyncio
from Manager import Manager
from Helper import Helper
from Masker import Masker

def controller_thread(flag: str, manager: Manager):

    async def register():

        # Default action, define reader/writer and remove the first 3 bytes (\xff\xfd\x18) from telnet server
        reader, writer = await asyncio.open_connection(Helper.get_env_variable("TRUSTED_PARTY_HOST"), Helper.get_env_variable("TRUSTED_PARTY_PORT"))
        _ = await reader.read(3)
        
        # Send requests to Trusted party
        writer.write(f"register_{manager.host}_{manager.port}_{manager.signer.get_public_key()}\n".encode("UTF-8"))
        
        # Get response
        result = await reader.readuntil()
        processed_data = result.decode('utf-8').split("_")
        if processed_data[0] == "Successfully" and len(processed_data) == 6:
            aggregator_host = processed_data[1]
            aggregator_port = processed_data[2]
            commitment_params = tuple([int(param) for param in processed_data[3:]])
            manager.set_FL_public_params(aggregator_host, aggregator_port, commitment_params)
            print("Register successfully!")
            writer.close()
        else:
            print(f"Server return: '{result}'")
            print("Client quit unexpectedly!")
            quit()

    # Register with Trusted Party
    asyncio.run(register())

    # Debugging
    while True:

        command = input()

        if command in ('quit', "exit", "end", "stop"):
            print("Client ends!")
            quit()

        elif "info" in command and "round" in command:
            if manager.round_ID == None:
                print("There is no round initiated yet")
                continue
            print(f"ID: {manager.round_ID}")
            print("Neighbor list:")
            for neighbor in manager.neighbor_list:
                print(f"ID: {neighbor.round_ID} - {neighbor.host}:{neighbor.port}, DH public key: {neighbor.DH_public_key}")
        
        elif "info" in command and ("client" in command or "self" in command):
            print(f"Aggregator info - {manager.aggregator_info.host}:{manager.aggregator_info.port}")
            print(f"Commitment parameters: p: {manager.commitment_params.p}, h: {manager.commitment_params.h}, k: {manager.commitment_params.k}")
            print(f"RSA public key: {manager.signer.get_public_key()}")