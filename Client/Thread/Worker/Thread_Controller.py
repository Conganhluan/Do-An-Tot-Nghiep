import asyncio, dill as pickle
from Thread.Worker.Helper import Helper
from Thread.Worker.Manager import Manager, Commiter

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