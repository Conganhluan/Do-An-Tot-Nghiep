import asyncio, telnetlib3, dill as pickle, numpy
from Thread.Worker.Manager import Manager, Client_info, RSA_public_key, Receipt
from Thread.Worker.Helper import Helper

def listener_thread(manager: Manager):

    print(f"Listener is on at port {manager.port}")

    async def shell(reader: telnetlib3.TelnetReader, writer: telnetlib3.TelnetWriter):
            
        data = await Helper.receive_data(reader)
        
        # Aggregator/Client aborts the process due to abnormal activities
        if b'STOP' == data[:4]:

            verification_round_number, message = data[5:].split(b' ', 1)
            if int(verification_round_number) != manager.round_number:
                manager.abort("Get the STOP signal with wrong round number")
            else:
                print("STOP due to " + message.decode())
                manager.set_flag(manager.FLAG.STOP)

        # Trusted Party sends round information to Aggregator
        elif b'ROUND_INFO' == data[:10]:

            # ROUND_INFO <round_number> <client_num> <q>
            manager.round_number, client_num, manager.q = [int(x) for x in data[11:].split(b' ', 2)]
            client_list = list()
            for i in range(client_num):

                # <client_round_ID> <client_host> <client_port> <client_DH_public_key> <client_RSA_public_key>
                data : bytes = await Helper.receive_data(reader)
                round_ID, host, port, DH_public_key, e, n = data.split(b' ', 5)
                host = host.decode()
                round_ID, port, DH_public_key, e, n = [int(param) for param in [round_ID, port, DH_public_key, e, n]]

                # <client_neighbor_round_ID_1> <client_neighbor_round_ID_2> ... <client_neighbor_round_ID_n>
                data: bytes = await Helper.receive_data(reader)
                neighbor_list = [int(neighbor_ID) for neighbor_ID in data.split(b' ')]

                client_list.append(Client_info(round_ID, host, port, RSA_public_key(e, n), DH_public_key, neighbor_list))
                print(f"Successfully receive information of client {round_ID}")

            # SUCCESS
            await asyncio.wait_for(Helper.send_data(writer, "SUCCESS"), timeout=None)
            manager.set_round_information(client_list)
            manager.set_flag(manager.FLAG.START_ROUND)
        
        # Client sends local model to Aggregator
        elif b'LOCAL_MODEL' == data[:11]:
            
            # LOCAL_MODEL <round_ID> <data_number> <signed_data_number> <client_r>
            round_ID, data_num, signed_data_num, local_r = [int(param) for param in data[12:].split(b' ', 3)]
            
            # <masked_parameters>
            data: bytes = await Helper.receive_data(reader)
            masked_params = numpy.frombuffer(data, dtype=numpy.int64)

            # <committed_parameters>
            data: bytes = await Helper.receive_data(reader)
            committed_params = numpy.frombuffer(data, dtype=numpy.uint64)

            # <signed_parameters>
            data: bytes = await Helper.receive_data(reader)
            signed_params = pickle.loads(data)
            
            if not manager.timeout:

                client = manager.get_client_by_ID(round_ID)
                
                if not client.check_signature(data_num, signed_data_num):
                    manager.abort(f"The signature of data number from client {client.round_ID} is wrong")
            
                elif not client.check_parameters_signature(masked_params, committed_params):
                    manager.abort(f"The signature of local model parameters from client {client.round_ID} is wrong")
                
                elif not client.check_commited_params(manager.commiter, masked_params, committed_params, local_r):
                    manager.abort(f"The commitment from client {client.round_ID} is wrong")

                else:
                    manager.receive_trained_data(client, data_num, signed_data_num, masked_params, local_r, committed_params, signed_params)
                    receipt: Receipt = manager.get_receipt(client)
                    manager.received_data += 1

                    # SUCCESS <received_time> <signed_received_data>
                    data = f"SUCCESS {receipt.received_time} {receipt.signed_received_data}"
                    await Helper.send_data(writer, data)
                    print(f"Successfully receive local model parameters of client {round_ID}")

            else:

                # OUT_OF_TIME <end_time>
                data = f"OUT_OF_TIME {manager.timeout_time}"
                await Helper.send_data(writer, data)
                print(f"Client {round_ID} has been late for the timeout of {manager.timeout_time}!")

        else:
            await Helper.send_data(writer, "Operation not allowed!")
        
        writer.close()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    coro = telnetlib3.create_server(port=manager.port, shell=shell, encoding=False, encoding_errors='ignore')
    server = loop.run_until_complete(coro)
    loop.run_until_complete(server.wait_closed())