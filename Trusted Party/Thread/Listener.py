import asyncio, telnetlib3, time, dill as pickle, struct, numpy
from Thread.Worker.Manager import Manager, RSA_public_key, Client_info
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

            # AGG_REGIS <aggregator_host> <aggregator_port> <aggregator RSA_public_key> <base_model_class>
            host, port, RSA_e, RSA_n, base_model_class = data[10:].split(b' ', 4)
            host = host.decode()
            port = int(port)
            public_key = RSA_public_key(int(RSA_e), int(RSA_n))
            base_model_class = pickle.loads(base_model_class)
            manager.register_aggregator(host, port, public_key, base_model_class)
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
            id = int(time.time()*65535)
            manager.add_client(id, host, port, RSA_public_key(e, n))
            # print(f"Confirm to get registration from Client {id} - {host}:{port}")

            # <aggregator_host> <aggregator_port> <aggregator RSA_public_key> <commiter>
            data = f"{manager.aggregator_info.host} {manager.aggregator_info.port} {manager.aggregator_info.RSA_public_key.e} {manager.aggregator_info.RSA_public_key.n} {manager.commiter.p} {manager.commiter.h} {manager.commiter.k}"
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

        # Aggregator sends round-end signal to Trusted Party
        elif b'AGG_END' == data[:7]:

            # AGG_END <parameters_commit>
            parameters_commit = numpy.frombuffer(data[8:], dtype=numpy.uint64)
            manager.set_last_model_commitment(parameters_commit)

            last_round_attendees = list()
            for _ in range(len(manager.client_list)):

                # <cient_round_ID> <client_data_num> <Offline training (ON/OFF)> <Offline neighbor (ON/OFF)>
                data = await Helper.receive_data(reader)
                round_ID, data_num, status, neighbor_status = data.split(b' ', 3)
                round_ID, data_num = int(round_ID), int(data_num)
                status, neighbor_status = status.decode(), neighbor_status.decode()
                the_client = manager.__get_client_by_round_ID__(round_ID)
                if status == "OFF":
                    the_client.choose_possibility -= 20
                if neighbor_status == "OFF":
                    the_client.choose_possibility -= 30
                last_round_attendees.append((the_client, data_num))
            
            # last_round_attendees : list[tuple[Client_info, int]] = sorted(last_round_attendees, key=lambda x: x[1], reverse=True)
            # first_data_num = last_round_attendees[0][1]
            # second_data_num = -1
            # third_data_num = -1
            # for attendee in last_round_attendees:
            #     if attendee[1] == first_data_num:
            #         attendee[0].choose_possibility += 25
            #     elif attendee[1] < first_data_num:
            #         if second_data_num == -1:
            #             second_data_num = attendee[1]
            #             attendee[0].choose_possibility += 15
            #         elif attendee[1] == second_data_num:
            #             attendee[0].choose_possibility += 15
            #         elif attendee[1] < second_data_num:
            #             if third_data_num == -1:
            #                 third_data_num = attendee[1]
            #                 attendee[0].choose_possibility += 5
            #             elif attendee[1] == third_data_num:
            #                 attendee[0].choose_possibility += 5
            #             elif attendee[1] < third_data_num:
            #                 break
            
            # SUCCESS
            await Helper.send_data(writer, "SUCCESS")
            print(f"Successfully get the round result the Aggregator")
            manager.start_timer(180)
            writer.close()

        elif b'CLI_END' == data[:7]:
            
            parameters_commit = numpy.frombuffer(data[8:], dtype=numpy.uint64)
            manager.round_manager.received_commit.append(parameters_commit)

            # <client_round_ID> <accuracy_evaluation>
            data = await Helper.receive_data(reader)
            round_ID, accuracy = data.split(b' ', 1)
            round_ID, accuracy = int(round_ID), float(accuracy)
            manager.round_manager.__get_client_by_round_ID__(round_ID).accuracy_ratio = accuracy

            # for _ in range(len(manager.round_manager.client_list)):
            # <client_round_ID> <ON/OFF>

            # SUCCESS
            await Helper.send_data(writer, "SUCCESS")
            print(f"Successfully get the round result the client {round_ID}")
            writer.close()

        else:
            await Helper.send_data(writer, "Operation not allowed!")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    coro = telnetlib3.create_server(port=TRUSTED_PARTY_PORT, shell=shell, encoding=False, encoding_errors="ignore")
    server = loop.run_until_complete(coro)
    loop.run_until_complete(server.wait_closed())