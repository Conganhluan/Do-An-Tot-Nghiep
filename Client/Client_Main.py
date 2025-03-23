import threading
from Listener import listener_thread
from Controller import controller_thread, Manager, Signer, Masker

def main():

    flag = "None"
    signer : Signer = Signer()
    manager: Manager = Manager()
    masker: Masker = None

    # Create a server listening and return needed information
    listener = threading.Thread(target=listener_thread, args=(flag, manager, masker, ), daemon=True)
    listener.start()

    # Create a controller to run as order of Trusted Party and Aggregator
    controller = threading.Thread(target=controller_thread, args=(flag, manager, signer, ))
    controller.start()
    controller.join()

if __name__ == "__main__":
    main()
else:
    raise Exception("Client_Main.py must be run as main file, not imported!")