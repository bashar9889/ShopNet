import socket
from client_searching import start_search_thread
from register import registerUser, deregisterUser, loginUser, get_local_ip
import threading
import sys
import time
import queue

# Server address (must match the server's IP and UDP port)
SERVER_IP = "192.168.2.46"  
TCP_PORT = 5006  # Separate port for TCP
UDP_PORT = 5005
serverAddr = (SERVER_IP, UDP_PORT)
client_name= ""
# Initialize the input queue
input_queue = queue.PriorityQueue()
input_lock = threading.Lock()
handle_search_active = threading.Event()

# Create UDP and TCP sockets
clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
clientSocket.bind((get_local_ip(), 0))  # Bind to an available local port
# tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
clientSocket.connect(serverAddr)
# Create UDP socket
clientUdpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
clientUdpSocket.bind((get_local_ip(), 0))  # Bind to an available local UDP port
# Create TCP socket
clientTcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
clientTcpSocket.bind((get_local_ip(), 0))  # Bind to an available local TCP port
# when u want to connect the TCP socket to the server's TCP port if needed
# clientTcpSocket.connect((SERVER_IP, TCP_PORT))


def registrationMenu():
    global client_name
    print("Welcome to the marketplace!")
    print("1. Register User")
    print("2. Deregister User")
    print("3. Exit")
    print("4. Login")
    choice = input("Enter your choice: ")

    if choice == "1":
        name = input("Enter your name: ")
        if registerUser(name, SERVER_IP, clientUdpSocket, clientTcpSocket, serverAddr):
            print("User registered successfully.")
            client_name = name
            searchMenu()
            return
        else:
            print("User registration failed.")
    elif choice == "2":
        rqNum = input("Enter your request number: ")
        name = input("Enter your name: ")
        deregisterUser(rqNum, name, clientUdpSocket, serverAddr)
    elif choice == "3":
        print("Exiting...")
        exit()
    elif choice == "4":
        name = input("Enter your name: ")
        if loginUser(name, clientUdpSocket, serverAddr):
            print("Login successful.")
            client_name = name
            searchMenu()
            return
        else:
            print("Login failed.")
    else:
        print("Invalid choice. Please try again.")
        registrationMenu()


def searchMenu():
    search_listener_thread = threading.Thread(
        target=listen_for_search_messages,
        args=(clientUdpSocket,)
    )
    search_listener_thread.daemon = True
    search_listener_thread.start()
    while True:
        # Check for input requests from other threads
        # while not input_queue.empty():
        #     priority, input_request = input_queue.get()
        #     with input_lock:
        #         if input_request['type'] == 'offer_prompt':
        #             rq_num = input_request['rq_num']
        #             item_name = input_request['item_name']
        #             # Prompt the user
        #             user_response = input(f"Do you want to offer '{item_name}'? (Y/N): ")
        #             input_request['response'] = user_response
        #             # Signal the waiting thread
        #             input_request['response_event'].set()
        #         elif input_request['type'] == 'price_prompt':
        #             rq_num = input_request['rq_num']
        #             item_name = input_request['item_name']
        #             # Prompt the user for the price
        #             price = input("Enter the price you want to offer: ")
        #             input_request['response'] = price
        #             # Signal the waiting thread
        #             input_request['response_event'].set()
        
        if not handle_search_active.is_set():
            # Display the search menu
            with input_lock:
                print("\nMarketplace Menu")
                print("1. Search for Item")
                print("3. Logout")
                choice = input("Enter your choice: ")

                if choice == "1":
                    # Existing code to search for an item
                    itemName = input("Enter the item name: ")
                    itemDescription = input("Enter the item description: ")
                    try:
                        maxPrice = float(input("Enter the maximum price: "))
                    except ValueError:
                        print("Invalid price. Please enter a number.")
                        continue
                    print(f"Searching for item: {itemName}, description: {itemDescription}, max price: {maxPrice}")
                    start_search_thread(
                        clientUdpSocket, client_name, itemName, itemDescription, maxPrice, serverAddr
                    )
                elif choice == "3":
                    print("Logging out...")
                    break  # Exit the search menu
                else:
                    print("Invalid choice. Please try again.")



