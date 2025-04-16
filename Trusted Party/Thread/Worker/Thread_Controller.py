import asyncio, struct
from Thread.Worker.Helper import Helper
from Thread.Worker.Manager import Manager, Client_info, DH_params


# Aggregator/Client aborts the process due to abnormal activities
async def send_STOP(manager: Manager):

    # STOP <message>
    if not manager.stop_message:
        manager.stop_message = "No message specified"

    for client in manager.client_list:
        reader, writer = await asyncio.open_connection(client.host, client.port)
        _ = await reader.read(3)  # Remove first 3 bytes of Telnet command
        await Helper.send_data(writer, f"STOP {manager.current_round} {manager.stop_message}")
        writer.close()

    reader, writer = await asyncio.open_connection(manager.aggregator_info.host, manager.aggregator_info.port)
    _ = await reader.read(3)  # Remove first 3 bytes of Telnet command
    await Helper.send_data(writer, f"STOP {manager.current_round} {manager.stop_message}")
    writer.close()



###########################################################################################################



# Trusted Party gets DH public keys from chosen Clients
async def send_DH_PARAM_each(manager: Manager, client: Client_info, dh_params: DH_params):

    reader, writer = await asyncio.open_connection(client.host, client.port)
    _ = await reader.read(3)  # Remove first 3 bytes of Telnet command
    
    # DH_PARAM <g> <q>
    data = f'DH_PARAM {dh_params.g} {dh_params.q}'
    await Helper.send_data(writer, data)
    # print(f"Send DH public parameters to client {client.ID} (round ID: {client.round_ID})...")
    
    # <client_DH_public_key>
    data = await Helper.receive_data(reader)
    manager.round_manager.set_DH_public_key(client.ID, int(data))
    # print(f"Confirm to get DH public key from client {client.ID} (round ID: {client.round_ID})")

    # SUCCESS
    await Helper.send_data(writer, "SUCCESS")
    print(f"Successfully get DH public key from client {client.ID} (round ID: {client.round_ID})")
    writer.close()

async def send_DH_PARAM(manager: Manager):

    dh_params = manager.round_manager.get_DH_params()
    for client in manager.round_manager.client_list:
        asyncio.create_task(send_DH_PARAM_each(manager, client, dh_params))
    all_remaining_tasks = asyncio.all_tasks()
    all_remaining_tasks.remove(asyncio.current_task())
    await asyncio.wait(all_remaining_tasks)



###########################################################################################################



# Trusted Party sends round information to Clients
async def send_ROUND_INFO_client_each(manager: Manager, client: Client_info):

    reader, writer = await asyncio.open_connection(client.host, client.port)
    _ = await reader.read(3)  # Remove first 3 bytes of Telnet command

    # ROUND_INFO <round_number> <client_round_ID> <neighbor_num> 
    data = f'ROUND_INFO {manager.round_manager.round_number} {client.round_ID} {len(client.neighbor_list)}'
    await Helper.send_data(writer, data)

    # <base_model_commit/previous_global_model_commit>
    # data = manager.last_commitment.tobytes()
    # await Helper.send_data(writer, data)

    for neighbor_info in manager.round_manager.get_neighbor_information(client.ID):
        
        # <neighbor_round_ID> <neighbor_host> <neighbor_port> <neighbor_DH_public_key>
        data = f"{' '.join([str(info) for info in neighbor_info])}"
        await Helper.send_data(writer, data)
    
    # SUCCESS
    data = await Helper.receive_data(reader)
    if data == b"SUCCESS":
        print(f"Successfully send round information to client {client.round_ID}")
    else:
        print(f"Client {client.round_ID} returns {data}")
    writer.close()

async def send_ROUND_INFO_client(manager: Manager):

    for client in manager.round_manager.client_list:
        asyncio.create_task(send_ROUND_INFO_client_each(manager, client))
    all_remaining_tasks = asyncio.all_tasks()
    all_remaining_tasks.remove(asyncio.current_task())
    await asyncio.wait(all_remaining_tasks)



###########################################################################################################



# Trusted Party sends round information to Aggregator
async def send_ROUND_INFO_aggregator(manager: Manager):

    reader, writer = await asyncio.open_connection(manager.aggregator_info.host, manager.aggregator_info.port)
    _ = await reader.read(3)  # Remove first 3 bytes of Telnet command

    # ROUND_INFO <round_number> <client_num> <q>
    data = f"ROUND_INFO {manager.round_manager.round_number} {len(manager.round_manager.client_list)} {manager.round_manager.dh_params.q}"
    await Helper.send_data(writer, data)

    for client in manager.round_manager.client_list:

        # <client_round_ID> <client_host> <client_port> <client_DH_public_key> <client_RSA_public_key>
        data = f"{client.round_ID} {client.host} {client.port} {client.DH_public_key} {client.RSA_public_key.e} {client.RSA_public_key.n}"
        await Helper.send_data(writer, data)

        # <client_neighbor_round_ID_1> <client_neighbor_round_ID_2> ... <client_neighbor_round_ID_n>
        data = " ".join([str(round_ID) for round_ID in client.neighbor_list])
        await Helper.send_data(writer, data)
    
    # SUCCESS
    data = await Helper.receive_data(reader)
    if data == b"SUCCESS":
        print(f"Successfully send round information to the Aggregator")
    else:
        print(f"Aggregator returns {data}")
    writer.close()