import asyncio, telnetlib3
from Manager import Manager, Client_info
from Masker import Masker

def listener_thread(flag: str, manager: Manager, masker: Masker):
    
    print(f"Listener is on at port {manager.port}")

    async def shell(reader: telnetlib3.TelnetReader, writer: telnetlib3.TelnetWriter):

        data_input = await reader.readuntil()
        processed_data = data_input.decode('UTF-8').split('_')

        # Not thought yet
        if processed_data[0] == 'DH params' and len(processed_data) == 3:
            print("Confirm to get DH parameters from Trusted party!")
            
            # Get DH parameters
            g = int(processed_data[1])
            q = int(processed_data[2])
            masker = Masker((g,q))

            writer.write(f"{masker.get_DH_public_key()}\n")
            await writer.drain()

        elif processed_data[0] == "Round information" and len(processed_data) == 3:

            round_ID = int(processed_data[1])
            neighbor_num = int(processed_data[2])
            print(f"Confirm round ID: {round_ID}")

            neighbor_list = []
            for i in range(neighbor_num):
                
                # Get neighbor information
                data_input = await reader.readuntil()
                processed_data = data_input.decode('UTF-8').split('_')
                
                # Process neighbor data
                neighbor_round_ID = int(processed_data[0])
                neighbor_host = processed_data[1]
                neighbor_port = int(processed_data[2])
                neighbor_DH_public_key = int(processed_data[3])

                neighbor_list.append(Client_info(neighbor_round_ID, neighbor_host, neighbor_port, neighbor_DH_public_key))
                print(f"Done getting information of neighbor {neighbor_round_ID} - {neighbor_host}:{neighbor_port}")

            manager.set_round_information(round_ID, neighbor_list)
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