from Thread.Worker.Manager import Manager
import os, sys

def commander_thread(manager: Manager):
    
    print("Commander is on and wait for input!")

    while True:

        command = input()

        if command == 'stop':
            print("Aggregator stops!")
            quit()
        
        elif command == 'round info':
            print("Attendee clients in round:")
            for client in manager.client_list:
                print(f"{client.round_ID} - {client.host}:{client.port}, neighbors: {client.neighbor_list}")
                print(f"DH_public_key: {client.DH_public_key}")
                print(f"RSA public key: e: {client.RSA_public_key.e}, n: {client.RSA_public_key.n}")
                print(f"Status: {"Online" if client.is_online else "Offline"}, dataset number: {client.local_datanum}")

        elif command == 'public info':
            print(f"Self address: {manager.host}:{manager.port}")
            # print(f"Commitment params: h: {manager.commiter.h}, k: {manager.commiter.k}, p: {manager.commiter.p}")

        elif command == 'register':
            manager.set_flag(manager.FLAG.RE_REGISTER)

        elif command == 'start round':
            manager.set_flag(manager.FLAG.START_ROUND)
        
        elif command == 'cls':
            os.system('cls')
        
        elif command == 'restart':
            os.execv(sys.executable, ['python'] + sys.argv)

        elif command[:5] == 'abort':
            manager.abort_message == command[6:]
            manager.set_flag(manager.FLAG.ABORT)

        elif command == 'local models':
            for client in manager.client_list:
                print(f"Client {client.round_ID}:")
                print(f"Data number: {client.local_datanum}")
                print(f"Local model: {client.local_parameters}")
                print(f"Received time: {client.receipt.received_time}")
                print(f"Signed received data: {client.receipt.signed_received_data}")

        elif command == 'timeout status':
            if manager.timeout:
                print("Out of training time!")
            else:
                print("There is still time!")

        elif command == "cancel timer":
            manager.timer.cancel()
            manager.end_timer()

        elif command == 'client status':
            for client in manager.client_list:
                print(f"Client {client.round_ID} -> {"Online" if client.is_online else "Offline"}")

        elif command == 'secret points':
            for client in manager.client_list:
                print(f"Client {client.round_ID}: {', '.join([f"({point.x}, {point.y})" for point in client.secret_points])}")

        else:
            print("I'm currently supporting these commands: [stop, public info, round info, register, cls, restart, abort <message>, local models, timeout status, cancel timer, client status, secret points]")