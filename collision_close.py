import socket
import time

ROBOT_IP = "192.168.5.3"

def send_command(sock, cmd):
    sock.send(f"{cmd}\n".encode())
    time.sleep(0.5)
    response = sock.recv(4096).decode(errors="ignore")
    return response.strip()

def try_port(port, commands):
    print(f"\n=== Port {port} ===")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    try:
        sock.connect((ROBOT_IP, port))
        print(f"Port {port} bağlantı OK")
        for cmd in commands:
            print(f"  {cmd}: {send_command(sock, cmd)}")
    except Exception as e:
        print(f"  Port {port} HATA: {e}")
    finally:
        sock.close()

commands = [
    "SetCollisionLevel(0)",
    "EnableSafeSkin(0)",
]

# Dashboard portu
try_port(29999, ["EnableRobot()"])
time.sleep(2)

# Move portu üzerinden dene
try_port(30004, commands)

# Dashboard üzerinden tekrar dene
try_port(29999, commands)

print("\nBitti.")
