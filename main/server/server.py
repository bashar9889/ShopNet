import threading
import socket
from search import *
from database import CreateDatabase, deleteTable, showUsers, get_cursor
from register import registerUser, deregisterUser, login_user

# Server Configuration
# UDP_IP = "172.30.40.10"  # The IP address for the server
UDP_PORT = 5005           # UDP port
TCP_PORT = 5006           # TCP port

def get_server_ip():
    try:
        # Create a temporary socket to find the IP address
        temp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Connect to a non-routable IP address; this does not send data
        temp_sock.connect(("8.8.8.8", 80))  # Google's DNS server
        ip_address = temp_sock.getsockname()[0]
        temp_sock.close()
        return ip_address
    except Exception as e:
        print(f"Error determining IP address: {e}")
        return "127.0.0.1"  # Fallback to localhost


UDP_IP = get_server_ip()  # Dynamically determine the server's IP
print(f"Server IP: {UDP_IP}")

# Initialize sockets
udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
offers_dict = {}
def setup_sockets():
    # Bind UDP socket
    udp_sock.bind((UDP_IP, UDP_PORT))
    print(f"Server is starting on UDP IP: {UDP_IP}:{UDP_PORT}")
    
    # Bind and listen on TCP socket
    tcp_sock.bind((UDP_IP, TCP_PORT))
    tcp_sock.listen() #tobe made to 20 clients
    print(f"Server is also starting on TCP IP: {UDP_IP}:{TCP_PORT}")

def initialize_database():
    # Ensure database is created fresh on each run
    CreateDatabase()


shutdown_flag = threading.Event()

# Handle incoming UDP messages
def udp_handler():
    

        
    while not shutdown_flag.is_set():
        # udp_sock.settimeout(1)
        try:
            data, addr = udp_sock.recvfrom(1024)
            print(f"UDP connection established with {addr}")
            process = threading.Thread(target=process_udp_message, args=(data, addr))
            process.start()

        except Exception as e:
            print(f"Error receiving UDP message: {e}")
            # break

# Process individual UDP message in a thread
def process_udp_message(data, addr):
    global offers_dict
    message = data.decode()
    print(f"Received message from {addr} via UDP: {message}")
    dataParts = message.split(" ")
    command = dataParts[0]

    if command == "REGISTER":
        name = dataParts[1]
        ipAddress = dataParts[2]
        udpSocket = dataParts[3]
        tcpSocket = dataParts[4]
        registerUser(name, ipAddress, udpSocket, tcpSocket, addr, udp_sock)
    elif command == "DEREGISTER":
        rqNum = int(dataParts[1])
        name = dataParts[2]
        deregisterUser(rqNum, name, addr, udp_sock)
    elif command == "LOGIN":
        name = dataParts[1]
        login_user(name, addr, udp_sock)    
    elif command == "LOOKING_FOR":
        lookup_req_num = int(dataParts[1])
        name = dataParts[2]
        itemName = dataParts[3]
        itemDescription = dataParts[4]
        maxPrice = float(dataParts[5])
        offers_dict[lookup_req_num] = {'offers': [], 'maxPrice': maxPrice}
        threading.Thread(target=searchItem, args=(name, itemName, itemDescription, maxPrice, addr, udp_sock)).start()
    elif command == "OFFER":
        rqNum = int(dataParts[1])
        seller_name = dataParts[2]
        item_name = dataParts[3]
        price = float(dataParts[4])
        store_offer(rqNum, seller_name, item_name, price, addr)
    elif command == "CANCEL":
        rqNum = int(dataParts[1])
        item_name = dataParts[2]
        price = float(dataParts[3])
        cancel_reservation(rqNum, item_name, price, addr)
    elif command == "BUY":
        rqNum = int(dataParts[1])
        item_name = dataParts[2]
        price = float(dataParts[3])
        finalize_purchase(rqNum, item_name, price, addr)        
    else:
        rqNum = -1  # default rqNum for invalid command
        response = f"INVALID-COMMAND {rqNum}"
        udp_sock.sendto(response.encode(), addr)  
    

def cancel_reservation(rqNum, item_name, price, buyer_addr):
    global offers_dict
    if rqNum in offers_dict:
        offers = offers_dict[rqNum]['offers']
        for offer in offers:
            seller_name, item_name, offer_price, seller_addr = offer
            if offer_price == price:
                cancel_message = f"CANCEL {rqNum} {item_name} {price}"
                udp_sock.sendto(cancel_message.encode(), seller_addr)
                print(f"Sent CANCEL message to {seller_addr}: {cancel_message}")
                break
        del offers_dict[rqNum]

def finalize_purchase(rqNum, item_name, price, buyer_addr):
    global offers_dict
    if rqNum in offers_dict:
        offers = offers_dict[rqNum]['offers']
        for offer in offers:
            seller_name, item_name, offer_price, seller_addr = offer
            if offer_price == price:
                buy_message = f"BUY {rqNum} {item_name} {price}"
                udp_sock.sendto(buy_message.encode(), seller_addr)
                print(f"Sent BUY message to {seller_addr}: {buy_message}")
                break
        del offers_dict[rqNum]


# Handle incoming TCP connections
def tcp_handler():
    while True:
        client_socket, client_address = tcp_sock.accept()
        print(f"TCP connection established with {client_address}")
        threading.Thread(target=process_tcp_connection, args=(client_socket, client_address)).start()

# Process individual TCP connection in a thread
def process_tcp_connection(client_socket, client_address):
    try:
        while True:
            data = client_socket.recv(1024).decode()
            if not data:
                break
            print(f"Received TCP message from {client_address}: {data}")
            # Process TCP message logic here
            # Example: handle INFORM_Req and INFORM_Res messages
            # respond to client if needed
    except Exception as e:
        print(f"Error handling TCP connection from {client_address}: {e}")
    finally:
        client_socket.close()
        print(f"Closed TCP connection with {client_address}")


# Close the server and sockets
def shutdown_server():
    conn, cursor = get_cursor()[0]
    conn.close()
    udp_sock.close()
    tcp_sock.close()

def main():
    setup_sockets()
    initialize_database()

    # Start UDP handler in a separate thread
    udp_thread = threading.Thread(target=udp_handler)
    udp_thread.start()
    
    try: 
         while True:
            pass
    except Exception as e:
        print("Shutting down the server...")
        shutdown_flag.set()  # Signal threads to exit
        udp_thread.join()    # Wait for the thread to finish
        shutdown_server()    # Close sockets and database
    # Uncomment and start TCP handler if needed
    tcp_thread = threading.Thread(target=tcp_handler)
    tcp_thread.start()
    udp_thread.join()
    tcp_thread.join()

if __name__ == "__main__":
    main()
