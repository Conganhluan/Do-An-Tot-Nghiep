import asyncio, telnetlib3
from Manager import Manager

def listener_thread(manager: Manager):
    
    print("listener is on!")

    async def shell(reader: telnetlib3.TelnetReader, writer: telnetlib3.TelnetWriter):

        data_input = await reader.readuntil()
        processed_data = data_input.decode('UTF-8').split('_')

        # Not thought yet
        if False:

            pass

        else:

            writer.write("Operation not allowed!\n")
            await writer.drain()

        writer.close()
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    coro = telnetlib3.create_server(port=manager.port, shell=shell)
    server = loop.run_until_complete(coro)
    loop.run_until_complete(server.wait_closed())