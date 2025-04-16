import asyncio, dill as pickle
from Thread.Worker.Helper import Helper
from Thread.Worker.Manager import Manager, Client_info
from Thread.Worker.BaseModel import *

TRUSTED_PARTY_HOST = Helper.get_env_variable("TRUSTED_PARTY_HOST")
TRUSTED_PARTY_PORT = Helper.get_env_variable("TRUSTED_PARTY_PORT")

# Aggregator registers itself with Trusted Party
async def send_AGG_REGIS(manager: Manager):

    reader, writer = await asyncio.open_connection(TRUSTED_PARTY_HOST, TRUSTED_PARTY_PORT)
    _ = await reader.read(3)  # Remove first 3 bytes of Telnet command
    
    # AGG_REGIS <aggregator_host> <aggregator_port> <aggregator RSA_public_key> <base_model_class>
    data = f'AGG_REGIS {manager.host} {manager.port} {manager.signer.e} {manager.signer.n} '.encode() + pickle.dumps(manager.model_type)
    await Helper.send_data(writer, data)
    # print(f"Send self registration to the Trusted party...")
    
    # <commiter>
    # data = await Helper.receive_data(reader)
    # commiter = Commiter(tuple([int(param) for param in data.split(b' ')]))
    # manager.set_commiter(commiter)
    # manager.commiter.gen_new_secret()
    # print(f"Confirm to get the commiter from the Trusted party")

    # # <base_model_commit>
    # data = manager.get_global_commit().tobytes()
    # await Helper.send_data(writer, data)
    # print(f"Send base model commitment to the Trusted party...")

    # SUCCESS
    data = await Helper.receive_data(reader)
    if data == b"SUCCESS":
        print("Successfully register with the Trusted party")
    else:
        print(f"Trusted party returns {data}")
    writer.close()



###########################################################################################################



# Aggregator sends global model to Clients
async def send_GLOB_MODEL_each(manager: Manager, client: Client_info):

    reader, writer = await asyncio.open_connection(client.host, client.port)
    _ = await reader.read(3)  # Remove first 3 bytes of Telnet command

    # GLOB_MODEL header (without commiter data)
    data = f"GLOB_MODEL"
    await Helper.send_data(writer, data)

    # <global_model_parameters>
    data = manager.get_global_parameters().tobytes()
    await Helper.send_data(writer, data)

    # SUCCESS
    data = await Helper.receive_data(reader)
    if data == b"SUCCESS":
        print(f"Successfully send global model to client {client.round_ID}")
    else:
        print(f"Client {client.round_ID} returns {data}")
    writer.close()

async def send_GLOB_MODEL(manager: Manager):
    print("đợi xíu, đang tải mô hình!!!")
    for client in manager.client_list:
        asyncio.create_task(send_GLOB_MODEL_each(manager, client))
    all_remaining_tasks = asyncio.all_tasks()
    all_remaining_tasks.remove(asyncio.current_task())
    await asyncio.wait(all_remaining_tasks)



###########################################################################################################



# Aggregator gets secrets points from Clients
async def send_STATUS_each(manager: Manager, client: Client_info, status_list: list[bool]):

    reader, writer = await asyncio.open_connection(client.host, client.port)
    _ = await reader.read(3)  # Remove first 3 bytes of Telnet command

    # STATUS <neighbor_num>
    data = f"STATUS {len(client.neighbor_list)}"
    await Helper.send_data(writer, data)

    for neighbor_ID in client.neighbor_list:
    
        # <neighbor_round_ID> <ON/OFF>
        sent_data = f"{neighbor_ID} {"ON" if status_list[neighbor_ID] else "OFF"}"
        await Helper.send_data(writer, sent_data)
        print(f"Send client {neighbor_ID} status to client {client.round_ID}")

        # <SS_point_X/PS_point_X> <signature> <SS_point_Y/PS_point_Y> <signature>
        receiv_data = await Helper.receive_data(reader)
        x_point, x_point_signature, y_point, y_point_signature = [int(number) for number in receiv_data.split(b' ')]
        
        if not client.check_signature(x_point, x_point_signature) or not client.check_signature(y_point, y_point_signature):
            manager.abort(f"There is something wrong with the points from client {client.round_ID}")
        else:
            manager.get_client_by_ID(neighbor_ID).add_secret_points(x_point, y_point, x_point_signature, y_point_signature, client.round_ID)

    # SUCCESS
    await Helper.send_data(writer, "SUCCESS")
    print(f"Successfully receive neighbor secret points from client {client.round_ID}")

async def send_STATUS(manager: Manager):

    status_list = list()
    for i in range(len(manager.client_list)):
        status_list.append((None, False))
    for client in manager.client_list:
        status_list[client.round_ID] = client.is_online

    for client in manager.client_list:
        asyncio.create_task(send_STATUS_each(manager, client, status_list))
    all_remaining_tasks = asyncio.all_tasks()
    all_remaining_tasks.remove(asyncio.current_task())
    await asyncio.wait(all_remaining_tasks)



###########################################################################################################



# Aggregator/Client aborts the process due to abnormal activities
async def send_ABORT(message: str):

    reader, writer = await asyncio.open_connection(TRUSTED_PARTY_HOST, TRUSTED_PARTY_PORT)
    _ = await reader.read(3)  # Remove first 3 bytes of Telnet command

    # ABORT <message>
    await Helper.send_data(writer, "ABORT " + message)
    writer.close()  



###########################################################################################################



# Aggregator sends aggregated global model to Clients
async def send_AGG_MODEL_each(manager: Manager, client: Client_info):

    reader, writer = await asyncio.open_connection(client.host, client.port)
    _ = await reader.read(3)  # Remove first 3 bytes of Telnet command

    # AGG_MODEL header
    data = f"AGG_MODEL"
    await Helper.send_data(writer, data)

    # <global_parameters>
    data = manager.global_parameters.tobytes()
    await Helper.send_data(writer, data)

    # SUCCESS
    data = await Helper.receive_data(reader)
    if data == b"SUCCESS":
        print(f"Successfully send aggregation result to client {client.round_ID}")
    else:
        print(f"Client {client.round_ID} returns {data}")
    writer.close()

async def send_AGG_MODEL(manager: Manager):

    for client in manager.client_list:
        asyncio.create_task(send_AGG_MODEL_each(manager, client))
    all_remaining_tasks = asyncio.all_tasks()
    all_remaining_tasks.remove(asyncio.current_task())
    await asyncio.wait(all_remaining_tasks)