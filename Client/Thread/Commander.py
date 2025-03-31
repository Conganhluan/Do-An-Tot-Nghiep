from Thread.Worker.Manager import Manager
import os, sys

def commander_thread(manager: Manager):

    print("Commander is on and wait for input!")

    while True:

        command = input()

        if command == 'stop':
            print("Client stops!")
            quit()

        elif command == "client info":
            print(f"Self info: {manager.host}:{manager.port}")
            print(f"Aggregator info - {manager.aggregator_info.host}:{manager.aggregator_info.port}")
            print(f"Commitment parameters: p: {manager.commiter.p}, h: {manager.commiter.h}, k: {manager.commiter.k}")
            print(f"RSA keys: d: {manager.signer.d} e: {manager.signer.e} d: {manager.signer.n}")

        elif command == "round info":
            if manager.round_ID == None:
                print("Client is currently not in training round")
                continue
            print(f"ID: {manager.round_ID}")
            print("Neighbor list:")
            for neighbor in manager.neighbor_list:
                print(f"ID: {neighbor.round_ID} - {neighbor.host}:{neighbor.port}, DH public key: {neighbor.DH_public_key}")

        elif command == "self secret":
            print(f"ID: {manager.round_ID} - {manager.host}:{manager.port}")
            print(f"ss: {manager.masker.ss}, ps: {manager.masker.ps}")

        elif command == "neighbor secrets":
            for neighbor in manager.neighbor_list:
                print(f"ID: {neighbor.round_ID} - {neighbor.host}:{neighbor.port}")
                print(f"ss: {neighbor.ss_point}, ps: {neighbor.ps_point}")

        elif command == 'register':
            manager.set_flag(manager.FLAG.RE_REGISTER)

        elif command == 'cls':
            os.system('cls')
        
        elif command == 'restart':
            os.execv(sys.executable, ['python'] + sys.argv)

        elif command[:5] == 'abort':
            manager.abort_message == command[6:]
            manager.set_flag(manager.FLAG.ABORT)

        elif command == 'receipt':
            print(f"Received time: {manager.receipt.received_time}")
            print(f"Signed data: {manager.receipt.signed_received_data}")

        else:
            print("I'm currently supporting these commands: [stop, client info, round info, register, cls, restart, self secret, neighbor secrets, abort <message>, receipt]")