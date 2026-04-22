"""
Dobot Nova 5 - PS5 DualSense joystick controller (dual mode).
Controls the robot over TCP/IP V4 using the MoveJog command.

Two control modes:
  [JOINT MODE] - Coarse positioning (J1-J6)
  [TOOL MODE]  - Fine adjustments around the tool center point

SHARE toggles between modes.

Control map:
  JOINT MODE:                      TOOL MODE:
  Left Stick Y : J1 base           Left Stick Y : X forward/back
  Left Stick X : J2 shoulder       Left Stick X : Y left/right
  Right Stick Y: J3 elbow          Right Stick Y: Z up/down
  Right Stick X: J4 wrist 1        Right Stick X: Rz rotation
  L2 / R2      : J5 wrist 2        L2 / R2      : Rx rotation
  D-Pad Y      : J6 tip rotation   D-Pad Y      : Ry rotation

  Buttons:
    SHARE          -> Switch mode (Joint <-> Tool)
    X (Cross)      -> Decrease speed
    Triangle       -> Increase speed
    Square         -> Stop robot
    Circle         -> Clear errors
    L1             -> Disable robot
    R1             -> Enable robot
    Options        -> Quit
    PS (Home)      -> Emergency stop
"""

import sys
import os


def _app_dir():
    """Return the correct base directory for both PyInstaller bundles and regular Python runs."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


_BASE_DIR = _app_dir()
sys.path.insert(0, os.path.join(_BASE_DIR, "TCP-IP-Python-V4"))

import pygame
from dobot_api import DobotApiDashboard
import time


# =============================================================================
# SETTINGS
# =============================================================================

import json as _json

SETTINGS_FILE = os.path.join(_BASE_DIR, "settings.json")
POSITIONS_FILE = os.path.join(_BASE_DIR, "positions.json")

_DEFAULTS = {
    "robot_ip": "192.168.5.1",
    "dashboard_port": 29999,
    "deadzone": 0.15,
    "loop_hz": 20,
    "speed_default": 30,
    "speed_min": 5,
    "speed_max": 100,
    "speed_step": 1,
    "jog_vel_joint": 50,
    "jog_acc_joint": 30,
    "jog_vel_linear": 50,
    "jog_acc_linear": 30,
    "tool_index": 1,
    "default_tool_distance": 350,
    "movj_speed": 30,
    "min_jog_hold": 0.15,
    "idle_before_stop": 0.15,
    "min_switch_time": 0.15
}


def _load_settings():
    """Load settings from settings.json; fall back to defaults and create the file if missing."""
    settings = dict(_DEFAULTS)
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                user = _json.load(f)
            settings.update(user)
        except Exception as e:
            print(f"[SETTINGS] Failed to read settings.json: {e}")
    else:
        with open(SETTINGS_FILE, 'w') as f:
            _json.dump(_DEFAULTS, f, indent=2)
        print(f"[SETTINGS] Created settings.json: {SETTINGS_FILE}")
    return settings


_S = _load_settings()

ROBOT_IP = _S["robot_ip"]
DASHBOARD_PORT = _S["dashboard_port"]
DEADZONE = _S["deadzone"]
LOOP_HZ = _S["loop_hz"]
SPEED_DEFAULT = _S["speed_default"]
SPEED_MIN = _S["speed_min"]
SPEED_MAX = _S["speed_max"]
SPEED_STEP = _S["speed_step"]
JOG_VEL_JOINT = _S["jog_vel_joint"]
JOG_ACC_JOINT = _S["jog_acc_joint"]
JOG_VEL_LINEAR = _S["jog_vel_linear"]
JOG_ACC_LINEAR = _S["jog_acc_linear"]
TOOL_INDEX = _S["tool_index"]
DEFAULT_TOOL_DISTANCE = _S["default_tool_distance"]
MOVJ_SPEED = _S["movj_speed"]
MIN_JOG_HOLD = _S["min_jog_hold"]
IDLE_BEFORE_STOP = _S["idle_before_stop"]
MIN_SWITCH_TIME = _S["min_switch_time"]

HOME_JOINTS = None
SURGERY_JOINTS = None

# PS5 DualSense button and axis indices - Windows and Linux differ
import platform as _platform
if _platform.system() == "Windows":
    # Windows (pygame 2.6 + DualSense - 17 buttons)
    # --- Verified test results ---
    BTN_CROSS      = 0    # Decrease speed
    BTN_CIRCLE     = 1    # Drag mode
    BTN_SQUARE     = 2    # EMERGENCY STOP
    BTN_TRIANGLE   = 3    # Increase speed
    BTN_SHARE      = 4    # Switch mode (matches Linux SHARE: toggle_mode)
    BTN_PS         = 5    # Unassigned (per user request)
    BTN_OPTIONS    = 6    # Stop (force_stop)
    BTN_L3         = 7    # Save Home (Linux L3)
    BTN_R3         = 8    # Save Surgery (Linux R3)
    BTN_L1         = 9    # Disable robot (Linux L1)
    BTN_R1         = 10   # Enable robot (Linux R1)
    BTN_DPAD_UP    = 11   # D-Pad up   -> J6+ (joint) / Rz+ (tool)
    BTN_DPAD_DOWN  = 12   # D-Pad down -> J6- (joint) / Rz- (tool)
    BTN_HOME_GO    = 13   # D-Pad left  -> go to HOME
    BTN_SURGERY_GO = 14   # D-Pad right -> go to SURGERY
    # B15: touchpad          (unassigned)
    # B16: microphone        captured by Windows OS, no event
    BTN_L2      = -91     # axis 4, not a button
    BTN_R2      = -92     # axis 5, not a button
else:
    # Linux SDL2
    BTN_CROSS      = 0
    BTN_CIRCLE     = 1
    BTN_TRIANGLE   = 2
    BTN_SQUARE     = 3
    BTN_L1         = 4
    BTN_R1         = 5
    BTN_L2         = 6
    BTN_R2         = 7
    BTN_SHARE      = 8
    BTN_OPTIONS    = 9
    BTN_PS         = 10
    BTN_L3         = 11
    BTN_R3         = 12
    BTN_HOME_GO    = -1  # Linux uses D-Pad (hat) events
    BTN_SURGERY_GO = -1
    BTN_DPAD_UP    = -1  # Linux uses hat[1]
    BTN_DPAD_DOWN  = -1

# Axis indices - Windows and Linux use different mappings
if _platform.system() == "Windows":
    # Windows: pygame DualSense axis order
    AXIS_LX = 0
    AXIS_LY = 1
    AXIS_RX = 2
    AXIS_RY = 3
    AXIS_L2 = 4
    AXIS_R2 = 5
else:
    # Linux SDL2
    AXIS_LX = 0
    AXIS_LY = 1
    AXIS_L2 = 2
    AXIS_RX = 3
    AXIS_RY = 4
    AXIS_R2 = 5

# Mode identifiers (internal). Use MODE_LABELS_TR to render them in Turkish in the GUI.
MODE_JOINT = "JOINT"
MODE_TOOL = "TOOL"

# Position identifiers (internal). Use POSITION_LABELS_TR for Turkish display.
POS_HOME = "HOME"
POS_SURGERY = "SURGERY"

# Turkish display labels for UI
MODE_LABELS_TR = {MODE_JOINT: "EKLEM", MODE_TOOL: "TOOL"}
POSITION_LABELS_TR = {POS_HOME: "HOME", POS_SURGERY: "AMELİYAT"}


# =============================================================================
# JOYSTICK CONTROLLER
# =============================================================================

class JoystickRobotController:
    def __init__(self, robot_ip=ROBOT_IP):
        self.robot_ip = robot_ip
        self.dashboard = None
        self.speed = SPEED_DEFAULT
        self.running = False
        self.active_jog = ""
        self.last_jog_start = 0
        self.idle_since = 0
        self.error_state = False
        self.mode = MODE_JOINT
        self.drag_active = False
        self.tool_distance = DEFAULT_TOOL_DISTANCE  # mm
        self.home_joints = None
        self.surgery_joints = None
        self._load_positions()

    def _load_positions(self):
        """Load saved poses, tool distance and speed from disk."""
        import json
        if os.path.exists(POSITIONS_FILE):
            try:
                with open(POSITIONS_FILE, 'r') as f:
                    data = json.load(f)
                self.home_joints = data.get("home")
                self.surgery_joints = data.get("surgery")
                self.tool_distance = data.get("tool_distance", DEFAULT_TOOL_DISTANCE)
                saved_speed = data.get("speed")
                if saved_speed is not None:
                    self.speed = max(SPEED_MIN, min(SPEED_MAX, int(saved_speed)))
                if self.home_joints:
                    print(f"[POSE] Home loaded: {self.home_joints}")
                if self.surgery_joints:
                    print(f"[POSE] Surgery loaded: {self.surgery_joints}")
                print(f"[POSE] Tool distance: {self.tool_distance}mm ({self.tool_distance/10:.0f}cm)")
                print(f"[POSE] Speed: %{self.speed}")
            except Exception as e:
                print(f"[POSE] Failed to read positions file: {e}")

    def _save_positions(self):
        """Persist poses, tool distance and speed to disk."""
        import json
        data = {
            "home": self.home_joints,
            "surgery": self.surgery_joints,
            "tool_distance": self.tool_distance,
            "speed": self.speed,
        }
        try:
            with open(POSITIONS_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[POSE] Failed to write positions file: {e}")

    def _read_current_joints(self):
        """Read the current joint angles and return them as a list."""
        import re
        resp = str(self._safe_cmd(self.dashboard.GetAngle))
        match = re.search(r'\{([^}]+)\}', resp)
        if match:
            return [round(float(x), 2) for x in match.group(1).split(',')]
        return None

    def save_home(self):
        """Save the current pose as HOME."""
        joints = self._read_current_joints()
        if joints:
            self.home_joints = joints
            self._save_positions()
            print(f"\n{'='*50}")
            print(f"  HOME POSE SAVED!")
            print(f"  {joints}")
            print(f"{'='*50}\n")
        else:
            print("[WARN] Could not read current pose")

    def save_surgery(self):
        """Save the current pose as SURGERY."""
        joints = self._read_current_joints()
        if joints:
            self.surgery_joints = joints
            self._save_positions()
            print(f"\n{'='*50}")
            print(f"  SURGERY POSE SAVED!")
            print(f"  {joints}")
            print(f"{'='*50}\n")
        else:
            print("[WARN] Could not read current pose")

    def set_tool_distance(self, distance_mm):
        """Update the tool distance and push it to the robot."""
        self.tool_distance = int(distance_mm)
        self._save_positions()
        self._apply_tool()
        print(f"[TOOL] Distance: {self.tool_distance}mm ({self.tool_distance/10:.0f}cm)")

    def _apply_tool(self):
        """Apply the current tool distance to the robot."""
        if not self.dashboard:
            return
        tool_cmd = f"SetTool({TOOL_INDEX},{{0.0,0.0,{float(self.tool_distance)},0.0,0.0,0.0}})"
        self._safe_cmd(self.dashboard.sendRecvMsg, tool_cmd)
        self._safe_cmd(self.dashboard.Tool, TOOL_INDEX)

    def _safe_cmd(self, func, *args):
        if not self.dashboard:
            print("[WARN] Robot not connected")
            return None
        try:
            return func(*args)
        except (ConnectionError, OSError, BrokenPipeError) as e:
            print(f"[ERROR] Connection lost: {e}")
            self.dashboard = None
            self.active_jog = ""
            return None

    def _parse_error_code(self, resp):
        if resp is None:
            return -999
        try:
            return int(str(resp).split(",")[0])
        except (ValueError, IndexError):
            return -999

    def connect(self):
        try:
            self.dashboard = DobotApiDashboard(self.robot_ip, DASHBOARD_PORT)
            print(f"[OK] Robot connection established: {self.robot_ip}")
            return True
        except Exception as e:
            print(f"[ERROR] Robot connection failed: {e}")
            return False

    def disconnect(self):
        self._force_stop()
        if self.dashboard:
            self.dashboard.close()
        print("[OK] Robot connection closed")

    def _force_stop(self):
        """Unconditionally stop the active jog."""
        if self.active_jog:
            self._safe_cmd(self.dashboard.MoveJog, "")
            self.active_jog = ""
            self.idle_since = 0

    def prepare_robot(self):
        """Prepare the robot: clear errors, enable, set speed, define tool."""
        print("[PREP] Preparing robot...")

        # Stop any running program (Mode 7 -> Mode 5)
        self._safe_cmd(self.dashboard.Stop)
        time.sleep(0.5)

        self._safe_cmd(self.dashboard.ClearError)
        time.sleep(0.5)
        self._safe_cmd(self.dashboard.SetCollisionLevel, 0)
        time.sleep(0.3)

        resp = self._safe_cmd(self.dashboard.EnableRobot)
        print(f"[PREP] EnableRobot: {resp}")
        time.sleep(1)

        self._safe_cmd(self.dashboard.SpeedFactor, self.speed)
        self._safe_cmd(self.dashboard.VelJ, JOG_VEL_JOINT)
        self._safe_cmd(self.dashboard.AccJ, JOG_ACC_JOINT)
        self._safe_cmd(self.dashboard.VelL, JOG_VEL_LINEAR)
        self._safe_cmd(self.dashboard.AccL, JOG_ACC_LINEAR)
        time.sleep(0.3)

        self._apply_tool()
        time.sleep(0.3)

        # Wait until Mode 5 (Idle/ready), up to 3 attempts
        ready = False
        for attempt in range(3):
            for _ in range(10):  # 5 s wait (10 x 0.5)
                mode_resp = str(self._safe_cmd(self.dashboard.RobotMode))
                if ",{5}," in mode_resp:
                    ready = True
                    break
                time.sleep(0.5)
            if ready:
                break
            # Still not Mode 5 -> clear errors + re-enable
            print(f"[PREP] Did not reach Mode 5 (attempt {attempt+1}), clearing errors...")
            self._safe_cmd(self.dashboard.ClearError)
            time.sleep(0.5)
            self._safe_cmd(self.dashboard.EnableRobot)
            time.sleep(1)

        mode = self._safe_cmd(self.dashboard.RobotMode)
        errors = self._safe_cmd(self.dashboard.GetErrorID)
        print(f"[PREP] Mode: {mode} | Errors: {errors}")

        self.error_state = False
        self.active_jog = ""
        print(f"[PREP] Speed: %{self.speed} | Tool: {TOOL_INDEX}")
        if ready:
            print("[PREP] Robot ready! (Mode 5 = Idle)")
        else:
            print("[WARN] Robot did not reach Mode 5. Check the physical E-stop or clear "
                  "any errors on the teach pendant, then retry.")

    def recover_from_error(self):
        print("[RECOVER] Error detected, recovering...")
        self.active_jog = ""
        self.prepare_robot()

    def toggle_mode(self):
        """Switch between Joint and Tool modes."""
        self._force_stop()
        time.sleep(0.1)

        if self.mode == MODE_JOINT:
            self.mode = MODE_TOOL
        else:
            self.mode = MODE_JOINT

        print(f"\n{'='*50}")
        print(f"  MODE SWITCHED -> [{self.mode}]")
        if self.mode == MODE_TOOL:
            print("  Left stick  : X/Y translation")
            print("  Right stick : Z translation + Rz rotation")
            print("  L2/R2       : Rx rotation")
            print("  D-Pad       : Ry rotation")
        else:
            print("  Left stick  : J1/J2")
            print("  Right stick : J3/J4")
            print("  L2/R2       : J5")
            print("  D-Pad       : J6")
        print(f"{'='*50}\n")

    def enable_robot(self):
        self.prepare_robot()

    def disable_robot(self):
        self._force_stop()
        resp = self._safe_cmd(self.dashboard.DisableRobot)
        print(f"[ROBOT] Disable: {resp}")

    def clear_error(self):
        self.prepare_robot()

    def toggle_drag(self):
        """Toggle drag mode. On exit, apply the tool offset from the current pose."""
        import re

        if not self.drag_active:
            # START DRAG
            self._force_stop()
            time.sleep(0.1)
            resp = self._safe_cmd(self.dashboard.StartDrag)
            print(f"\n{'='*50}")
            print(f"  DRAG MODE ACTIVE - drag the robot by hand!")
            print(f"  Press Circle again when done.")
            print(f"  StartDrag: {resp}")
            print(f"{'='*50}\n")
            self.drag_active = True
        else:
            # STOP DRAG + APPLY TOOL
            resp = self._safe_cmd(self.dashboard.StopDrag)
            print(f"[DRAG] StopDrag: {resp}")
            self.drag_active = False
            time.sleep(0.5)

            # Re-enable the robot (drag disables it)
            self._safe_cmd(self.dashboard.EnableRobot)
            time.sleep(1)

            # Read current pose
            pose_resp = str(self._safe_cmd(self.dashboard.GetPose))
            match = re.search(r'\{([^}]+)\}', pose_resp)

            if match:
                pose = [float(x) for x in match.group(1).split(',')]
                print(f"[DRAG] Released pose: X={pose[0]:.1f} Y={pose[1]:.1f} Z={pose[2]:.1f}")
                print(f"       Rx={pose[3]:.1f} Ry={pose[4]:.1f} Rz={pose[5]:.1f}")

                # Apply tool offset
                self._apply_tool()

                print(f"\n{'='*50}")
                print(f"  TOOL APPLIED!")
                print(f"  {self.tool_distance}mm ({self.tool_distance/10:.0f}cm) ahead of the flange")
                print(f"  Tool mode active - joystick now rotates around this point")
                print(f"{'='*50}\n")

                # Auto switch to Tool mode
                self.mode = MODE_TOOL
            else:
                print(f"[DRAG] Could not read pose: {pose_resp}")

            # Restore speed/acceleration settings
            self._safe_cmd(self.dashboard.SpeedFactor, self.speed)
            self._safe_cmd(self.dashboard.VelJ, JOG_VEL_JOINT)
            self._safe_cmd(self.dashboard.AccJ, JOG_ACC_JOINT)

    def set_speed(self, speed):
        new_speed = max(SPEED_MIN, min(SPEED_MAX, speed))
        if new_speed == self.speed:
            return
        self.speed = new_speed
        if self.dashboard:
            resp = self._safe_cmd(self.dashboard.SpeedFactor, self.speed)
            print(f"[SPEED] %{self.speed}  ({resp})")
        else:
            print(f"[SPEED] %{self.speed}")
        self._save_positions()

    def print_current_position(self):
        """Print the current pose to stdout (handy for copy/paste)."""
        import re
        angle_resp = str(self._safe_cmd(self.dashboard.GetAngle))
        pose_resp = str(self._safe_cmd(self.dashboard.GetPose))

        match = re.search(r'\{([^}]+)\}', angle_resp)
        if match:
            nums = [float(x) for x in match.group(1).split(',')]
            if len(nums) >= 6:
                print(f"\n{'='*50}")
                print(f"  CURRENT POSE")
                print(f"  Joints: [{nums[0]}, {nums[1]}, {nums[2]}, {nums[3]}, {nums[4]}, {nums[5]}]")
                print(f"  Pose:   {pose_resp}")
                print(f"  Copy and paste as HOME_JOINTS or SURGERY_JOINTS")
                print(f"{'='*50}\n")
                return
        print(f"[WARN] Could not read pose: {angle_resp}")

    def go_to_position(self, joints, name):
        """Use MovJ to move to a preset pose."""
        if joints is None:
            print(f"[WARN] {name} pose is not defined! Save it first.")
            return

        if not self.dashboard:
            print(f"[WARN] Robot not connected!")
            return

        self._force_stop()
        time.sleep(0.1)

        # Stop running program + clear errors (Mode 7 workaround)
        self._safe_cmd(self.dashboard.Stop)
        time.sleep(0.3)
        self._safe_cmd(self.dashboard.ClearError)
        time.sleep(0.3)
        self._safe_cmd(self.dashboard.EnableRobot)
        time.sleep(0.5)

        # Set speed
        self._safe_cmd(self.dashboard.SpeedFactor, MOVJ_SPEED)
        print(f"[MOVE] Going to {name} pose (speed: %{MOVJ_SPEED})...")
        print(f"  Target: {joints}")

        # MovJ in joint coordinates (coordinateMode=1 = joint)
        resp = self._safe_cmd(
            self.dashboard.MovJ,
            joints[0], joints[1], joints[2],
            joints[3], joints[4], joints[5], 1
        )
        err = self._parse_error_code(resp)
        print(f"[MOVE] MovJ: {resp}")

        if err == 0:
            print(f"[MOVE] Motion in progress...")
            time.sleep(1)
            # Wait for RobotMode 5 (motion complete); up to 15 s
            for _ in range(30):
                mode_resp = str(self._safe_cmd(self.dashboard.RobotMode))
                if ",{5}," in mode_resp:
                    break
                time.sleep(0.5)

            print(f"[MOVE] Reached {name} pose!")

            # Auto switch modes based on the target pose
            if name == POS_SURGERY:
                self.mode = MODE_TOOL
                print(f"\n{'='*50}")
                print(f"  SWITCHED TO TOOL MODE (surgery pose)")
                print(f"  Left stick  : X/Y translation")
                print(f"  Right stick : Z translation + Rz rotation")
                print(f"  L2/R2       : Rx rotation")
                print(f"  D-Pad       : Ry rotation")
                print(f"{'='*50}\n")
            elif name == POS_HOME:
                self.mode = MODE_JOINT
                print(f"  Switched to Joint mode.")

            # Restore previous speed
            self._safe_cmd(self.dashboard.SpeedFactor, self.speed)
        else:
            print(f"[MOVE] ERROR! MovJ failed: {err}")
            self._safe_cmd(self.dashboard.SpeedFactor, self.speed)

    def start_jog(self, axis_id):
        """Start a jog motion (parameters differ per mode)."""
        self.idle_since = 0

        if axis_id == self.active_jog:
            return

        if self.error_state:
            self.recover_from_error()
            return

        now = time.time()

        if self.active_jog:
            if now - self.last_jog_start < MIN_SWITCH_TIME:
                return
            self._safe_cmd(self.dashboard.MoveJog, "")
            time.sleep(0.05)

        self.active_jog = axis_id
        self.last_jog_start = now

        if self.mode == MODE_JOINT:
            # Joint mode: no coordtype
            resp = self._safe_cmd(self.dashboard.MoveJog, axis_id)
        else:
            # Tool mode:
            # Rotations (Rx/Ry/Rz) -> coordtype=1 (user) -> TCP fixed, flange rotates
            # Translations (X/Y/Z) -> coordtype=2 (tool) -> move along tool axes
            if axis_id.startswith("R"):
                resp = self._safe_cmd(self.dashboard.MoveJog, axis_id, 1, -1, TOOL_INDEX)
            else:
                resp = self._safe_cmd(self.dashboard.MoveJog, axis_id, 2, -1, TOOL_INDEX)

        err = self._parse_error_code(resp)
        print(f"[{self.mode}] MoveJog({axis_id}) -> {resp}")

        if err == -1:
            # -1 = command rejected (busy/in transition) - will retry
            self.active_jog = ""
        elif err != 0 and err != -2:
            # Serious error - recovery needed
            print(f"[{self.mode}] Serious error: {err}")
            self.active_jog = ""
            self.error_state = True

    def stop_jog(self):
        if not self.active_jog:
            return

        now = time.time()

        if now - self.last_jog_start < MIN_JOG_HOLD:
            return

        if self.idle_since == 0:
            self.idle_since = now
            return

        if now - self.idle_since < IDLE_BEFORE_STOP:
            return

        resp = self._safe_cmd(self.dashboard.MoveJog, "")
        print(f"[{self.mode}] STOP -> {resp}")
        self.active_jog = ""
        self.idle_since = 0

    def run(self):
        pygame.init()
        pygame.joystick.init()

        if pygame.joystick.get_count() == 0:
            print("[ERROR] No joystick detected!")
            return

        js = pygame.joystick.Joystick(0)
        js.init()
        print(f"[OK] Joystick: {js.get_name()}")
        print(f"     Axes: {js.get_numaxes()}, Buttons: {js.get_numbuttons()}")

        if not self.connect():
            return

        self.prepare_robot()

        self.running = True
        loop_delay = 1.0 / LOOP_HZ

        home_str = "SET" if self.home_joints else "UNSET"
        surg_str = "SET" if self.surgery_joints else "UNSET"

        print("\n" + "=" * 50)
        print(f"  JOYSTICK CONTROL ACTIVE [{self.mode} MODE]")
        print(f"  Home: {home_str} | Surgery: {surg_str}")
        print("=" * 50)
        print("  ---  POSITION  ---")
        print("  D-Pad Left   : Go to HOME pose")
        print("  D-Pad Right  : Go to SURGERY pose")
        print("  L3           : Save current pose as Home")
        print("  R3           : Save current pose as Surgery")
        print("  ---  JOINT MODE  ---")
        print("  Left stick   : J1 / J2")
        print("  Right stick  : J3 / J4")
        print("  L2/R2        : J5")
        print("  D-Pad Y      : J6")
        print("  ---  TOOL MODE  ---")
        print("  Left stick   : X / Y translation")
        print("  Right stick  : Z translation / Rz rotation")
        print("  L2/R2        : Rx rotation")
        print("  D-Pad Y      : Ry rotation")
        print("  ---  BUTTONS  ---")
        print("  SHARE        : Switch mode (Joint <-> Tool)")
        print("  Triangle/X   : Speed up/down")
        print("  Square       : Stop")
        print("  R1           : Enable + Prepare")
        print("  L1           : Disable")
        print("  Options      : Quit")
        print("  PS           : EMERGENCY STOP")
        print("=" * 50 + "\n")

        try:
            while self.running:
                for event in pygame.event.get():
                    if event.type == pygame.JOYBUTTONDOWN:
                        self._handle_button(event.button)
                    elif event.type == pygame.JOYHATMOTION:
                        self._handle_dpad(event.value)
                    elif event.type == pygame.QUIT:
                        self.running = False

                if not self.running:
                    break

                self._handle_axes(js)
                time.sleep(loop_delay)

        except KeyboardInterrupt:
            print("\n[!] Ctrl+C - shutting down...")
        finally:
            self._force_stop()
            self.disconnect()
            js.quit()
            pygame.quit()
            print("[OK] Program terminated")

    def _handle_button(self, button):
        _BTN_NAMES = {}
        # Only add valid (non-negative) constants to the label table
        for _btn, _lbl in (
            (BTN_CROSS, "x Cross"), (BTN_CIRCLE, "o Circle"),
            (BTN_SQUARE, "Square"), (BTN_TRIANGLE, "Triangle"),
            (BTN_L1, "L1"), (BTN_R1, "R1"),
            (BTN_L2, "L2"), (BTN_R2, "R2"),
            (BTN_SHARE, "SHARE"), (BTN_OPTIONS, "OPTIONS"),
            (BTN_L3, "L3"), (BTN_R3, "R3"), (BTN_PS, "PS"),
            (BTN_HOME_GO, "HOME_GO"), (BTN_SURGERY_GO, "SURGERY_GO"),
        ):
            if _btn >= 0 and _btn not in _BTN_NAMES:
                _BTN_NAMES[_btn] = f"{_lbl}(B{_btn})"
        name = _BTN_NAMES.get(button, f"B{button}(unassigned)")

        # Verify each target button is valid (>=0) before comparing
        def _is(target):
            return target >= 0 and button == target

        if _is(BTN_SQUARE):
            print(f"[BTN] {name} -> EMERGENCY STOP (Robot Disable)")
            self.disable_robot()
        elif _is(BTN_L1):
            print(f"[BTN] {name} -> Robot Disable (Linux: L1)")
            self.disable_robot()
        elif _is(BTN_R1):
            print(f"[BTN] {name} -> Robot Enable (Linux: R1)")
            self.enable_robot()
        elif _is(BTN_OPTIONS):
            print(f"[BTN] {name} -> Stop (MoveJog stop)")
            self._force_stop()
        elif _is(BTN_L3):
            print(f"[BTN] {name} -> Save Home pose")
            self.save_home()
        elif _is(BTN_R3):
            print(f"[BTN] {name} -> Save Surgery pose")
            self.save_surgery()
        elif _is(BTN_SHARE):
            print(f"[BTN] {name} -> Switch mode (Joint <-> Tool)")
            self.toggle_mode()
        elif _is(BTN_HOME_GO):
            print(f"[BTN] {name} -> Go to HOME pose")
            self.go_to_position(self.home_joints, POS_HOME)
        elif _is(BTN_SURGERY_GO):
            print(f"[BTN] {name} -> Go to SURGERY pose")
            self.go_to_position(self.surgery_joints, POS_SURGERY)
        elif _is(BTN_TRIANGLE):
            print(f"[BTN] {name} -> Speed up (%{self.speed} -> %{min(self.speed+SPEED_STEP, SPEED_MAX)})")
            self.set_speed(self.speed + SPEED_STEP)
        elif _is(BTN_CROSS):
            print(f"[BTN] {name} -> Speed down (%{self.speed} -> %{max(self.speed-SPEED_STEP, SPEED_MIN)})")
            self.set_speed(self.speed - SPEED_STEP)
        elif _is(BTN_CIRCLE):
            print(f"[BTN] {name} -> Drag mode")
            self.toggle_drag()
        elif _is(BTN_PS):
            print(f"[BTN] {name} -> (disabled)")
        elif _is(BTN_DPAD_UP) or _is(BTN_DPAD_DOWN):
            # D-Pad Y is polled continuously inside _handle_axes; no extra log
            pass
        else:
            print(f"[BTN] B{button} -> (unassigned)")

    def _handle_dpad(self, value):
        """Handle D-Pad events: left/right -> go to pose."""
        hat_x, hat_y = value
        if hat_x == -1:
            print("[D-PAD] Left -> Go to HOME pose")
            self.go_to_position(self.home_joints, POS_HOME)
        elif hat_x == 1:
            print("[D-PAD] Right -> Go to SURGERY pose")
            self.go_to_position(self.surgery_joints, POS_SURGERY)

    def _handle_axes(self, js):
        # Do not send jog commands while drag mode is active
        if self.drag_active:
            return

        lx = js.get_axis(AXIS_LX)
        ly = js.get_axis(AXIS_LY)
        rx = js.get_axis(AXIS_RX)
        ry = js.get_axis(AXIS_RY)
        l2 = js.get_axis(AXIS_L2)
        r2 = js.get_axis(AXIS_R2)
        hat = js.get_hat(0) if js.get_numhats() > 0 else (0, 0)

        # Platform-agnostic D-Pad Y synthesis:
        # Linux delivers hat[1]; Windows uses buttons 11/12.
        dpad_y = hat[1]
        if BTN_DPAD_UP >= 0 and js.get_button(BTN_DPAD_UP):
            dpad_y = 1
        elif BTN_DPAD_DOWN >= 0 and js.get_button(BTN_DPAD_DOWN):
            dpad_y = -1

        candidates = []

        if self.mode == MODE_JOINT:
            # --- JOINT MODE ---
            if abs(ly) > DEADZONE:
                candidates.append(("J1", abs(ly), "J1-" if ly > 0 else "J1+"))
            if abs(lx) > DEADZONE:
                candidates.append(("J2", abs(lx), "J2+" if lx > 0 else "J2-"))
            if abs(ry) > DEADZONE:
                candidates.append(("J3", abs(ry), "J3-" if ry > 0 else "J3+"))
            if abs(rx) > DEADZONE:
                candidates.append(("J4", abs(rx), "J4+" if rx > 0 else "J4-"))

            l2_val = (l2 + 1) / 2
            r2_val = (r2 + 1) / 2
            if l2_val > 0.3:
                candidates.append(("J5+", l2_val, "J5+"))
            if r2_val > 0.3:
                candidates.append(("J5-", r2_val, "J5-"))

            # D-Pad up/down -> J6 (left/right reserved for pose recall)
            if dpad_y != 0:
                candidates.append(("J6", 1.0, "J6+" if dpad_y > 0 else "J6-"))

        else:
            # --- TOOL MODE ---
            # Left stick: X/Y translation along tool axes
            if abs(ly) > DEADZONE:
                candidates.append(("X", abs(ly), "X-" if ly > 0 else "X+"))
            if abs(lx) > DEADZONE:
                candidates.append(("Y", abs(lx), "Y+" if lx > 0 else "Y-"))

            # Right stick Y: Z translation up/down
            if abs(ry) > DEADZONE:
                candidates.append(("Z", abs(ry), "Z-" if ry > 0 else "Z+"))

            # Right stick X: Ry rotation = head turn (TCP stays fixed)
            if abs(rx) > DEADZONE:
                candidates.append(("Ry", abs(rx), "Ry+" if rx > 0 else "Ry-"))

            # L2/R2: Rx rotation = head up/down (TCP stays fixed)
            l2_val = (l2 + 1) / 2
            r2_val = (r2 + 1) / 2
            if l2_val > 0.3:
                candidates.append(("Rx-", l2_val, "Rx-"))
            if r2_val > 0.3:
                candidates.append(("Rx+", r2_val, "Rx+"))

            # D-Pad Y: Rz rotation = head tilt
            if dpad_y != 0:
                candidates.append(("Rz", 1.0, "Rz+" if dpad_y > 0 else "Rz-"))

        if candidates:
            candidates.sort(key=lambda c: c[1], reverse=True)
            self.start_jog(candidates[0][2])
        else:
            self.stop_jog()


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    print("=" * 50)
    print("  Dobot Nova 5 - PS5 Joystick Controller")
    print("  Dual mode: Joint (J1-J6) + Tool (XYZ/rotation)")
    print("=" * 50)

    controller = JoystickRobotController(ROBOT_IP)
    controller.run()
