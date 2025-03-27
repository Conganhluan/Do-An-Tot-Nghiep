import asyncio, dill as pickle, struct
from Thread.Worker.Helper import Helper
from Thread.Worker.Manager import Manager, Client_info, Commiter
from Thread.Worker.BaseModel import *

TRUSTED_PARTY_HOST = Helper.get_env_variable("TRUSTED_PARTY_HOST")
TRUSTED_PARTY_PORT = Helper.get_env_variable("TRUSTED_PARTY_PORT")

# Aggregator registers itself with Trusted Party
async def send_AGG_REGIS(manager: Manager):

    reader, writer = await asyncio.open_connection(TRUSTED_PARTY_HOST, TRUSTED_PARTY_PORT)
    _ = await reader.read(3)  # Remove first 3 bytes of Telnet command
    
    # AGG_REGIS <aggregator_host> <aggregator_port> <base_model_class>
    data = f'AGG_REGIS {manager.host} {manager.port} '.encode() + pickle.dumps(manager.model_type)
    await Helper.send_data(writer, data)
    print(f"Send self registration to the Trusted party...")
    
    # <commiter>
    data = await Helper.receive_data(reader)
    commiter = Commiter(tuple([int(param) for param in data.split(b' ')]))
    manager.set_commiter(commiter)
    manager.commiter.gen_new_secret()
    print(f"Confirm to get the commiter from the Trusted party")

    # <base_model_commit>
    data = b''.join([struct.pack('Q', param) for param in manager.get_model_commit()])
    await Helper.send_data(writer, data)
    print(f"Send base model commitment to the Trusted party...")

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

    # GLOB_MODEL <r>
    data = f"GLOB_MODEL {manager.commiter.get_secret()}"
    await Helper.send_data(writer, data)

    # <global_model_parameters>
    data = b''.join(struct.pack('d', param) for param in manager.get_model_parameters())
    await Helper.send_data(writer, data)

    # SUCCESS
    data = await Helper.receive_data(reader)
    if data == b"SUCCESS":
        print(f"Successfully send global model to client {client.round_ID}")
    else:
        print(f"Client {client.round_ID} returns {data}")
    writer.close()

async def send_GLOB_MODEL(manager: Manager):

    for client in manager.client_list:
        asyncio.create_task(send_GLOB_MODEL_each(manager, client))
    all_remaining_tasks = asyncio.all_tasks()
    all_remaining_tasks.remove(asyncio.current_task())
    await asyncio.wait(all_remaining_tasks)



###########################################################################################################



# Aggregator/Client aborts the process due to abnormal activities
async def send_ABORT(message: str):

    reader, writer = await asyncio.open_connection(TRUSTED_PARTY_HOST, TRUSTED_PARTY_PORT)
    _ = await reader.read(3)  # Remove first 3 bytes of Telnet command

    # ABORT <message>
    await Helper.send_data(writer, message)
    writer.close()  