import asyncio, dill as pickle, time
from Thread.Worker.Helper import Helper
from Thread.Worker.Manager import Manager, Client_info, RSA_public_key

TRUSTED_PARTY_HOST = Helper.get_env_variable("TRUSTED_PARTY_HOST")
TRUSTED_PARTY_PORT = Helper.get_env_variable("TRUSTED_PARTY_PORT")

# Client registers itself with Trusted Party
async def send_CLIENT(manager: Manager):

    reader, writer = await asyncio.open_connection(TRUSTED_PARTY_HOST, TRUSTED_PARTY_PORT)
    _ = await reader.read(3)  # Remove first 3 bytes of Telnet command
    
    # CLIENT <client_host> <client_port> <client RSA_public_key>
    data = f'CLIENT {manager.host} {manager.port} {manager.signer.e} {manager.signer.n}'
    await Helper.send_data(writer, data)
    
    # <aggregator_host> <aggregator_port> <aggregator RSA_public_key> <gs_mask>
    data = await Helper.receive_data(reader)
    host, port, e, n, gs_mask = data.split(b' ', 4)  # Fixed: Only expecting 5 items now
    host = host.decode()
    port, gs_mask = int(port), int(gs_mask)
    public_key = RSA_public_key(int(e), int(n))
    # commiter = Commiter(tuple([int(param) for param in [p, h, k]]))

    # <base_model_class>
    data = await Helper.receive_data(reader)
    base_model_class = pickle.loads(data)
    manager.set_FL_public_params(host, port, public_key, gs_mask, base_model_class)

    # SUCCESS
    await Helper.send_data(writer, "SUCCESS")
    print("Successfully register with the Trusted party")
    writer.close()



###########################################################################################################



# Aggregator/Client aborts the process due to abnormal activities
async def send_ABORT(message: str):

    reader, writer = await asyncio.open_connection(TRUSTED_PARTY_HOST, TRUSTED_PARTY_PORT)
    _ = await reader.read(3)  # Remove first 3 bytes of Telnet command

    # ABORT <message>
    await Helper.send_data(writer, "ABORT " + message)
    writer.close()



###########################################################################################################



# Client sends secret points to its neighbors
async def send_POINTS_each(manager: Manager, neighbor: Client_info, points: tuple[tuple[int, int], tuple[int, int]]):

    reader, writer = await asyncio.open_connection(neighbor.host, neighbor.port)
    _ = await reader.read(3)  # Remove first 3 bytes of Telnet command

    # POINTS <SS_point_X> <SS_point_Y> <PS_point_X> <PS_point_Y>
    data = f"POINTS {manager.round_ID} {points[0][0]} {points[0][1]} {points[1][0]} {points[1][1]}"
    await Helper.send_data(writer, data)

    # SUCCESS
    data = await Helper.receive_data(reader)
    if data == b"SUCCESS":
        print(f"Successfully share secret points with client {neighbor.round_ID}")
    else:
        print(f"Trusted party returns {data}")
    writer.close()

async def send_POINTS(manager: Manager):

    for neighbor, secret_points in zip(manager.neighbor_list, manager.get_secret_points()):
        asyncio.create_task(send_POINTS_each(manager, neighbor, secret_points))
    all_remaining_tasks = asyncio.all_tasks()
    all_remaining_tasks.remove(asyncio.current_task())
    await asyncio.wait(all_remaining_tasks)



###########################################################################################################



async def send_LOCAL_MODEL(manager: Manager):

    reader, writer = await asyncio.open_connection(manager.aggregator_info.host, manager.aggregator_info.port)
    _ = await reader.read(3)  # Remove first 3 bytes of Telnet command

    # LOCAL_MODEL <round_ID> <data_number> <data_num_signature> <parameters_signature>
    data = f"LOCAL_MODEL {manager.round_ID} {manager.trainer.data_num} {manager.get_signed_data_num()} {manager.get_signed_parameters()}"
    await Helper.send_data(writer, data)

    # print("Send local model information")

    # <local_model_parameters>
    data = manager.get_masked_model().tobytes()
    await Helper.send_data(writer, data)

    # print("Send local model parameters")

    # SUCCESS <received_time> <signed_received_data>
    data = await Helper.receive_data(reader)
    if data[:7] == b"SUCCESS":
        received_time, signed_received_data = data[8:].split(b' ', 1)
        received_time = float(received_time)
        signed_received_data = int(signed_received_data)
        manager.set_receipt_from_Aggregator(received_time, signed_received_data)

        # print("Check receipt")
        if not manager.check_recept():
            manager.abort("The receipt from the Aggregator is incorrect!")
        else:
            print("Successfully receive receipt from the Aggregator")
    
    # OUT_OF_TIME <end_time>
    elif data[:11] == b'OUT_OF_TIME':
        print(f"Aggregator timer ends at {float(data[12:])}, it is {time.time()} now!")

    else:
        print(f"Trusted party returns {data}")
    writer.close()