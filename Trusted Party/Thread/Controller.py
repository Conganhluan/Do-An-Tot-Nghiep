from Thread.Worker.Manager import Manager, Round_Manager
from Thread.Worker.Thread_Controller import *
from time import sleep
from copy import deepcopy

def controller_thread(manager: Manager):

    print("Controller is on and at duty!")

    # Get next command from stdinput
    while True:
        
        flag = manager.get_flag()

        if flag == manager.FLAG.STOP:

            print("Got the ABORT signal, send the STOP signal...")
            asyncio.run(send_STOP(manager))

        # Init the round
        elif flag == manager.FLAG.START_ROUND:
            
            # Choose clients for training round
            client_list = list()
            ATTEND_CLIENTS = [Helper.get_env_variable('ATTEND_CLIENTS')]
            available_client_list = deepcopy(manager.client_list)                         # Available clients
            
            while ATTEND_CLIENTS[0] and available_client_list:

                # Make sure desired number of chosen client always be smaller or equal to available client number
                ATTEND_CLIENTS[0] = min(ATTEND_CLIENTS[0], len(available_client_list))

                # Choose clients by its probability number
                chosen_clients = manager.choose_clients(available_client_list, ATTEND_CLIENTS[0])

                # Filter unalive ones
                asyncio.run(send_PING(client_list, chosen_clients, ATTEND_CLIENTS))
                    
            # Create round manger
            manager.round_manager = Round_Manager(client_list, manager.get_current_round(), manager.get_commiter())
            asyncio.run(send_DH_PARAM(manager))
            asyncio.run(send_ROUND_INFO_client(manager))
            asyncio.run(send_ROUND_INFO_aggregator(manager))

        else:

            pass

        sleep(5)