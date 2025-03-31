import asyncio, telnetlib3, time, dill as pickle, struct, numpy
from Thread.Worker.Manager import Manager, RSA_public_key
from Thread.Worker.Helper import Helper

TRUSTED_PARTY_PORT = Helper.get_env_variable("TRUSTED_PARTY_PORT")

def listener_thread(manager: Manager):
    
    print(f"Listener is on at port {TRUSTED_PARTY_PORT}")

    async def shell(reader: telnetlib3.TelnetReader, writer: telnetlib3.TelnetWriter):
            
        data = await Helper.receive_data(reader)

        # Aggregator/Client aborts the process due to abnormal activities
        if b'ABORT' == data[:5]:

            manager.stop(str(data[6:]))

        # Aggregator registers itself with Trusted Party
        elif b"AGG_REGIS" == data[:9]:

            # AGG_REGIS <aggregator_host> <aggregator_port> <base_model_class>
            host, port, base_model_class = data[10:].split(b' ', 2)
            host = host.decode()
            port = int(port)
            base_model_class = pickle.loads(base_model_class)
            manager.register_aggregator(host, port, base_model_class)
            # print(f"Confirm to get registration from the Aggregator {host}:{port}")

            # <commiter>
            data = f"{manager.commiter.p} {manager.commiter.h} {manager.commiter.k}"
            await Helper.send_data(writer, data)
            # print(f"Send commiter to the Aggregator...")

            # <base_model_commit> 
            data = await Helper.receive_data(reader)
            manager.set_last_model_commitment(numpy.frombuffer(data, dtype=numpy.int64))
            # print(f"Confirm to get the model commitment from the Aggregator")

            # SUCCESS
            await Helper.send_data(writer, "SUCCESS")
            print(f"Successfully register the Aggregator")
            writer.close()

        # Client registers itself with Trusted Party
        elif b'CLIENT' == data[:6]:

            # CLIENT <client_host> <client_port> <client RSA_public_key>
            host, port, e, n = data[7:].split(b' ', 3)
            host = host.decode()
            port, e, n = int(port), int(e), int(n)
            id = int(time.time()*1024)
            manager.add_client(id, host, port, RSA_public_key(e, n))
            # print(f"Confirm to get registration from Client {id} - {host}:{port}")

            # <aggregator_host> <aggregator_port> <gs_mask> <commiter>
            data = f"{manager.aggregator_info.host} {manager.aggregator_info.port} {manager.gs_mask} {manager.commiter.p} {manager.commiter.h} {manager.commiter.k}"
            await Helper.send_data(writer, data)
            
            # <base_model_class>
            data = pickle.dumps(manager.aggregator_info.base_model_class)
            await Helper.send_data(writer, data)
            # print(f"Send FL public information to Client {id}...")

            # SUCCESS
            data = await Helper.receive_data(reader)
            if data == b"SUCCESS":
                print(f"Successfully register the client {id} - {host}:{port}")
            else:
                print(f"Client {host}:{port} returns {data}")
            writer.close()
        
        else:
            await Helper.send_data(writer, "Operation not allowed!")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    coro = telnetlib3.create_server(port=TRUSTED_PARTY_PORT, shell=shell, encoding=False, encoding_errors="ignore")
    server = loop.run_until_complete(coro)
    loop.run_until_complete(server.wait_closed())