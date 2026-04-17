import socket
import time

ROBOT_IP = "192.168.5.1"
DASHBOARD_PORT = 29999

def send_command(sock, cmd):
    sock.send(f"{cmd}\n".encode())
    time.sleep(0.5)
    response = sock.recv(4096).decode(errors="ignore")
    return response.strip()

def main():
    print(f"Dobot Nova 5 bağlantı testi - {ROBOT_IP}:{DASHBOARD_PORT}")
    print("-" * 50)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)

    try:
        sock.connect((ROBOT_IP, DASHBOARD_PORT))
        print("Bağlantı başarılı!")

        # Robot durumunu sorgula
        print(f"\nRobotMode: {send_command(sock, 'RobotMode()')}")
        print(f"GetPose: {send_command(sock, 'GetPose()')}")
        print(f"GetAngle: {send_command(sock, 'GetAngle()')}")

    except socket.timeout:
        print("HATA: Bağlantı zaman aşımı!")
    except ConnectionRefusedError:
        print("HATA: Bağlantı reddedildi! TCP/IP Remote Control aktif mi?")
    except Exception as e:
        print(f"HATA: {e}")
    finally:
        sock.close()
        print("\nBağlantı kapatıldı.")

if __name__ == "__main__":
    main()
