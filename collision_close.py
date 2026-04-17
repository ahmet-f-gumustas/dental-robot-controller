import json
import os
import socket
import time

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "settings.json")

def _load_robot_ip():
    try:
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f).get("robot_ip", "192.168.5.1")
    except (OSError, json.JSONDecodeError) as e:
        print(f"[AYAR] settings.json okunamadı, varsayılan IP kullanılacak: {e}")
        return "192.168.5.1"

ROBOT_IP = _load_robot_ip()
print(f"[AYAR] Robot IP: {ROBOT_IP}")

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
