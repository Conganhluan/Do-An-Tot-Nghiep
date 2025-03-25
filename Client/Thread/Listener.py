import asyncio, telnetlib3, dill as pickle
from Thread.Worker.Manager import Manager, Client_info
from Thread.Worker.Helper import Helper

def listener_thread(manager: Manager):
    
    print(f"Listener is on at port {manager.port}")

    async def shell(reader: telnetlib3.TelnetReader, writer: telnetlib3.TelnetWriter):

        data = await Helper.receive_data(reader)

        # Aggregator/Client aborts the process due to abnormal activities
        if b'STOP' == data[:4]:

            verification_round_number = int(data[5:])
            if verification_round_number != manager.round_number:
                manager.abort("Get the STOP signal with wrong round number")
            else:
                manager.set_flag(manager.FLAG.STOP)

        # Trusted Party gets DH public keys from chosen Clients
        elif b'DH_PARAM' == data[:8]:

            # DH_PARAM <g> <q>
            g, q = [int(param) for param in data[9:].split(b' ', 2)]
            manager.set_masker(g, q)

            # <client_DH_public_key>
            await Helper.send_data(writer, f"{manager.masker.get_DH_public_key()}")

            # SUCCESS
            data = await Helper.receive_data(reader)
            if data == b"SUCCESS":
                print("Successfully send DH public key to the Trusted party")
            else:
                print(f"Trusted party returns {data}")
            writer.close()

        # Trusted Party sends round information to Clients
        elif b'ROUND_INFO' == data[:10]:

            # ROUND_INFO <round_number> <client_round_ID> <neighbor_num>
            round_number, self_round_ID, neighbor_num = data[11:].split(b' ', 2)
            self_round_ID, neighbor_num = int(self_round_ID), int(neighbor_num)
            
            # <base_model_commit/previous_global_model_commit>
            data = await Helper.receive_data(reader)
            manager.set_last_commit([int(param) for param in data.split(b' ')])

            neighbor_list = list()
            for _ in range(neighbor_num):

                # <neighbor_round_ID> <neighbor_host> <neighbor_port> <neighbor_DH_public_key>
                data = await Helper.receive_data(reader)
                round_ID, host, port, DH_public_key = data.split(b' ', 3)
                round_ID, port, DH_public_key = int(round_ID), int(port), int(DH_public_key)
                host = host.decode()
                neighbor_list.append(Client_info(round_ID, host, port, DH_public_key))
            
            manager.set_round_information(round_number, self_round_ID, neighbor_list)

            # SUCCESS
            await Helper.send_data(writer, "SUCCESS")
            print("Successfully receive round information from the Trusted party")
            writer.close()

        # Aggregator sends global model to Clients
        elif b'GLOB_MODEL' == data[:10]:

            # GLOB_MODEL <r> 
            commit_secret = int(data[11:])
            manager.commiter.set_secret(commit_secret)

            # <global_model_parameters>
            data = await Helper.receive_data(reader)
            global_parameters = [float(param) for param in data.split(b' ')]
            if manager.round_number != 0:
                for idx in range(len(global_parameters)):
                    global_parameters[idx] /= manager.accuracy
            if not manager.commiter.check_commit(global_parameters, manager.last_commit):
                manager.abort("The global parameter received from Aggregator is not equal to commitment from the Trusted party")
            else:
                manager.trainer.load_parameters(global_parameters)

            # SUCCESS
            await Helper.send_data(writer, "SUCCESS")
            print("Successfully receive global model from the Aggregator")
            writer.close()

        else:
            await Helper.send_data(writer, "Operation not allowed!")
        
        writer.close()
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    coro = telnetlib3.create_server(port=manager.port, shell=shell, encoding=False, encoding_errors="ignore")
    server = loop.run_until_complete(coro)
    loop.run_until_complete(server.wait_closed())