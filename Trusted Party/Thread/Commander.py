from Thread.Worker.Manager import Manager
import os, sys

def commander_thread(manager: Manager):
    
    print("Commander is on and wait for input!")

    while True:

        command = input()

        if command == 'stop':
            print("Trusted party stops!")
            quit()
        
        elif command == 'list client':
            for client in manager.client_list:
                print(f"ID: {client.ID} - {client.host}:{client.port}, Choose point: {client.choose_possibility}")
                print(f"RSA public key: e: {client.RSA_public_key.e}, n: {client.RSA_public_key.n}")

        elif command == 'public info':
            if manager.aggregator_info != None:
                print(f"Aggregator info: {manager.aggregator_info.host}:{manager.aggregator_info.port}, Model type: {manager.aggregator_info.base_model_class.__name__}")
            else:
                print(f"There is no aggregator registered")
            # print(f"Commitment params: h: {manager.commiter.h}, k: {manager.commiter.k}, p: {manager.commiter.p}")
            print(f'Current round number: {manager.current_round}')
            print(f"GS mask: {manager.gs_mask}")
            
        elif command == 'init round':
            manager.set_flag(manager.FLAG.START_ROUND)

        elif command == "clear client":
            manager.clear_client()
            print("Successfully clear client")

        elif command == "clear aggregator":
            manager.clear_aggregator()
            print('Successfully clear aggregator')

        elif command == 'cls':
            os.system('cls')
        
        elif command == 'restart':
            os.execv(sys.executable, ['python'] + sys.argv)

        else:
            print("I'm currently supporting these commands: [stop, list client, public info, init round, clear client, clear aggregator, cls, restart]")