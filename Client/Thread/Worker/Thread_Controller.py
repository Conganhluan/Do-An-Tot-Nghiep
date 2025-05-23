import asyncio, dill as pickle, time
from Thread.Worker.Helper import Helper
from Thread.Worker.Manager import Manager, Commiter, Client_info, RSA_public_key

TRUSTED_PARTY_HOST = Helper.get_env_variable("TRUSTED_PARTY_HOST")
TRUSTED_PARTY_PORT = Helper.get_env_variable("TRUSTED_PARTY_PORT")

# Client registers itself with Trusted Party
async def send_CLIENT(manager: Manager):

    reader, writer = await asyncio.open_connection(TRUSTED_PARTY_HOST, TRUSTED_PARTY_PORT)
    _ = await reader.read(3)  # Remove first 3 bytes of Telnet command
    
    # CLIENT <client_host> <client_port> <client RSA_public_key>
    data = f'CLIENT {manager.host} {manager.port} {manager.signer.e} {manager.signer.n}'
    await Helper.send_data(writer, data)
    
    # <aggregator_host> <aggregator_port> <aggregator RSA_public_key> <commiter>
    data = await Helper.receive_data(reader)
    host, port, e, n, p, h, k = data.split(b' ', 6)
    host = host.decode()
    port = int(port)
    public_key = RSA_public_key(int(e), int(n))
    commiter = Commiter(tuple([int(param) for param in [p, h, k]]))

    # <base_model_class>
    data = await Helper.receive_data(reader)
    base_model_class = pickle.loads(data)
    manager.set_FL_public_params(host, port, public_key, commiter, base_model_class)

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
        print(f"Client {neighbor.round_ID} returns {data}")
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

    # LOCAL_MODEL <round_ID> <data_number> <signed_data_number> <client_r>
    manager.commiter.gen_new_local_r()
    data = f"LOCAL_MODEL {manager.round_ID} {manager.trainer.data_num} {manager.signer.sign(manager.trainer.data_num)} {manager.commiter.local_r}"
    await Helper.send_data(writer, data)

    # <masked_parameters>
    masked_parameters = manager.get_masked_params()
    await Helper.send_data(writer, masked_parameters.tobytes())

    # <committed_parameters>
    committed_parameters = manager.get_committed_params(masked_parameters)
    await Helper.send_data(writer, committed_parameters.tobytes())

    # <signed_parameters>
    signed_parameters = manager.get_signed_params(committed_parameters)
    await Helper.send_data(writer, pickle.dumps(signed_parameters))

    # SUCCESS <received_time> <signed_received_data>
    data = await Helper.receive_data(reader)
    if data[:7] == b"SUCCESS":
        received_time, signed_received_data = data[8:].split(b' ', 1)
        received_time = float(received_time)
        signed_received_data = int(signed_received_data)
        manager.set_receipt_from_Aggregator(received_time, signed_received_data)

        # print("Check receipt")
        if not manager.check_receipt(committed_parameters):
            manager.abort("The receipt from the Aggregator is incorrect!")
        else:
            print("Successfully receive receipt from the Aggregator")
    
    # OUT_OF_TIME <end_time>
    elif data[:11] == b'OUT_OF_TIME':
        print(f"Aggregator timer ends at {float(data[12:])}, it is {time.time()} now!")

    else:
        print(f"Trusted party returns {data}")
    writer.close()



###########################################################################################################



# Client sends round-end signal to Trusted Party
async def send_CLI_END(manager: Manager):

    reader, writer = await asyncio.open_connection(TRUSTED_PARTY_HOST, TRUSTED_PARTY_PORT)
    _ = await reader.read(3)  # Remove first 3 bytes of Telnet command

    # CLI_END <global_model_commit> <client_num>
    data = "CLI_END ".encode() + manager.last_commit.tobytes()
    await Helper.send_data(writer, data)

    # <client_round_ID> <accuracy_evaluation>
    data = f"{manager.round_ID} {manager.trainer.self_evaluate()}"
    await Helper.send_data(writer, data)

    # for client in ZKP_public_json
    # <client_round_ID> <ON/OFF>

    # SUCCESS
    data = await Helper.receive_data(reader)
    if data == b"SUCCESS":
        print(f"Successfully send round result to the Trusted party")
    else:
        print(f"Trusted party returns {data}")
    writer.close()