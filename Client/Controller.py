import asyncio
from Manager import Manager
from Signer import Signer
from Helper import Helper

def controller_thread(manager: Manager, signer: Signer):

    async def register():

        # Default action, define reader/writer and remove the first 3 bytes (\xff\xfd\x18) from telnet server
        reader, writer = await asyncio.open_connection(Helper.get_env_variable("TRUSTED_PARTY_HOST"), Helper.get_env_variable("TRUSTED_PARTY_PORT"))
        _ = await reader.read(3)
        
        # Send requests to Trusted party
        writer.write(f"register_{'localhost'}_{manager.port}_{signer.get_public_key()}\n".encode("UTF-8"))
        
        # Get response
        result = await reader.readuntil()
        if result == b"Sucessfully\n":
            print("Register successfully!")
            writer.close()
        else:
            print(f"Server return: '{result}'")
            print("Client quit unexpectedly!")
            quit()

    # Register with Trusted Party
    asyncio.run(register())