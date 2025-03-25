import asyncio, dill as pickle
from Thread.Worker.Helper import Helper
from Thread.Worker.Manager import Manager, Commiter, Client_info

TRUSTED_PARTY_HOST = Helper.get_env_variable("TRUSTED_PARTY_HOST")
TRUSTED_PARTY_PORT = Helper.get_env_variable("TRUSTED_PARTY_PORT")

# Client registers itself with Trusted Party
async def send_CLIENT(manager: Manager):

    reader, writer = await asyncio.open_connection(TRUSTED_PARTY_HOST, TRUSTED_PARTY_PORT)
    _ = await reader.read(3)  # Remove first 3 bytes of Telnet command
    
    # CLIENT <client_host> <client_port> <client RSA_public_key>
    data = f'CLIENT {manager.host} {manager.port} {manager.signer.e} {manager.signer.n}'
    await Helper.send_data(writer, data)
    
    # <aggregator_host> <aggregator_port> <accuracy> <commiter>
    data = await Helper.receive_data(reader)
    host, port, accuracy, p, h, k = data.split(b' ', 5)
    host = host.decode()
    port, accuracy = int(port), int(accuracy)
    commiter = Commiter(tuple([int(param) for param in [p, h, k]]))

    # <base_model_class>
    data = await Helper.receive_data(reader)
    base_model_class = pickle.loads(data)
    manager.set_FL_public_params(host, port, commiter, accuracy, base_model_class)

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
    await Helper.send_data(writer, message)
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