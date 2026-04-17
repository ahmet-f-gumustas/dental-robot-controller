"""
Singularity kaçış + Kartezyen/Tool jog testi
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "TCP-IP-Python-V4"))

from dobot_api import DobotApiDashboard
from time import sleep

ROBOT_IP = "192.168.5.1"

print("=" * 60)
print("  SİNGULARİTY KAÇIŞ + TOOL TESTİ")
print("=" * 60)

d = DobotApiDashboard(ROBOT_IP, 29999)
print(f"[OK] Bağlantı: {ROBOT_IP}\n")

# --- HAZIRLIK ---
print("[1] HAZIRLIK")
print(f"  ClearError: {d.ClearError()}")
sleep(0.5)
print(f"  SetCollisionLevel(0): {d.SetCollisionLevel(0)}")
print(f"  EnableRobot: {d.EnableRobot()}")
sleep(1.5)
print(f"  SpeedFactor(20): {d.SpeedFactor(20)}")
print(f"  VelJ(30): {d.VelJ(30)}")
print(f"  AccJ(20): {d.AccJ(20)}")

print(f"\n  RobotMode: {d.RobotMode()}")
print(f"  GetAngle: {d.GetAngle()}")
print(f"  GetPose: {d.GetPose()}")

# --- J5 DÖNDÜR (SİNGULARİTY KAÇIŞ) ---
print("\n[2] J5 DÖNDÜRME (singularity kaçış - 5 saniye)")
print("  >>> J5+ başlatılıyor...")
print(f"  MoveJog(J5+): {d.MoveJog('J5+')}")
sleep(5)
print(f"  MoveJog(STOP): {d.MoveJog('')}")
sleep(0.5)
print(f"  GetAngle: {d.GetAngle()}")
print(f"  RobotMode: {d.RobotMode()}")

# --- KARTEZYEN JOG ---
print("\n[3] KARTEZYEN JOG TESTİ")
print(f"  ClearError: {d.ClearError()}")
sleep(0.3)
print(f"  EnableRobot: {d.EnableRobot()}")
sleep(1.5)
print(f"  RobotMode: {d.RobotMode()}")

print("  >>> MoveJog(X+, coordtype=1)...")
print(f"  Sonuç: {d.MoveJog('X+', 1)}")
sleep(0.5)
print(f"  RobotMode: {d.RobotMode()}")
print(f"  GetErrorID: {d.GetErrorID()}")
sleep(2)
print(f"  MoveJog(STOP): {d.MoveJog('')}")
sleep(0.5)

# --- TOOL TANIMLA ---
print("\n[4] TOOL TANIMLA")
print(f"  ClearError: {d.ClearError()}")
sleep(0.3)
print(f"  EnableRobot: {d.EnableRobot()}")
sleep(1)

# Dobot format: SetTool(index, {x,y,z,rx,ry,rz})
raw_cmd = 'SetTool(1,{0.0,0.0,0.0,0.0,0.0,0.0})'
print(f"  >>> Raw: {raw_cmd}")
print(f"  Sonuç: {d.sendRecvMsg(raw_cmd)}")
sleep(0.3)
print(f"  Tool(1): {d.Tool(1)}")
sleep(0.3)

# --- TOOL JOG ---
print("\n[5] TOOL JOG TESTİ")
print(f"  ClearError: {d.ClearError()}")
sleep(0.3)
print(f"  EnableRobot: {d.EnableRobot()}")
sleep(1.5)
print(f"  RobotMode: {d.RobotMode()}")

print("  >>> MoveJog(X+, coordtype=2, tool=1)...")
print(f"  Sonuç: {d.MoveJog('X+', 2, -1, 1)}")
sleep(0.5)
print(f"  RobotMode: {d.RobotMode()}")
print(f"  GetErrorID: {d.GetErrorID()}")
sleep(2)
print(f"  MoveJog(STOP): {d.MoveJog('')}")

# --- SONUÇ ---
print("\n" + "=" * 60)
print(f"  GetAngle: {d.GetAngle()}")
print(f"  GetPose: {d.GetPose()}")
print(f"  RobotMode: {d.RobotMode()}")
print(f"  GetErrorID: {d.GetErrorID()}")
print("=" * 60)

d.close()
