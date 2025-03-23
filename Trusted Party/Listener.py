import asyncio, telnetlib3
from Manager import FL_Manager
from time import time
from Helper import Helper

def listener_thread(FL_manager: FL_Manager):
    
    print(f"Listener is on at port {Helper.get_env_variable("TRUSTED_PARTY_PORT")}")

    async def shell(reader: telnetlib3.TelnetReader, writer: telnetlib3.TelnetWriter):
            
        data_input = await reader.readuntil()
        processed_data = data_input.decode('UTF-8').split('_')
        
        # A client registers, send "register_<client host>_<client port>_<RSA key e>_<RSA key n>"
        if processed_data[0] == 'register' and len(processed_data) == 5:
        
            # Create a client
            client_id = int(time()*100)
            client_host = processed_data[1]
            client_port = int(processed_data[2])
            RSA_keys = (int(processed_data[3]), int(processed_data[4]))

            # Add client
            FL_manager.add_client(client_id, client_host, client_port, RSA_keys)
            print(f"Successfully register new client: {client_id}, {client_host}:{client_port}")
            writer.write(f"Successfully_{FL_manager.aggregator_info.host}_{FL_manager.aggregator_info.port}_{FL_manager.commitment_params.p}_{FL_manager.commitment_params.h}_{FL_manager.commitment_params.k}\n")
            await writer.drain()

        # The aggregator register, send "aggregator_<aggregator host>_<aggregator port>"
        if processed_data[0] == 'aggregator' and len(processed_data) == 3:
        
            # Create a client
            aggregator_host = processed_data[1]
            aggregator_port = int(processed_data[2])

            # Add client
            FL_manager.register_aggregator(aggregator_host, aggregator_port)
            print(f"Successfully register the aggregator: {aggregator_host}:{aggregator_port}")
            writer.write(f"Successfully_{FL_manager.commitment_params.p}_{FL_manager.commitment_params.h}_{FL_manager.commitment_params.k}\n")
            await writer.drain()
        
        else:

            writer.write("Operation not allowed!\n")
            await writer.drain()
        
        writer.close()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    coro = telnetlib3.create_server(port=Helper.get_env_variable("TRUSTED_PARTY_PORT"), shell=shell)
    server = loop.run_until_complete(coro)
    loop.run_until_complete(server.wait_closed())