def listen_for_search_messages(clientUdpSocket):
    print(f"Listening on {clientUdpSocket.getsockname()} for SEARCH messages...")
    while True:
        try:
            data, addr = clientUdpSocket.recvfrom(1024)
            message = data.decode()
            print(f"\nReceived message from {addr}: {message}")
            if message.startswith("SEARCH"):
                # Parse the SEARCH message
                parts = message.split(None, 3)
                if len(parts) == 4:
                    command, rq_num, item_name, item_description = parts
                    # Start a new thread to handle user interaction
                    user_thread = threading.Thread(
                        target=handle_search_message,
                        args=(clientUdpSocket, rq_num, item_name)
                    )
                    user_thread.start()
                else:
                    print("Invalid SEARCH message format.")
        except Exception as e:
            print(f"Error receiving data lfsm: {e}")
            break




def handle_search_message(clientUdpSocket, rq_num, item_name):
    global client_name
    handle_search_active.set()

    # handle_search_active = threading.Event()

    # Create a threading event
    response_event = threading.Event()    
    # Place a request in the input queue
    input_request = {
        'type': 'offer_prompt',
        'rq_num': rq_num,
        'item_name': item_name,
        'response_event': response_event,
        'response': None
    }
    input_queue.put((0,input_request))

    # Handle input requests directly
    while not input_queue.empty():
        priority, input_request = input_queue.get()
        with input_lock:
            if input_request['type'] == 'offer_prompt':
                rq_num = input_request['rq_num']
                item_name = input_request['item_name']
                # Prompt the user
                user_response = input(f"Do you want to offer '{item_name}'? (Y/N): ")
                input_request['response'] = user_response
                # Signal the waiting thread
                input_request['response_event'].set()
            elif input_request['type'] == 'price_prompt':
                rq_num = input_request['rq_num']
                item_name = input_request['item_name']
                # Prompt the user for the price
                price = input("Enter the price you want to offer: ")
                input_request['response'] = price
                # Signal the waiting thread
                input_request['response_event'].set()
    # Wait for the main thread to provide the response
    if not response_event.wait(timeout=15):
        print(f"No response for the SEARCH request {rq_num} within the time limit.")
        return

    user_response = input_request['response']

    if user_response is None:
        print(f"No response for the SEARCH request {rq_num}.")
        handle_search_active.clear()
        return
    elif user_response.upper() == 'Y':
        # Create another event for the price input
        price_event = threading.Event()
        price_request = {
            'type': 'price_prompt',
            'rq_num': rq_num,
            'item_name': item_name,
            'response_event': price_event,
            'response': None
        }
        input_queue.put((1,price_request))
        while not input_queue.empty():
            priority, input_request = input_queue.get()
            with input_lock:
                if input_request['type'] == 'offer_prompt':
                    rq_num = input_request['rq_num']
                    item_name = input_request['item_name']
                    # Prompt the user
                    user_response = input(f"Do you want to offer '{item_name}'? (Y/N): ")
                    input_request['response'] = user_response
                    # Signal the waiting thread
                    input_request['response_event'].set()
                elif input_request['type'] == 'price_prompt':
                    rq_num = input_request['rq_num']
                    item_name = input_request['item_name']
                    # Prompt the user for the price
                    price = input("Enter the price you want to offer: ")
                    input_request['response'] = price
                    # Signal the waiting thread
                    input_request['response_event'].set()
        if not price_event.wait():
            print("No price provided. Offer canceled.")
            handle_search_active.clear()

            return

        price = price_request['response']
        try:
            price = float(price)
        except ValueError:
            print("Invalid price entered. Offer canceled.")
            handle_search_active.clear()
            return
        # Construct and send the OFFER message
        offer_message = f"OFFER {rq_num} {client_name} {item_name} {price}"
        clientUdpSocket.sendto(offer_message.encode(), serverAddr)
        print(f"Sent OFFER to server: {offer_message}")
    else:
        print(f"You chose not to offer '{item_name}' for the SEARCH request {rq_num}.")
    handle_search_active.clear()        


if __name__ == "__main__":
    print("Client started.")
    registrationMenu()

    # Close the socket when done
    clientUdpSocket.close()
    # tcpSocket.close()
