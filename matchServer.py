import socket
import threading

HOST = "192.168.27.1"
PORT = 5000


def forward(src, dst, name):
    """Forwards data from src socket to dst socket."""
    while True:
        try:
            data = src.recv(4096)
            if not data:
                print(f"[{name}] disconnected.")
                dst.close()
                src.close()
                break
            dst.sendall(data)
        except:
            dst.close()
            src.close()
            break


print("[SERVER] Starting server...")
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(2)

print("[SERVER] Waiting for player 1...")
p1, addr1 = server.accept()
print(f"[SERVER] Player 1 connected from {addr1}")

print("[SERVER] Waiting for player 2...")
p2, addr2 = server.accept()
print(f"[SERVER] Player 2 connected from {addr2}")

print("[SERVER] Match started!")

# Create forwarding threads
t1 = threading.Thread(target=forward, args=(p1, p2, "P1→P2"))
t2 = threading.Thread(target=forward, args=(p2, p1, "P2→P1"))

t1.start()
t2.start()

t1.join()
t2.join()

server.close()
print("[SERVER] Match ended.")
