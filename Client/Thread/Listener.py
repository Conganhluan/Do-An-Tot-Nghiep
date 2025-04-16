import asyncio, telnetlib3, struct, numpy
from Thread.Worker.Manager import Manager, Client_info
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
            round_number, self_round_ID, neighbor_num = int(round_number), int(self_round_ID), int(neighbor_num)
            
            # <base_model_commit/previous_global_model_commit>
            # data = await Helper.receive_data(reader)
            # manager.set_last_commit(numpy.frombuffer(data, dtype=numpy.uint64))
            # print("Confirm to get the model commit from the Trusted party")

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

            # <global_model_parameters>
            data = await Helper.receive_data(reader)
            
            # print(f"Get global parameters for the round {manager.round_number}")
            if manager.round_number == 0:
                global_parameters = numpy.frombuffer(data, dtype=numpy.float32)
                manager.trainer.load_parameters(global_parameters, manager.round_ID)
            else:
                global_parameters = numpy.frombuffer(data, dtype=numpy.int64)
                manager.trainer.load_parameters(manager.get_unmasked_model(global_parameters), manager.round_ID)

            # SUCCESS
            await Helper.send_data(writer, "SUCCESS")
            print("Successfully receive global model from the Aggregator")
            manager.set_flag(manager.FLAG.TRAIN)
            
            writer.close()

        # Client sends secret points to its neighbors
        elif b'POINTS' == data[:6]:

            # POINTS <SS_point_X> <SS_point_Y> <PS_point_X> <PS_point_Y>
            neighbor_round_ID, ss_X, ss_Y, ps_X, ps_Y = [int(num) for num in data[7:].split(b' ', 4)]
            manager.set_secret_points(neighbor_round_ID, (ss_X, ss_Y), (ps_X, ps_Y))

            # SUCCESS
            await Helper.send_data(writer, "SUCCESS")
            print(f"Successfully receive secret points from client {neighbor_round_ID}")
            writer.close()

        # Aggregator gets secrets points from Clients
        elif b'STATUS' == data[:6]:

            # STATUS <neighbor_num>
            neighbor_num = int(data[7:])

            for idx in range(neighbor_num):
                
                # <neighbor_round_ID> <ON/OFF>
                receiv_data = await Helper.receive_data(reader)
                neighbor_ID, neighbor_status = receiv_data.split(b' ')
                neighbor = manager.get_neighbor_by_ID(int(neighbor_ID))
                
                if neighbor is None:
                    manager.abort(f"Aggregator tries to get secret points of unknown client {neighbor_ID}")
                
                elif not neighbor.is_online is None:
                    manager.abort(f"Aggregator tries to get neighbor {neighbor.round_ID} secret points twice")

                # <SS_point_X/PS_point_X> <signature> <SS_point_Y/PS_point_Y> <signature>
                elif neighbor_status == b'ON':
                    neighbor.is_online = True
                    sent_data = f"{neighbor.ss_point[0]} {manager.signer.sign(neighbor.ss_point[0])} {neighbor.ss_point[1]} {manager.signer.sign(neighbor.ss_point[1])}"
                    print(f"Aggregator said neighbor {neighbor.round_ID} is online")
                elif neighbor_status == b'OFF':
                    neighbor.is_online = False
                    sent_data = f"{neighbor.ps_point[0]} {manager.signer.sign(neighbor.ps_point[0])} {neighbor.ps_point[1]} {manager.signer.sign(neighbor.ps_point[1])}"
                    print(f"Aggregator said neighbor {neighbor.round_ID} is offline")
                await Helper.send_data(writer, sent_data)

            # SUCCESS
            data = await Helper.receive_data(reader)
            if data == b"SUCCESS":
                print("Successfully send neighbor secret points to the Aggregator")
            else:
                print(f"Aggregator returns {data}")
            writer.close()

        # Aggregator sends aggregated global model to Clients
        elif data[:9] == b'AGG_MODEL':

            # <global_parameters>
            data = await Helper.receive_data(reader)
            received_global_parameters = numpy.frombuffer(data, dtype=numpy.int64)

            # Load the parameters directly without verification since ZKP is removed
            manager.trainer.load_parameters(manager.get_unmasked_model(received_global_parameters), manager.round_ID)
            await Helper.send_data(writer, "SUCCESS")
            print(f"Successfully receive global models from the Aggregator")
            writer.close()

        else:
            await Helper.send_data(writer, "Operation not allowed!")
        
        writer.close()
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    coro = telnetlib3.create_server(port=manager.port, shell=shell, encoding=False, encoding_errors="ignore")
    server = loop.run_until_complete(coro)
    loop.run_until_complete(server.wait_closed())