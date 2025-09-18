# Peer-to-Peer Shopping System (P2S2)

## 📌 Overview
The **Peer-to-Peer Shopping System (P2S2)** is a distributed application built in **Python** that demonstrates real-world networking concepts with **UDP**, **TCP**, **multi-threading**, and **persistent state storage**.

It allows multiple peers (clients) to **search, offer, and purchase items** through a central **server** that manages registrations, item searches, negotiations, and purchase finalizations.

---

## 🚀 Features
- **Client Operations**
  - Register / De-register  
  - Login  
  - Search for items  
  - Offer items for sale  
  - Buy items from peers  

- **Server Operations**
  - Manage registrations and deregistrations  
  - Handle concurrent searches and offers  
  - Negotiate transactions between peers  
  - Finalize purchases securely over TCP  
  - Maintain persistent state with SQLite  

---

## 🏗️ System Architecture

### 🔹 Networking Model
- **UDP** → Lightweight, best-effort communication  
  - Used for registration, deregistration, and item searches  
- **TCP** → Reliable, connection-oriented communication  
  - Used for finalizing purchases (credit card info, shipping details)  

---

### 🔹 Concurrency & Responsiveness
- **Multi-threaded server** handles multiple client requests concurrently  
- **Thread-per-request model**: each UDP or TCP interaction is processed independently  
- **Timers** enforce offer expirations and transaction timeouts  
- Prevents blocking: misbehaving or slow clients cannot freeze the system  

---

### 🔹 Database Integration
- **SQLite** stores:  
  - Registered users (name, IP, UDP/TCP sockets)  
  - Transaction logs (offers, purchases, rejections)  
- **Crash Recovery**: system resumes with same state after restart  
- Lightweight schema optimized for performance and scalability  

---

### 🔹 Protocol Workflow
1. **Registration (UDP)**  
   - Client sends `REGISTER` → server replies `REGISTERED` or `REGISTER-DENIED`  
2. **Item Search (UDP)**  
   - Client sends `LOOKING_FOR` → server queries other peers → peers respond with `OFFER`  
3. **Negotiation (UDP)**  
   - If offers exceed buyer’s max price → server sends `NEGOTIATE`  
   - Sellers can `ACCEPT` or `REFUSE`  
4. **Purchase Finalization (TCP)**  
   - Buyer sends `BUY` → server opens TCP connections with buyer & seller  
   - Sensitive data (credit card, shipping address) exchanged securely  
   - Server applies a **transaction fee (10%)** and completes purchase  

---

## 🔬 Technical Highlights
- **Transport Layer Awareness**: UDP vs TCP separation for speed vs reliability  
- **Concurrency Model**: multi-threaded server with isolation between requests  
- **Timeout Handling**: timers for offers and TCP transactions  
- **Error Resilience**: malformed packets or DB errors handled gracefully  
- **Extensible Design**: can add authentication, GUI, or richer e-commerce features  

---



