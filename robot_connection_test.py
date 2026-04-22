import json
import os
import socket
import time

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "settings.json")


def _load_robot_ip():
    try:
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f).get("robot_ip", "192.168.5.1")
    except (OSError, json.JSONDecodeError):
        return "192.168.5.1"


ROBOT_IP = _load_robot_ip()
DASHBOARD_PORT = 29999


def send_command(sock, cmd):
    sock.send(f"{cmd}\n".encode())
    time.sleep(0.5)
    response = sock.recv(4096).decode(errors="ignore")
    return response.strip()


def main():
    print(f"Dobot Nova 5 connection test - {ROBOT_IP}:{DASHBOARD_PORT}")
    print("-" * 50)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)

    try:
        sock.connect((ROBOT_IP, DASHBOARD_PORT))
        print("Connection successful!")

        # Query robot status
        print(f"\nRobotMode: {send_command(sock, 'RobotMode()')}")
        print(f"GetPose:   {send_command(sock, 'GetPose()')}")
        print(f"GetAngle:  {send_command(sock, 'GetAngle()')}")

    except socket.timeout:
        print("ERROR: Connection timed out!")
    except ConnectionRefusedError:
        print("ERROR: Connection refused! Is TCP/IP Remote Control enabled?")
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        sock.close()
        print("\nConnection closed.")


if __name__ == "__main__":
    main()
