"""
Singularity escape + Cartesian/Tool jog test.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "TCP-IP-Python-V4"))

import json
from dobot_api import DobotApiDashboard
from time import sleep

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "settings.json")


def _load_robot_ip():
    try:
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f).get("robot_ip", "192.168.5.1")
    except (OSError, json.JSONDecodeError):
        return "192.168.5.1"


ROBOT_IP = _load_robot_ip()

print("=" * 60)
print("  SINGULARITY ESCAPE + TOOL TEST")
print("=" * 60)

d = DobotApiDashboard(ROBOT_IP, 29999)
print(f"[OK] Connected: {ROBOT_IP}\n")

# --- PREP ---
print("[1] PREP")
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

# --- ROTATE J5 (ESCAPE SINGULARITY) ---
print("\n[2] ROTATE J5 (singularity escape - 5 seconds)")
print("  >>> Starting J5+...")
print(f"  MoveJog(J5+): {d.MoveJog('J5+')}")
sleep(5)
print(f"  MoveJog(STOP): {d.MoveJog('')}")
sleep(0.5)
print(f"  GetAngle: {d.GetAngle()}")
print(f"  RobotMode: {d.RobotMode()}")

# --- CARTESIAN JOG ---
print("\n[3] CARTESIAN JOG TEST")
print(f"  ClearError: {d.ClearError()}")
sleep(0.3)
print(f"  EnableRobot: {d.EnableRobot()}")
sleep(1.5)
print(f"  RobotMode: {d.RobotMode()}")

print("  >>> MoveJog(X+, coordtype=1)...")
print(f"  Result: {d.MoveJog('X+', 1)}")
sleep(0.5)
print(f"  RobotMode: {d.RobotMode()}")
print(f"  GetErrorID: {d.GetErrorID()}")
sleep(2)
print(f"  MoveJog(STOP): {d.MoveJog('')}")
sleep(0.5)

# --- DEFINE TOOL ---
print("\n[4] DEFINE TOOL")
print(f"  ClearError: {d.ClearError()}")
sleep(0.3)
print(f"  EnableRobot: {d.EnableRobot()}")
sleep(1)

# Dobot format: SetTool(index, {x,y,z,rx,ry,rz})
raw_cmd = 'SetTool(1,{0.0,0.0,0.0,0.0,0.0,0.0})'
print(f"  >>> Raw: {raw_cmd}")
print(f"  Result: {d.sendRecvMsg(raw_cmd)}")
sleep(0.3)
print(f"  Tool(1): {d.Tool(1)}")
sleep(0.3)

# --- TOOL JOG ---
print("\n[5] TOOL JOG TEST")
print(f"  ClearError: {d.ClearError()}")
sleep(0.3)
print(f"  EnableRobot: {d.EnableRobot()}")
sleep(1.5)
print(f"  RobotMode: {d.RobotMode()}")

print("  >>> MoveJog(X+, coordtype=2, tool=1)...")
print(f"  Result: {d.MoveJog('X+', 2, -1, 1)}")
sleep(0.5)
print(f"  RobotMode: {d.RobotMode()}")
print(f"  GetErrorID: {d.GetErrorID()}")
sleep(2)
print(f"  MoveJog(STOP): {d.MoveJog('')}")

# --- SUMMARY ---
print("\n" + "=" * 60)
print(f"  GetAngle: {d.GetAngle()}")
print(f"  GetPose: {d.GetPose()}")
print(f"  RobotMode: {d.RobotMode()}")
print(f"  GetErrorID: {d.GetErrorID()}")
print("=" * 60)

d.close()
