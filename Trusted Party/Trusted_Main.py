import threading
from time import time, sleep
from Listener import listener_thread
from Controller import controller_thread, FL_Manager, Round_Manager

def main(): 
    
    FL_manager = FL_Manager()

    # Create a server listening and return needed information
    listener = threading.Thread(target=listener_thread, args=(FL_manager, ), daemon=True)
    listener.start()

    # Create a controller to run command as input
    controller = threading.Thread(target=controller_thread, args=(FL_manager, ))
    controller.start()
    controller.join()

if __name__ == "__main__":
    main()
else:
    raise Exception("Trusted_Main.py must be run as main file, not imported!")