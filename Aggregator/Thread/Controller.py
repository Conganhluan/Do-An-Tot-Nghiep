from Thread.Worker.Manager import Manager
from Thread.Worker.Helper import Helper
from Thread.Worker.Thread_Controller import *
from time import sleep

def controller_thread(manager: Manager):

    print("Controller is on and at duty!")

    # Register with Trusted Party
    asyncio.run(send_AGG_REGIS(manager))

    while True:

        flag = manager.get_flag()

        if flag == manager.FLAG.STOP:

            print("Got the STOP signal from Trusted party, please command 'stop' to quit!")

        elif flag == manager.FLAG.ABORT:

            asyncio.run(send_ABORT(manager.abort_message))
        
        elif flag == manager.FLAG.START_ROUND:

            asyncio.run(send_GLOB_MODEL(manager))
            manager.start_timer(int(Helper.get_env_variable("TIMEOUT_SECONDS")))

        elif flag == manager.FLAG.AGGREGATE:

            asyncio.run(send_STATUS(manager))
            manager.aggregate()
            asyncio.run(send_AGG_MODEL(manager))

        elif flag == manager.FLAG.RE_REGISTER:

            asyncio.run(send_AGG_REGIS(manager))

        sleep(5)