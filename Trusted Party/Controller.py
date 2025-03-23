import asyncio
from Helper import Helper
from Manager import FL_Manager, Round_Manager

def controller_thread(FL_manager: FL_Manager):

    # Get next command from stdinput
    while True:
        
        command = input()

        # Stop the trusted party
        if command in ("end", "quit", "exit"):
            print("Program ends!")
            quit()
        
        # List the client that registered with trusted party
        elif "client" in command and "list" in command:
            print("Registed client list:")
            for client in FL_manager.client_list:
                print(f"ID: {client.ID}, Address: {client.host}:{client.port}, RSA keys: {client.RSA_pulic_key}")

        # Init a new training round
        elif "init" in command and "round" in command:
            pass