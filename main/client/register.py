import socket

def get_local_ip():
    try:
        # Create a temporary socket to find the local IP address
        temp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # This doesn't need to connect; the IP is not actually used
        temp_socket.connect(("8.8.8.8", 80))
        local_ip = temp_socket.getsockname()[0]
        temp_socket.close()
        return local_ip
    except Exception as e:
        print(f"Error obtaining local IP address: {e}")
        return "127.0.0.1"  # Fallback to localhost if failed


def registerUser(name, ipAddress, clientSocket, tcpSocket, serverAddr):
    try:
        
        localIP = get_local_ip()
        udpPort = clientSocket.getsockname()[1]  # Get the assigned UDP port
        tcpPort = tcpSocket.getsockname()[1]  # Get the assigned TCP port
        message = f"REGISTER {name} {localIP} {udpPort} {tcpPort}"

        # Send the registration request to the server via UDP
        clientSocket.sendto(message.encode(), serverAddr)
        # Receive the server's response
        response, addr = clientSocket.recvfrom(1024)
        print("Server response:", response.decode())
         # Check if the registration was successful
        if response.decode().startswith("REGISTERED"):
            
            
            print("Registration successful.")
            print(f"Registered name: {name}")
            print(f"UDP port: {udpPort}")
            print(f"TCP port: {tcpPort}")
            print(f"IP address: {localIP}")
            return True
        else:
            print("Registration failed.")
            return False
    except Exception as e:
        print(f"Error registering user: {e}")
        return False
        
def loginUser(name, clientSocket, serverAddr):
    try:
        # Construct the LOGIN request
        message = f"LOGIN {name}"
        clientSocket.sendto(message.encode(), serverAddr)

        # Receive the server's response
        response, _ = clientSocket.recvfrom(1024)
        response_message = response.decode()
        print(f"Raw server response: {response_message}")


        if response_message.startswith("LOGIN-SUCCESS"):
            _, user_name, ip_address, udp_socket, tcp_socket = response_message.split(" ")
            print(f"Login successful!")
            print(f"User Details:\n- Name: {user_name}\n- IP Address: {ip_address}\n- UDP Socket: {udp_socket}\n- TCP Socket: {tcp_socket}")
            return True
        else:
            print(f"Server response: {response_message}")
            return False
    except Exception as e:
        print(f"Error during login: {e}")
        return False


def deregisterUser(rqNum, name, clientSocket, serverAddr):
    message = f"DEREGISTER {rqNum} {name}"
    clientSocket.sendto(message.encode(), (serverAddr))
    response, _ = clientSocket.recvfrom(1024)
    print("Server response:", response.decode())
