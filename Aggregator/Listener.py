import asyncio, telnetlib3
from Helper import Helper
from Manager import Manager, Client_info

def listener_thread(flag: str, manager: Manager):

    print(f"Listener is on at port {manager.port}")

    async def shell(reader: telnetlib3.TelnetReader, writer: telnetlib3.TelnetWriter):
            
        data_input = await reader.readuntil()
        processed_data = data_input.decode('UTF-8').split('_')
        
        if processed_data[0] == "Init the round" and len(processed_data) == 3:

            client_num = int(processed_data[1])
            neighbor_num = int(processed_data[2])
            client_list = list()

            # Get information of each client
            for i in range(client_num):

                data_input = await reader.readuntil()
                processed_data = data_input.decode('UTF-8').split('_')

                round_ID = int(processed_data[0])
                host = processed_data[1]
                port = int(processed_data[2])
                DH_public_key = int(processed_data[3])
                RSA_public_key = (int(processed_data[4]), int(processed_data[5]))

                data_input = await reader.readuntil()
                processed_data = data_input.decode('UTF-8').split('_')

                neighbor_list = [int(neighbor_ID) for neighbor_ID in processed_data]

                client_list.append(Client_info(round_ID, host, port, RSA_public_key, DH_public_key, neighbor_list))

            manager.set_round_information(client_list)
            flag = "START_ROUND"
            writer.write("Successfully\n")
            await writer.drain()
        
        else:

            writer.write("Operation not allowed!\n")
            await writer.drain()
        
        writer.close()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    coro = telnetlib3.create_server(port=manager.port, shell=shell)
    server = loop.run_until_complete(coro)
    loop.run_until_complete(server.wait_closed())