import socket
import threading

def lookingForItem(clientSocket, name, itemName, itemDescription, maxPrice, serverAddr):
    # Generate the lookup request number based on the search criteria
    # Shall we add time to the hash function so lookupRqNum is unique?
    lookupRqNum = abs(hash((itemName, itemDescription, maxPrice)))
    message = f"LOOKING_FOR {lookupRqNum} {name} {itemName} {itemDescription} {maxPrice}"
    print(f"Sending search request: {message}")
    
    clientSocket.sendto(message.encode(), serverAddr)
    
    try:
        clientSocket.settimeout(25)  # Set the timeout to 1 second
        while True:
            responseData, responseAddr = clientSocket.recvfrom(1024)
            response = responseData.decode()
            print(f"Server response: {response}")

            # Split response and check the first part for type (OFFER, NOT AVAILABLE, END)
            response_parts = response.split()

            if len(response_parts) > 1:
                response_code = response_parts[0]
                response_rqnum = response_parts[1]
                # Check if the response contains the same search request number as the client sent
                if response_code == "OFFER" and response_rqnum == str(lookupRqNum):
                    # Check if this is the correct offer, and return it to the client
                    print(f"{lookupRqNum} Received offer from {responseAddr}: {response}")
                    # will add FOUND from server and seller side
                    if response_code == "FOUND":
                        handle_offer_response(clientSocket, lookupRqNum, response, serverAddr, itemName)
                    return response  # Return the offer to the client
                elif response_code == "NOT" and response_parts[2] == "AVAILABLE":
                    # Handle the case where no matching item was found
                    print(f"Item not available: {response}")
                    return response  # Return the NOT AVAILABLE response

                elif response_code == "END":
                    print("No more offers, search complete.")
                    return "END"  # Stop after receiving the END message
            else:
                print(f"Unexpected response format: {response}")
                return "Unexpected response format"
            
    except Exception as e:
        print("Request timed out")
        return "No offers received within the timeout period."
    finally:
        clientSocket.settimeout(None)  # Remove the timeout after search completes

# Run lookingForItem in a thread
def start_search_thread(clientSocket, name, itemName, itemDescription, maxPrice, serverAddr):
    search_thread = threading.Thread(
        target=lookingForItem, 
        args=(clientSocket, name, itemName, itemDescription, maxPrice, serverAddr),
        daemon=True
    )
    search_thread.start()
    print("Search thread started. You can continue with other tasks.")
    


def handle_offer_response(clientSocket, lookupRqNum, response, serverAddr, itemName):
    user_decision = input("Do you want to proceed with the purchase? (yes/no): ").strip().lower()
    if user_decision == "yes":
        print(f"Proceeding with the purchase of {itemName}.")
        proceed_message = f"BUY {lookupRqNum}"
        clientSocket.sendto(proceed_message.encode(), serverAddr)
    else:
        print(f"Cancelling the purchase of {itemName}.")
        cancel_message = f"CANCEL {lookupRqNum}"
        clientSocket.sendto(cancel_message.encode(), serverAddr)
        return response