"""
Dobot Nova 5 - Teşhis Scripti
Robot neden hareket etmiyor / kırmızıya düşüyor araştırması
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "TCP-IP-Python-V4"))

from dobot_api import DobotApiDashboard
from time import sleep

ROBOT_IP = "192.168.5.1"

print("=" * 60)
print("  DOBOT NOVA 5 - TEŞHİS")
print("=" * 60)

dashboard = DobotApiDashboard(ROBOT_IP, 29999)
print(f"[OK] Bağlantı kuruldu: {ROBOT_IP}\n")

def cmd(label, func, *args):
    resp = func(*args)
    print(f"  {label}: {resp}")
    return resp

# 1. MEVCUT DURUM
print("[1] ROBOT DURUMU")
cmd("RobotMode", dashboard.RobotMode)
cmd("GetErrorID", dashboard.GetErrorID)
cmd("GetPose", dashboard.GetPose)
cmd("GetAngle", dashboard.GetAngle)

# 2. HATALARI TEMİZLE
print("\n[2] HATA TEMİZLEME")
cmd("ClearError", dashboard.ClearError)
sleep(0.5)
cmd("RobotMode (sonra)", dashboard.RobotMode)
cmd("GetErrorID (sonra)", dashboard.GetErrorID)

# 3. GÜVENLİK AYARLARI
print("\n[3] GÜVENLİK AYARLARI")
cmd("SetCollisionLevel(0)", dashboard.SetCollisionLevel, 0)
cmd("EnableSafeSkin(0)", dashboard.EnableSafeSkin, 0)
cmd("SetBackDistance(0)", dashboard.SetBackDistance, 0)
cmd("SetPostCollisionMode(1)", dashboard.SetPostCollisionMode, 1)  # pause mode

# 4. ENABLE
print("\n[4] ENABLE")
cmd("EnableRobot", dashboard.EnableRobot)
sleep(2)
cmd("RobotMode (enable sonrası)", dashboard.RobotMode)
cmd("GetErrorID (enable sonrası)", dashboard.GetErrorID)

# 5. HIZ ÇOK DÜŞÜK AYARLA
print("\n[5] HIZ AYARLARI")
cmd("SpeedFactor(5)", dashboard.SpeedFactor, 5)
cmd("VelJ(10)", dashboard.VelJ, 10)
cmd("AccJ(10)", dashboard.AccJ, 10)
cmd("VelL(10)", dashboard.VelL, 10)
cmd("AccL(10)", dashboard.AccL, 10)

# 6. JOG TESTİ - TEK EKSEN
print("\n[6] JOG TESTİ")
print("  >>> MoveJog(J1+) gönderiliyor (3 saniye)...")
resp = dashboard.MoveJog("J1+")  # Eklem koordinatı (coordtype yok)
print(f"  MoveJog(J1+): {resp}")

sleep(0.5)
cmd("RobotMode (jog sırasında)", dashboard.RobotMode)
cmd("GetErrorID (jog sırasında)", dashboard.GetErrorID)

sleep(2.5)
resp = dashboard.MoveJog("")
print(f"  MoveJog(STOP): {resp}")

sleep(0.5)
cmd("RobotMode (jog sonrası)", dashboard.RobotMode)
cmd("GetErrorID (jog sonrası)", dashboard.GetErrorID)

# 7. JOG TESTİ - KARTEZYEN
print("\n[7] KARTEZYEN JOG TESTİ")
# Önce tekrar enable et (hata olduysa)
cmd("ClearError", dashboard.ClearError)
sleep(0.5)
cmd("EnableRobot", dashboard.EnableRobot)
sleep(1)
cmd("RobotMode", dashboard.RobotMode)

print("  >>> MoveJog(X+, coordtype=1) gönderiliyor (3 saniye)...")
resp = dashboard.MoveJog("X+", 1)
print(f"  MoveJog(X+, coordtype=1): {resp}")

sleep(0.5)
cmd("RobotMode (jog sırasında)", dashboard.RobotMode)
cmd("GetErrorID (jog sırasında)", dashboard.GetErrorID)

sleep(2.5)
resp = dashboard.MoveJog("")
print(f"  MoveJog(STOP): {resp}")

sleep(0.5)
cmd("RobotMode (jog sonrası)", dashboard.RobotMode)
cmd("GetErrorID (jog sonrası)", dashboard.GetErrorID)
cmd("GetPose (final)", dashboard.GetPose)

print("\n" + "=" * 60)
print("  TEŞHİS TAMAMLANDI")
print("=" * 60)

dashboard.close()
