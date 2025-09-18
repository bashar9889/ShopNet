import socket
from database import get_cursor
import threading
offers_dict = {}
# udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

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
    
udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_sock.bind((get_server_ip(), 0))
def searchItem(name, itemName, itemDescription, maxPrice, addr, sock):
    conn, cursor = get_cursor()
    cursor.execute("SELECT * FROM users_new WHERE name != ?", (name,))
    registeredPeers = cursor.fetchall()

    if not registeredPeers:
        response = f"NOT AVAILABLE 0 {itemName} {itemDescription} {maxPrice}"
        sock.sendto(response.encode(), addr)
        return

    searchRqNum = abs(hash((name, itemName, itemDescription, maxPrice)))
    searchMessage = f"SEARCH {searchRqNum} {itemName} {itemDescription} {maxPrice}"
    global offers_dict
    offers_dict[searchRqNum] = {'offers': [], 'maxPrice': maxPrice, 'buyer_addr': addr}
    # Send search message to all registered peers
    for peer in registeredPeers:
        peer_ip = peer[2]       # IP address of the peer
        peer_udp_port = peer[3] # UDP port of the peer
        peerAddress = (peer_ip, int(peer_udp_port))
        sock.sendto(searchMessage.encode(), peerAddress)
        print(f"Sent search request to {peer[1]} at {peer_ip}:{peer_udp_port}: {searchMessage}")
 

    threading.Timer(20, compare_offers, args=(searchRqNum, sock)).start()

def store_offer(rqNum, seller_name, item_name, price, addr):
    global offers_dict
    if rqNum in offers_dict:
        offers_dict[rqNum]['offers'].append((seller_name, item_name, price, addr))
        print(f"Stored offer for RQ# {rqNum} from {seller_name}: {item_name} at {price}")


def compare_offers(rqNum, sock):
    global offers_dict
    if rqNum not in offers_dict:
        return
    offers = offers_dict[rqNum]['offers']
    maxPrice = offers_dict[rqNum]['maxPrice']
    buyer_addr = offers_dict[rqNum]['buyer_addr']
    if not offers:
        response = f"NOT AVAILABLE {rqNum} {maxPrice}"
        sock.sendto(response.encode(), buyer_addr)
        print(f"Sent NOT AVAILABLE message to {buyer_addr}: {response}")
        return
    # Find the cheapest offer
    cheapest_offer = min(offers, key=lambda x: x[2])
    seller_name, item_name, price, addr = cheapest_offer
    # Compare the cheapest offer to the Max_price
    if price <= maxPrice:
        response = f"FOUND {rqNum} {item_name} {price}"
        sock.sendto(response.encode(), buyer_addr)
        print(f"Sent FOUND message to {buyer_addr}: {response}")
    else:
        response = f"NOT AVAILABLE {rqNum} {item_name} {maxPrice}"
        sock.sendto(response.encode(), buyer_addr)
        print(f"Sent NOT AVAILABLE message to {buyer_addr}: {response}")
    # Clean up the offers for this RQ#
    threading.Thread(target=wait_for_buyer_response, args=(rqNum, item_name, price, addr, buyer_addr)).start()


def wait_for_buyer_response(rqNum, item_name, price, seller_addr, buyer_addr):
    global offers_dict
    # Wait for buyer response (CANCEL or BUY)
    while True:
        data, addr = udp_sock.recvfrom(1024)
        message = data.decode()
        dataParts = message.split(" ")
        command = dataParts[0]
        if command == "CANCEL" and int(dataParts[1]) == rqNum:
            cancel_reservation(rqNum, item_name, price, buyer_addr)
            break
        elif command == "BUY" and int(dataParts[1]) == rqNum:
            finalize_purchase(rqNum, item_name, price, buyer_addr)
            break

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

def handle_seller_offers(searchRqNum, best_offer_item, maxPrice, sock, addr):
    conn, cursor = get_cursor()
    
    #sample  response only 
    sample_response = "ACCEPT"
    seller_name = best_offer_item[1]
    item_name = best_offer_item[5]
    item_description = best_offer_item[6]
    offer = best_offer_item[7]
    item = best_offer_item
    offer_under_max = []
    offer_over_equal_max = []
    
    nego_address = (best_offer_item[2], best_offer_item[3])
    
    # Check if the offer is higher than or equal to the max price
    if offer >= maxPrice:
        offer_over_equal_max.append(item)
        print(f"Offer from {seller_name} is higher than or equal to the max price: {offer} >= {maxPrice}")
        message = f"NEGOTIATE {searchRqNum} {item_name} {offer}"
        sock.sendto(message.encode(), nego_address)
        print(f"Sent negotiation request to {seller_name}: {message}")
        handle_negotiation_response(searchRqNum, item_name, maxPrice, sock, sample_response, nego_address, addr)
    elif offer < maxPrice:
        offer_under_max.append(item)
        print(f"Offer from {seller_name} is under the max price: {offer} < {maxPrice}")
        reserverMsg = f"RESERVE {searchRqNum} {item_name} {offer}"
        #rqNum here should be from client looking_for_item
        foundMsg = f"FOUND {searchRqNum} {item_name} {offer}"
        sock.sendto(reserverMsg.encode(), nego_address)
        sock.sendto(foundMsg.encode(), addr)
        print(f"Sent reservation request to {seller_name}: {reserverMsg}")
        
def handle_negotiation_response(searchRqNum, itemName, maxPrice, sock, response, nego_address, addr):
    if response == "ACCEPT":
        acceptMessage = f"ACCEPT {searchRqNum} {itemName} {maxPrice}"
        sock.sendto(acceptMessage.encode(),nego_address)
        print(f"Sent ACCEPT message to {nego_address}: {acceptMessage}")
        reserveMsg = f"FOUND {searchRqNum} {itemName} {maxPrice}"
        sock.sendto(reserveMsg.encode(), addr)
        print(f"Sent reservation request to {addr}: {reserveMsg}")
    elif response == "REFUSE":
        refuseMessage = f"REFUSE {searchRqNum} {itemName} {maxPrice}"
        sock.sendto(refuseMessage.encode(), nego_address)
        print(f"Sent REFUSE message to {nego_address}: {refuseMessage}")
        rejectMessage = f"NOT_FOUND {searchRqNum} {itemName} {maxPrice}"
        sock.sendto(rejectMessage.encode(), addr)
        