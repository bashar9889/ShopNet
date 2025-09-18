#register and d-register methods
from database import get_cursor, showUsers


request_number = 4


   # Register user
def registerUser(name, ipAddress, udpSocket, tcpSocket, addr, udp_sock):
    global request_number
    try:
        print(f"Attempting to register user: {name}")
        conn, cursor = get_cursor()

        # Check if the name already exists
        cursor.execute("SELECT id FROM users_new WHERE name=?", (name,))
        existing_user = cursor.fetchone()
        if existing_user:
            # If the name already exists, deny registration
            response = f"REGISTER-DENIED {existing_user[0]} Name-Already-Exists"
            
        else:
            # Insert the new user into the database without item-related fields
            cursor.execute(
                """
                INSERT INTO users_new (id, name, ipAddress, udpSocket, tcpSocket)
                VALUES (?, ?, ?, ?, ?)
                """,
                (request_number, name, ipAddress, int(udpSocket), int(tcpSocket)),
            )
            conn.commit()
            rqNum = cursor.lastrowid
            response = f"REGISTERED {request_number}"
            # request_number += 1
            

    except Exception as e:
        # rqNum = -1
        response = f"REGISTER-DENIED {request_number} Error-{str(e)}"

    # Send the response to the client
    udp_sock.sendto(response.encode(), addr)
    request_number+=1
    print(f"Response sent to {addr}: {response}")
    print(showUsers())


# Login user
def login_user(name, addr, udp_sock):
    global request_number

    try:
        conn, cursor = get_cursor()
        cursor.execute("SELECT id, ipAddress, udpSocket, tcpSocket FROM users_new WHERE name=?", (name,))
        user = cursor.fetchone()
        if user:
            user_id, ip_address, udp_socket, tcp_socket = user
            response = f"LOGIN-SUCCESS {name} {ip_address} {udp_socket} {tcp_socket}"
        else:
            response = f"LOGIN-FAILED User-Not-Found"
    except Exception as e:
        response = f"LOGIN-FAILED Error-{str(e)}"
    
    udp_sock.sendto(response.encode(), addr)
    print(f"Response sent to {addr}: {response}")

        
# Deregister user
def deregisterUser(rqNum, name, addr, udp_sock):
    try:
        conn, cursor = get_cursor()
        # Check if the user exists
        # i done made a mistake here smh, we check the table for the id by giving it value of rqNum
        # then we can delete it
        cursor.execute("SELECT * FROM users_new WHERE id=? AND name=?", (rqNum,name))
        if cursor.fetchone():
            # Delete the user from the database
            cursor.execute("DELETE FROM users_new WHERE id=? AND name=?", (rqNum,name))
            conn.commit()
            response = f"DEREGISTERED #{rqNum} {name}"
            
        else:
            response = f"DEREGISTER-DENIED {rqNum} {name} User-Not-Found"
    except Exception as e:
        response = f"DEREGISTER-DENIED {rqNum, name} Error-{str(e)}"

    # Send the response to the client
    udp_sock.sendto(response.encode(), addr)
    print(f"Response sent to {addr}: {response}")
  