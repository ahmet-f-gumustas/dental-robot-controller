"""
Dobot Nova 5 - diagnostics script.
Investigates why the robot refuses to move or drops into the error state.
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
print("  DOBOT NOVA 5 - DIAGNOSTICS")
print("=" * 60)

dashboard = DobotApiDashboard(ROBOT_IP, 29999)
print(f"[OK] Connected: {ROBOT_IP}\n")


def cmd(label, func, *args):
    resp = func(*args)
    print(f"  {label}: {resp}")
    return resp


# 1. CURRENT STATE
print("[1] ROBOT STATE")
cmd("RobotMode", dashboard.RobotMode)
cmd("GetErrorID", dashboard.GetErrorID)
cmd("GetPose", dashboard.GetPose)
cmd("GetAngle", dashboard.GetAngle)

# 2. CLEAR ERRORS
print("\n[2] CLEAR ERRORS")
cmd("ClearError", dashboard.ClearError)
sleep(0.5)
cmd("RobotMode (after)", dashboard.RobotMode)
cmd("GetErrorID (after)", dashboard.GetErrorID)

# 3. SAFETY SETTINGS
print("\n[3] SAFETY SETTINGS")
cmd("SetCollisionLevel(0)", dashboard.SetCollisionLevel, 0)
cmd("EnableSafeSkin(0)", dashboard.EnableSafeSkin, 0)
cmd("SetBackDistance(0)", dashboard.SetBackDistance, 0)
cmd("SetPostCollisionMode(1)", dashboard.SetPostCollisionMode, 1)  # pause mode

# 4. ENABLE
print("\n[4] ENABLE")
cmd("EnableRobot", dashboard.EnableRobot)
sleep(2)
cmd("RobotMode (after enable)", dashboard.RobotMode)
cmd("GetErrorID (after enable)", dashboard.GetErrorID)

# 5. LOW SPEED SETTINGS
print("\n[5] SPEED SETTINGS")
cmd("SpeedFactor(5)", dashboard.SpeedFactor, 5)
cmd("VelJ(10)", dashboard.VelJ, 10)
cmd("AccJ(10)", dashboard.AccJ, 10)
cmd("VelL(10)", dashboard.VelL, 10)
cmd("AccL(10)", dashboard.AccL, 10)

# 6. JOG TEST - SINGLE AXIS
print("\n[6] JOG TEST")
print("  >>> Sending MoveJog(J1+) for 3 seconds...")
resp = dashboard.MoveJog("J1+")  # Joint coordinates (no coordtype)
print(f"  MoveJog(J1+): {resp}")

sleep(0.5)
cmd("RobotMode (during jog)", dashboard.RobotMode)
cmd("GetErrorID (during jog)", dashboard.GetErrorID)

sleep(2.5)
resp = dashboard.MoveJog("")
print(f"  MoveJog(STOP): {resp}")

sleep(0.5)
cmd("RobotMode (after jog)", dashboard.RobotMode)
cmd("GetErrorID (after jog)", dashboard.GetErrorID)

# 7. JOG TEST - CARTESIAN
print("\n[7] CARTESIAN JOG TEST")
# Re-enable in case an error triggered
cmd("ClearError", dashboard.ClearError)
sleep(0.5)
cmd("EnableRobot", dashboard.EnableRobot)
sleep(1)
cmd("RobotMode", dashboard.RobotMode)

print("  >>> Sending MoveJog(X+, coordtype=1) for 3 seconds...")
resp = dashboard.MoveJog("X+", 1)
print(f"  MoveJog(X+, coordtype=1): {resp}")

sleep(0.5)
cmd("RobotMode (during jog)", dashboard.RobotMode)
cmd("GetErrorID (during jog)", dashboard.GetErrorID)

sleep(2.5)
resp = dashboard.MoveJog("")
print(f"  MoveJog(STOP): {resp}")

sleep(0.5)
cmd("RobotMode (after jog)", dashboard.RobotMode)
cmd("GetErrorID (after jog)", dashboard.GetErrorID)
cmd("GetPose (final)", dashboard.GetPose)

print("\n" + "=" * 60)
print("  DIAGNOSTICS COMPLETE")
print("=" * 60)

dashboard.close()
