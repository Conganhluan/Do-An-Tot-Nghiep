import asyncio
from Helper import Helper
from Manager import FL_Manager, Round_Manager, Client_info, DH_params

def controller_thread(FL_manager: FL_Manager):

    # Global variables
    round_manager = None

    # Request DH public key from chosen clients
    async def request_DH_public_key(client: Client_info, dh_params: DH_params):

        # Default action, define reader/writer and remove the first 3 bytes (\xff\xfd\x18) from telnet server
        reader, writer = await asyncio.open_connection(client.host, client.port)
        _ = await reader.read(3)

        # Send DH parameters
        writer.write(f"DH params_{dh_params.g}_{dh_params.q}\n".encode("utf-8"))

        # Get response
        result = await reader.readuntil()
        try:
            client.set_DH_public_key(int(result))
            print(f"Successfully get DH public keys from client {client.ID}")
        except:
            print(f"There is something wrong: Client {client.ID} returned {result} instead of DH public key")
        writer.close()

    # Send round information for each client
    async def send_round_information_to_client(client: Client_info, needed_information: dict):

        # Default action, define reader/writer and remove the first 3 bytes (\xff\xfd\x18) from telnet server
        reader, writer = await asyncio.open_connection(client.host, client.port)
        _ = await reader.read(3)

        # Send needed information
        writer.write(f"Round information_{needed_information["Round ID"]}_{len(needed_information["Neighbors"])}\n".encode("utf-8"))
        for neighbor in needed_information["Neighbors"]:
            writer.write(f"{neighbor[0]}_{neighbor[1]}_{neighbor[2]}_{neighbor[3]}\n".encode("utf-8"))

        # Get response
        result = await reader.readuntil()
        if result == b"Successfully\n":
            print(f"Send information to client {client.ID} successfully!")
        else:
            print(f"Client {client.ID} returned: '{result}'")
        writer.close()

    # Send signal of Round Initiation to Aggregator
    async def send_round_information_to_aggregator():

        # Default action, define reader/writer and remove the first 3 bytes (\xff\xfd\x18) from telnet server
        reader, writer = await asyncio.open_connection(FL_manager.aggregator_info.host, FL_manager.aggregator_info.port)
        _ = await reader.read(3)

        # Send initiation signal
        writer.write(f"Init the round_{len(round_manager.client_list)}_{len(round_manager.client_list[0].neighbor_list)}\n".encode("UTF-8"))
        
        for client in round_manager.client_list:
            writer.write(f"{client.round_ID}_{client.host}_{client.port}_{client.DH_public_key}_{client.RSA_pulic_key[0]}_{client.RSA_pulic_key[1]}\n".encode('UTF-8'))
            writer.write(f"{'_'.join([str(neighbor_round_ID) for neighbor_round_ID in client.neighbor_list])}\n".encode('UTF-8'))

        # Get response
        result = await reader.readuntil()
        if result == b"Successfully\n":
            print(f"Successfully send initiation signal to Aggregator!")
        else:
            print(f"Aggregator returned: '{result}'")
        writer.close()

    # Init a round
    async def init_round(round_manager: Round_Manager):

        for client in round_manager.client_list:
            dh_params = round_manager.get_DH_params()
            asyncio.create_task(request_DH_public_key(client, dh_params))
        all_remaining_tasks = asyncio.all_tasks()
        all_remaining_tasks.remove(asyncio.current_task())
        await asyncio.wait(all_remaining_tasks)

        for client in round_manager.client_list:
            needed_information = round_manager.get_needed_info_for_client(client.ID)
            asyncio.create_task(send_round_information_to_client(client, needed_information))
        asyncio.create_task(send_round_information_to_aggregator())

        all_remaining_tasks = asyncio.all_tasks()
        all_remaining_tasks.remove(asyncio.current_task())
        await asyncio.wait(all_remaining_tasks)

    # Get next command from stdinput
    while True:
        
        command = input()

        # Stop the trusted party
        if command in ("end", "quit", "exit"):
            print("Trusted party ends!")
            quit()
        
        # List the client that registered with trusted party
        elif "client" in command and "list" in command:
            if "round" in command:
                if not round_manager:
                    print("There is no training round initiated!")
                    continue
                print("Round attended client list:")
                for client in round_manager.client_list:
                    print(f"round ID: {client.round_ID}, DH public key: {client.DH_public_key}, neighbors: {client.neighbor_list}")
            else:
                print("Registed client list:")
                for client in FL_manager.client_list:
                    print(f"ID: {client.ID}, Address: {client.host}:{client.port}, RSA keys: {client.RSA_pulic_key}")

        # Init a new training round
        elif "init" in command and "round" in command:
            round_manager : Round_Manager = Round_Manager(FL_manager.choose_clients(Helper.get_env_variable('ATTEND_CLIENTS')), FL_manager.current_round)
            asyncio.run(init_round(round_manager))
