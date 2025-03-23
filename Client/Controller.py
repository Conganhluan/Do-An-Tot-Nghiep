import asyncio
from Manager import Manager
from Signer import Signer
from Helper import Helper
from Masker import Masker

def controller_thread(flag: str, manager: Manager, signer: Signer):

    async def register():

        # Default action, define reader/writer and remove the first 3 bytes (\xff\xfd\x18) from telnet server
        reader, writer = await asyncio.open_connection(Helper.get_env_variable("TRUSTED_PARTY_HOST"), Helper.get_env_variable("TRUSTED_PARTY_PORT"))
        _ = await reader.read(3)
        
        # Send requests to Trusted party
        writer.write(f"register_{'localhost'}_{manager.port}_{signer.get_public_key()}\n".encode("UTF-8"))
        
        # Get response
        result = await reader.readuntil()
        if result == b"Successfully\n":
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
        if command == "round information":
            print(f"ID: {manager.round_ID}")
            print("Neighbor list:")
            for neighbor in manager.neighbor_list:
                print(f"ID: {neighbor.round_ID} - {neighbor.host}:{neighbor.port}, DH public key: {neighbor.DH_public_key}")