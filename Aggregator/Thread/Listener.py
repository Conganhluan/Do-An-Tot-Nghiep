import asyncio, telnetlib3, dill as pickle
from Thread.Worker.Manager import Manager, Client_info, RSA_public_key
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

        # Trusted Party sends round information to Aggregator
        elif b'ROUND_INFO' == data[:10]:

            # ROUND_INFO <round_number> <client_num>
            manager.round_number, client_num = [int(x) for x in data[11:].split(b' ', 1)]
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
            
        else:
            await Helper.send_data(writer, "Operation not allowed!")
        
        writer.close()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    coro = telnetlib3.create_server(port=manager.port, shell=shell, encoding=False, encoding_errors='ignore')
    server = loop.run_until_complete(coro)
    loop.run_until_complete(server.wait_closed())