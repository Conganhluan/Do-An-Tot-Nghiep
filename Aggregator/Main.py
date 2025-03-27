import threading
from Thread.Commander import commander_thread
from Thread.Listener import listener_thread
from Thread.Controller import controller_thread
from Thread.Worker.BaseModel import *
from Thread.Worker.Manager import Manager
import os, sys

def main():

    manager : Manager = Manager(CNNModel_MNIST)
    os.system('cls')

    # Create a server listening and return needed information
    listener = threading.Thread(target=listener_thread, args=(manager, ), daemon=True)
    listener.start()

    # Create a controller to automatically run as flag orders
    controller = threading.Thread(target=controller_thread, args=(manager, ), daemon=True)
    controller.start()
    
    # Create a commander for manual interraction
    commander = threading.Thread(target=commander_thread, args=(manager, ))
    commander.start()
    commander.join()

if __name__ == "__main__":
    main()
else:
    raise Exception("Main.py must be run as main file, not imported!")