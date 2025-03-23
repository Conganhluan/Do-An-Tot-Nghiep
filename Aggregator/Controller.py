import asyncio
from Helper import Helper
from Manager import Manager
from time import sleep

def controller_thread(flag: str, manager: Manager):

    async def register():

        # Default action, define reader/writer and remove the first 3 bytes (\xff\xfd\x18) from telnet server
        reader, writer = await asyncio.open_connection(Helper.get_env_variable("TRUSTED_PARTY_HOST"), Helper.get_env_variable("TRUSTED_PARTY_PORT"))
        _ = await reader.read(3)
        
        # Send requests to Trusted party
        writer.write(f"aggregator_{manager.host}_{manager.port}\n".encode("UTF-8"))
        
        # Get response
        result = await reader.readuntil()
        processed_data = result.decode("utf-8").split("_")
        if processed_data[0] == "Successfully" and len(processed_data) == 4:
            commitment_params = tuple([int(param) for param in processed_data[1:]])
            manager.set_commitment_params(commitment_params)
            print("Register successfully!")
            writer.close()
        else:
            print(f"Trusted party returns '{result}'")
            print("Aggregator quit unexpectedly!")
            quit()

    # Register with Trusted Party
    asyncio.run(register())

    while True:

        if flag == "START_ROUND":
        
            print("Round started!")
            flag = "NONE"

        else:

            # Wait for the next flag
            sleep(10)

            # For debugging purpose
            command = input()
            if command == "next":
                continue
            elif command in ("quit", "exit", "stop"):
                quit()
            elif "round" in command and "info" in command:
                print("Attendee clients in round:")
                for client in manager.client_list:
                    print(f"{client.round_ID} - {client.host}:{client.port}, {client.neighbor_list}")
                    print(f"DH_public_key: {client.DH_public_key}")
                    print(f"RSA public key: e: {client.RSA_public_key[0]}, n: {client.RSA_public_key[1]}")
            elif "info" in command:
                print(f"Commitment params: {manager.commitment_params}")