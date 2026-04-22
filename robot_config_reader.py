"""
CR20A robot configuration reader.
Pulls robot information over the TCP/IP V4 protocol.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "TCP-IP-Python-V4"))

from dobot_api import DobotApiDashboard, DobotApiFeedBack, MyType
import numpy as np
import re
import json
from time import sleep


class RobotConfigReader:
    def __init__(self, ip="192.168.5.3"):
        self.ip = ip
        self.dashboard = None
        self.feed = None

    def connect(self):
        try:
            self.dashboard = DobotApiDashboard(self.ip, 29999)
            self.feed = DobotApiFeedBack(self.ip, 30004)
            print(f"CR20A ({self.ip}) connected successfully")
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False

    def disconnect(self):
        if self.dashboard:
            self.dashboard.close()
        if self.feed:
            self.feed.close()
        print("Connection closed")

    def parse_response(self, response):
        """Parse a Dobot response string."""
        if not response:
            return None
        if isinstance(response, bytes):
            response = response.decode('utf-8', errors='ignore')
        return response.strip().rstrip(';')

    def _safe_resp(self, response):
        """Always return the response as a string."""
        if not response:
            return ""
        if isinstance(response, bytes):
            return response.decode('utf-8', errors='ignore')
        return str(response)

    def _extract_nums(self, resp):
        """Pull numbers out of a response string."""
        return re.findall(r'-?\d+\.?\d*', self._safe_resp(resp))

    # =========================================================================
    # 1. BASIC STATE
    # =========================================================================

    def get_robot_mode(self):
        """Robot mode (1-11)."""
        resp = self._safe_resp(self.dashboard.RobotMode())
        parsed = self.parse_response(resp)
        print(f"  Robot Mode: {parsed}")
        modes = {
            1: "INIT", 2: "BRAKE_OPEN", 3: "POWEROFF",
            4: "DISABLED", 5: "ENABLE (ready)", 6: "BACKDRIVE (drag)",
            7: "RUNNING", 8: "SINGLE_MOVE (jog)", 9: "ERROR",
            10: "PAUSE", 11: "COLLISION"
        }
        nums = re.findall(r'-?\d+', resp)
        if len(nums) >= 2:
            mode_val = int(nums[1])
            print(f"    -> {modes.get(mode_val, 'UNKNOWN')}")
        return resp

    def get_pose(self):
        """Cartesian pose (X, Y, Z, Rx, Ry, Rz)."""
        resp = self._safe_resp(self.dashboard.GetPose())
        print(f"  Pose (X,Y,Z,Rx,Ry,Rz): {self.parse_response(resp)}")
        return resp

    def get_angle(self):
        """Joint angles (J1-J6)."""
        resp = self._safe_resp(self.dashboard.GetAngle())
        print(f"  Angles (J1-J6): {self.parse_response(resp)}")
        return resp

    def get_error_id(self):
        """Active error IDs."""
        resp = self._safe_resp(self.dashboard.GetErrorID())
        print(f"  Error IDs: {self.parse_response(resp)}")
        return resp

    def get_current_command_id(self):
        """ID of the command currently being executed."""
        resp = self._safe_resp(self.dashboard.GetCurrentCommandID())
        print(f"  Current Command ID: {self.parse_response(resp)}")
        return resp

    # =========================================================================
    # 2. I/O STATES
    # =========================================================================

    def get_digital_outputs(self, count=16):
        """Read DO states (CR20A: 24 DO)."""
        print(f"  Digital Outputs (DO1-DO{count}):")
        results = {}
        for i in range(1, count + 1):
            resp = self._safe_resp(self.dashboard.GetDO(i))
            nums = re.findall(r'-?\d+', resp)
            if len(nums) >= 2:
                status = int(nums[1])
                results[f"DO{i}"] = status
                state_str = "ON" if status == 1 else "OFF"
                print(f"    DO{i}: {state_str}")
        return results

    def get_digital_inputs(self, count=16):
        """Read DI states (CR20A: 32 DI)."""
        print(f"  Digital Inputs (DI1-DI{count}):")
        results = {}
        for i in range(1, count + 1):
            resp = self._safe_resp(self.dashboard.DI(i))
            nums = re.findall(r'-?\d+', resp)
            if len(nums) >= 2:
                status = int(nums[1])
                results[f"DI{i}"] = status
                state_str = "ON" if status == 1 else "OFF"
                print(f"    DI{i}: {state_str}")
        return results

    def get_analog_inputs(self, count=2):
        """Read AI states."""
        print(f"  Analog Inputs (AI1-AI{count}):")
        results = {}
        for i in range(1, count + 1):
            resp = self._safe_resp(self.dashboard.AI(i))
            print(f"    AI{i}: {self.parse_response(resp)}")
            results[f"AI{i}"] = resp
        return results

    def get_analog_outputs(self, count=2):
        """Read AO states."""
        print(f"  Analog Outputs (AO1-AO{count}):")
        results = {}
        for i in range(1, count + 1):
            resp = self._safe_resp(self.dashboard.GetAO(i))
            print(f"    AO{i}: {self.parse_response(resp)}")
            results[f"AO{i}"] = resp
        return results

    def get_do_group_dec(self, start_index=1, count=16):
        """Read a DO group as a decimal value."""
        print(f"  DO Group DEC (start={start_index}, count={count}):")
        try:
            resp = self._safe_resp(self.dashboard.GetDOGroupDEC(start_index, count))
            print(f"    DOGroupDEC: {self.parse_response(resp)}")
            return resp
        except Exception as e:
            print(f"    DOGroupDEC error: {e}")
            return None

    # =========================================================================
    # 3. TOOL I/O
    # =========================================================================

    def get_tool_io(self):
        """Read tool-end DI/DO states."""
        print("  Tool I/O:")
        results = {}
        for i in range(1, 3):
            try:
                resp_di = self._safe_resp(self.dashboard.ToolDI(i))
                print(f"    ToolDI{i}: {self.parse_response(resp_di)}")
                results[f"ToolDI{i}"] = resp_di
            except:
                pass
            try:
                resp_do = self._safe_resp(self.dashboard.GetToolDO(i))
                print(f"    ToolDO{i}: {self.parse_response(resp_do)}")
                results[f"ToolDO{i}"] = resp_do
            except:
                pass
        # Tool AI
        for i in range(1, 3):
            try:
                resp_ai = self._safe_resp(self.dashboard.ToolAI(i))
                print(f"    ToolAI{i}: {self.parse_response(resp_ai)}")
                results[f"ToolAI{i}"] = resp_ai
            except:
                pass
        return results

    # =========================================================================
    # 4. KINEMATICS
    # =========================================================================

    def get_positive_kin(self, j1, j2, j3, j4, j5, j6):
        """Forward kinematics: joint angles -> Cartesian pose."""
        print(f"  PositiveKin({j1},{j2},{j3},{j4},{j5},{j6}):")
        resp = self._safe_resp(self.dashboard.PositiveKin(j1, j2, j3, j4, j5, j6))
        print(f"    Result: {self.parse_response(resp)}")
        return resp

    def get_inverse_kin(self, x, y, z, rx, ry, rz):
        """Inverse kinematics: Cartesian pose -> joint angles."""
        print(f"  InverseKin({x},{y},{z},{rx},{ry},{rz}):")
        resp = self._safe_resp(self.dashboard.InverseKin(x, y, z, rx, ry, rz))
        print(f"    Result: {self.parse_response(resp)}")
        return resp

    def get_positive_kin_current(self):
        """Compute Cartesian pose from the current joint angles."""
        print("  PositiveKin (from current joints):")
        angle_resp = self._safe_resp(self.dashboard.GetAngle())
        nums = re.findall(r'-?\d+\.?\d*', angle_resp)
        if len(nums) >= 8:  # ErrorID + {6 joints}
            joints = [float(nums[i]) for i in range(2, 8)]
            resp = self._safe_resp(self.dashboard.PositiveKin(*joints))
            print(f"    Joints:    {joints}")
            print(f"    Cartesian: {self.parse_response(resp)}")
            return resp
        print("    Could not read joint angles")
        return None

    # =========================================================================
    # 5. REACHABILITY CHECKS
    # =========================================================================

    def check_movj_reachable(self, j1a, j2a, j3a, j4a, j5a, j6a,
                              j1b, j2b, j3b, j4b, j5b, j6b):
        """Can a MovJ motion be performed between two points?"""
        print(f"  CheckOddMovJ:")
        print(f"    A: [{j1a},{j2a},{j3a},{j4a},{j5a},{j6a}]")
        print(f"    B: [{j1b},{j2b},{j3b},{j4b},{j5b},{j6b}]")
        resp = self._safe_resp(self.dashboard.CheckOddMovJ(
            j1a, j2a, j3a, j4a, j5a, j6a, j1b, j2b, j3b, j4b, j5b, j6b))
        print(f"    Result: {self.parse_response(resp)}")
        return resp

    def check_movl_reachable(self, j1a, j2a, j3a, j4a, j5a, j6a,
                              j1b, j2b, j3b, j4b, j5b, j6b):
        """Can a MovL (straight line) motion be performed between two points?"""
        print(f"  CheckOddMovL:")
        print(f"    A: [{j1a},{j2a},{j3a},{j4a},{j5a},{j6a}]")
        print(f"    B: [{j1b},{j2b},{j3b},{j4b},{j5b},{j6b}]")
        resp = self._safe_resp(self.dashboard.CheckOddMovL(
            j1a, j2a, j3a, j4a, j5a, j6a, j1b, j2b, j3b, j4b, j5b, j6b))
        print(f"    Result: {self.parse_response(resp)}")
        return resp

    def check_movc_reachable(self, j1a, j2a, j3a, j4a, j5a, j6a,
                              j1b, j2b, j3b, j4b, j5b, j6b,
                              j1c, j2c, j3c, j4c, j5c, j6c):
        """Can an arc motion through three points be performed?"""
        print(f"  CheckOddMovC:")
        resp = self._safe_resp(self.dashboard.CheckOddMovC(
            j1a, j2a, j3a, j4a, j5a, j6a,
            j1b, j2b, j3b, j4b, j5b, j6b,
            j1c, j2c, j3c, j4c, j5c, j6c))
        print(f"    Result: {self.parse_response(resp)}")
        return resp

    # =========================================================================
    # 6. FORCE SENSOR (supported by CR20A)
    # =========================================================================

    def get_force(self):
        """TCP force and torque (Fx,Fy,Fz,Mx,My,Mz)."""
        print("  GetForce (force sensor):")
        try:
            resp = self._safe_resp(self.dashboard.GetForce())
            print(f"    Force: {self.parse_response(resp)}")
            return resp
        except Exception as e:
            print(f"    Force read error: {e}")
            return None

    def get_force_sensor_status(self):
        """Force sensor status (from the feedback stream)."""
        print("  Force Sensor Status:")
        try:
            self.feed.socket_dobot.setblocking(True)
            self.feed.socket_dobot.settimeout(5)
            data = self.feed.socket_dobot.recv(144000)
            if len(data) >= 1440:
                data = data[:1440]
                a = np.frombuffer(data, dtype=MyType)
                if hex(a['TestValue'][0]) == '0x123456789abcdef':
                    result = {
                        "SixForceOnline": int(a['SixForceOnline'][0]),
                        "SixForceValue": np.around(a['SixForceValue'], decimals=4)[0].tolist(),
                        "ActualTCPForce": np.around(a['ActualTCPForce'], decimals=4)[0].tolist(),
                    }
                    online_str = "ONLINE" if result["SixForceOnline"] else "OFFLINE"
                    print(f"    Sensor status: {online_str}")
                    print(f"    SixForce: {result['SixForceValue']}")
                    print(f"    ActualTCPForce: {result['ActualTCPForce']}")
                    return result
            print("    No data received")
            return None
        except Exception as e:
            print(f"    Error: {e}")
            return None

    # =========================================================================
    # 7. INTERNAL SOFTWARE REGISTERS
    # =========================================================================

    def get_input_registers(self, bool_count=16, int_count=8, float_count=8):
        """Read internal input registers."""
        print("  Input Registers:")
        results = {}

        print(f"    Bool (0-{bool_count-1}):")
        for i in range(bool_count):
            try:
                resp = self._safe_resp(self.dashboard.GetInputBool(i))
                nums = re.findall(r'-?\d+', resp)
                if len(nums) >= 2 and int(nums[0]) == 0:
                    val = int(nums[1])
                    results[f"InputBool_{i}"] = val
                    if val != 0:
                        print(f"      [{i}] = {val}")
            except:
                pass

        print(f"    Int (0-{int_count-1}):")
        for i in range(int_count):
            try:
                resp = self._safe_resp(self.dashboard.GetInputInt(i))
                nums = re.findall(r'-?\d+', resp)
                if len(nums) >= 2 and int(nums[0]) == 0:
                    val = int(nums[1])
                    results[f"InputInt_{i}"] = val
                    if val != 0:
                        print(f"      [{i}] = {val}")
            except:
                pass

        print(f"    Float (0-{float_count-1}):")
        for i in range(float_count):
            try:
                resp = self._safe_resp(self.dashboard.GetInputFloat(i))
                nums = re.findall(r'-?\d+\.?\d*', resp)
                if len(nums) >= 2 and int(float(nums[0])) == 0:
                    val = float(nums[1])
                    results[f"InputFloat_{i}"] = val
                    if val != 0.0:
                        print(f"      [{i}] = {val}")
            except:
                pass

        if not any(v != 0 for v in results.values()):
            print("    (all values are 0)")
        return results

    def get_output_registers(self, bool_count=16, int_count=8, float_count=8):
        """Read internal output registers."""
        print("  Output Registers:")
        results = {}

        print(f"    Bool (0-{bool_count-1}):")
        for i in range(bool_count):
            try:
                resp = self._safe_resp(self.dashboard.GetOutputBool(i))
                nums = re.findall(r'-?\d+', resp)
                if len(nums) >= 2 and int(nums[0]) == 0:
                    val = int(nums[1])
                    results[f"OutputBool_{i}"] = val
                    if val != 0:
                        print(f"      [{i}] = {val}")
            except:
                pass

        print(f"    Int (0-{int_count-1}):")
        for i in range(int_count):
            try:
                resp = self._safe_resp(self.dashboard.GetOutputInt(i))
                nums = re.findall(r'-?\d+', resp)
                if len(nums) >= 2 and int(nums[0]) == 0:
                    val = int(nums[1])
                    results[f"OutputInt_{i}"] = val
                    if val != 0:
                        print(f"      [{i}] = {val}")
            except:
                pass

        print(f"    Float (0-{float_count-1}):")
        for i in range(float_count):
            try:
                resp = self._safe_resp(self.dashboard.GetOutputFloat(i))
                nums = re.findall(r'-?\d+\.?\d*', resp)
                if len(nums) >= 2 and int(float(nums[0])) == 0:
                    val = float(nums[1])
                    results[f"OutputFloat_{i}"] = val
                    if val != 0.0:
                        print(f"      [{i}] = {val}")
            except:
                pass

        if not any(v != 0 for v in results.values()):
            print("    (all values are 0)")
        return results

    # =========================================================================
    # 8. PATH RECOVERY & LOG
    # =========================================================================

    def get_path_recovery_status(self):
        """Path recovery status."""
        print("  PathRecoveryStatus:")
        try:
            resp = self._safe_resp(self.dashboard.PathRecoveryStatus())
            print(f"    Status: {self.parse_response(resp)}")
            return resp
        except Exception as e:
            print(f"    Error: {e}")
            return None

    def get_export_status(self):
        """Log export status."""
        print("  GetExportStatus:")
        resp = self._safe_resp(self.dashboard.GetExportStatus())
        statuses = {
            0: "Not started", 1: "In progress", 2: "Completed",
            3: "Failed (USB not found)", 4: "Failed (USB full)",
            5: "Failed (USB removed)"
        }
        nums = re.findall(r'-?\d+', resp)
        if len(nums) >= 2:
            s = int(nums[1])
            print(f"    Status: {statuses.get(s, f'Unknown ({s})')}")
        else:
            print(f"    Response: {self.parse_response(resp)}")
        return resp

    # =========================================================================
    # 9. REALTIME FEEDBACK (port 30004) - FULL
    # =========================================================================

    def get_realtime_feedback(self):
        """Read a 1440-byte realtime packet from port 30004 (all fields)."""
        print("  Realtime Feedback (port 30004):")
        try:
            self.feed.socket_dobot.setblocking(True)
            self.feed.socket_dobot.settimeout(5)
            data = self.feed.socket_dobot.recv(144000)
            if len(data) > 1440:
                data = data[-1440:]
            elif len(data) < 1440:
                print(f"    Insufficient data: {len(data)} bytes (1440 expected)")
                return None

            a = np.frombuffer(data[:1440], dtype=MyType)

            if hex(a['TestValue'][0]) != '0x123456789abcdef':
                print("    TestValue check failed, retrying...")
                data = self.feed.socket_dobot.recv(144000)
                data = data[:1440]
                a = np.frombuffer(data, dtype=MyType)
                if hex(a['TestValue'][0]) != '0x123456789abcdef':
                    print("    TestValue still invalid!")
                    return None

            feedback = {
                # --- Basic state ---
                "RobotMode": int(a['RobotMode'][0]),
                "SpeedScaling": float(a['SpeedScaling'][0]),
                "CurrentCommandId": int(a['CurrentCommandId'][0]),
                "TimeStamp": int(a['TimeStamp'][0]),
                "RunTime": int(a['RunTime'][0]),

                # --- DI/DO (bit mask) ---
                "DigitalInputs": hex(int(a['DigitalInputs'][0])),
                "DigitalOutputs": hex(int(a['DigitalOutputs'][0])),

                # --- Position ---
                "JointAngles_J1_J6": np.around(a['QActual'], decimals=4)[0].tolist(),
                "CartesianPose_XYZRxRyRz": np.around(a['ToolVectorActual'], decimals=4)[0].tolist(),
                "JointTargets": np.around(a['QTarget'], decimals=4)[0].tolist(),
                "CartesianTarget": np.around(a['ToolVectorTarget'], decimals=4)[0].tolist(),

                # --- Speed ---
                "JointSpeeds": np.around(a['QDActual'], decimals=4)[0].tolist(),
                "JointSpeedTargets": np.around(a['QDTarget'], decimals=4)[0].tolist(),
                "TCPSpeed": np.around(a['TCPSpeedActual'], decimals=4)[0].tolist(),
                "TCPSpeedTarget": np.around(a['TCPSpeedTarget'], decimals=4)[0].tolist(),

                # --- Current / Torque ---
                "JointCurrents": np.around(a['IActual'], decimals=4)[0].tolist(),
                "JointCurrentTargets": np.around(a['ITarget'], decimals=4)[0].tolist(),
                "JointTorques": np.around(a['MActual'], decimals=4)[0].tolist(),
                "JointTorqueTargets": np.around(a['MTarget'], decimals=4)[0].tolist(),
                "JointAccelTargets": np.around(a['QDDTarget'], decimals=4)[0].tolist(),

                # --- Force ---
                "TCPForce": np.around(a['TCPForce'], decimals=4)[0].tolist(),
                "ActualTCPForce": np.around(a['ActualTCPForce'], decimals=4)[0].tolist(),

                # --- Temperature ---
                "MotorTemperatures": np.around(a['MotorTemperatures'], decimals=2)[0].tolist(),

                # --- Power ---
                "VRobot": float(a['VRobot'][0]),
                "IRobot": float(a['IRobot'][0]),

                # --- Load ---
                "Load_kg": float(a['Load'][0]),
                "CenterX_mm": float(a['CenterX'][0]),
                "CenterY_mm": float(a['CenterY'][0]),
                "CenterZ_mm": float(a['CenterZ'][0]),

                # --- Status flags ---
                "CollisionState": int(a['CollisionState'][0]),
                "BrakeStatus": int(a['BrakeStatus'][0]),
                "EnableStatus": int(a['EnableStatus'][0]),
                "DragStatus": int(a['DragStatus'][0]),
                "ErrorStatus": int(a['ErrorStatus'][0]),
                "RunningStatus": int(a['RunningStatus'][0]),
                "JogStatusCR": int(a['JogStatusCR'][0]),
                "SafetyState": int(a['SafetyState'][0]),
                "SafetyOIn": int(a['SafetyOIn'][0]),
                "SafetyOOut": int(a['SafetyOOut'][0]),
                "ProgramState": float(a['ProgramState'][0]),
                "AutoManualMode": int(a['AutoManualMode'][0]),
                "ExportStatus": int(a['ExportStatus'][0]),

                # --- Robot type & buttons ---
                "CRRobotType": int(a['CRRobotType'][0]),
                "HandType": a['HandType'][0].tolist(),
                "DragButtonSignal": int(a['DragButtonSignal'][0]),
                "EnableButtonSignal": int(a['EnableButtonSignal'][0]),
                "RecordButtonSignal": int(a['RecordButtonSignal'][0]),
                "ReappearButtonSignal": int(a['ReappearButtonSignal'][0]),
                "JawButtonSignal": int(a['JawButtonSignal'][0]),

                # --- Coordinate systems ---
                "User": int(a['User'][0]),
                "Tool": int(a['Tool'][0]),
                "UserValue": np.around(a['UserValue[6]'], decimals=4)[0].tolist(),
                "ToolValue": np.around(a['ToolValue[6]'], decimals=4)[0].tolist(),

                # --- Velocity/Acceleration ratios ---
                "VelocityRatio": int(a['VelocityRatio'][0]),
                "AccelerationRatio": int(a['AccelerationRatio'][0]),
                "XYZVelocityRatio": int(a['XYZVelocityRatio'][0]),
                "RVelocityRatio": int(a['RVelocityRatio'][0]),
                "XYZAccelerationRatio": int(a['XYZAccelerationRatio'][0]),
                "RAccelerationRatio": int(a['RAccelerationRatio'][0]),
                "RunQueuedCmd": int(a['RunQueuedCmd'][0]),
                "PauseCmdFlag": int(a['PauseCmdFlag'][0]),

                # --- Vibration ---
                "VibrationDisZ": float(a['VibrationDisZ'][0]),

                # --- Joint modes ---
                "JointModes": np.around(a['JointModes'], decimals=0)[0].tolist(),
                "VActual": np.around(a['VActual'], decimals=4)[0].tolist(),

                # --- Approach states ---
                "ArmApproachState": int(a['ArmApproachState'][0]),
                "J4ApproachState": int(a['J4ApproachState'][0]),
                "J5ApproachState": int(a['J5ApproachState'][0]),
                "J6ApproachState": int(a['J6ApproachState'][0]),

                # --- Quaternion ---
                "ActualQuaternion": np.around(a['ActualQuaternion'], decimals=6)[0].tolist(),
                "TargetQuaternion": np.around(a['TargetQuaternion'], decimals=6)[0].tolist(),

                # --- Force sensor ---
                "SixForceOnline": int(a['SixForceOnline'][0]),
                "SixForceValue": np.around(a['SixForceValue'], decimals=4)[0].tolist(),
            }

            for key, val in feedback.items():
                print(f"    {key}: {val}")

            return feedback

        except Exception as e:
            print(f"    Feedback read error: {e}")
            return None

    # =========================================================================
    # 10. HTTP API (port 22000)
    # =========================================================================

    def get_alarm_info(self, language="en"):
        """Fetch alarm info via the HTTP API."""
        print("  Alarm Info (HTTP API):")
        try:
            resp = self.dashboard.GetError(language)
            if resp and "errMsg" in resp:
                if not resp["errMsg"]:
                    print("    No active alarms")
                else:
                    for err in resp["errMsg"]:
                        print(f"    [{err.get('level','')}] ID:{err.get('id','')} - {err.get('description','')}")
                        print(f"      Solution: {err.get('solution','')}")
            return resp
        except Exception as e:
            print(f"    Alarm read error: {e}")
            return None

    # =========================================================================
    # 11. FULL REPORT
    # =========================================================================

    def read_all_config(self, include_io=True, include_feedback=True,
                        include_kinematic=True, include_force=True,
                        include_registers=True, include_extra=True,
                        di_count=16, do_count=16):
        """Read every section of the robot configuration and report it."""
        print("=" * 60)
        print(f"  CR20A ROBOT CONFIGURATION REPORT (FULL)")
        print(f"  IP: {self.ip}")
        print("=" * 60)

        config = {}
        section = 1

        # 1. Robot Mode
        print(f"\n[{section}] ROBOT STATE")
        config["robot_mode"] = self.get_robot_mode()
        section += 1

        # 2. Position
        print(f"\n[{section}] CURRENT POSITION")
        config["pose"] = self.get_pose()
        config["angles"] = self.get_angle()
        section += 1

        # 3. Errors
        print(f"\n[{section}] ERROR STATE")
        config["errors"] = self.get_error_id()
        config["alarm_info"] = self.get_alarm_info()
        section += 1

        # 4. Command ID
        print(f"\n[{section}] COMMAND STATE")
        config["command_id"] = self.get_current_command_id()
        section += 1

        # 5. I/O
        if include_io:
            print(f"\n[{section}] DIGITAL I/O")
            config["digital_outputs"] = self.get_digital_outputs(do_count)
            config["digital_inputs"] = self.get_digital_inputs(di_count)
            config["do_group_dec"] = self.get_do_group_dec()
            section += 1

            print(f"\n[{section}] ANALOG I/O")
            config["analog_inputs"] = self.get_analog_inputs()
            config["analog_outputs"] = self.get_analog_outputs()
            section += 1

            print(f"\n[{section}] TOOL I/O")
            config["tool_io"] = self.get_tool_io()
            section += 1

        # 6. Kinematics
        if include_kinematic:
            print(f"\n[{section}] KINEMATICS (from current pose)")
            config["positive_kin"] = self.get_positive_kin_current()
            section += 1

        # 7. Force sensor
        if include_force:
            print(f"\n[{section}] FORCE SENSOR")
            config["force"] = self.get_force()
            config["force_sensor_status"] = self.get_force_sensor_status()
            section += 1

        # 8. Internal registers
        if include_registers:
            print(f"\n[{section}] INTERNAL REGISTERS")
            config["input_registers"] = self.get_input_registers()
            config["output_registers"] = self.get_output_registers()
            section += 1

        # 9. Extra
        if include_extra:
            print(f"\n[{section}] PATH & LOG STATE")
            config["path_recovery"] = self.get_path_recovery_status()
            config["export_status"] = self.get_export_status()
            section += 1

        # 10. Realtime feedback
        if include_feedback:
            print(f"\n[{section}] REALTIME FEEDBACK (30004) - FULL")
            config["feedback"] = self.get_realtime_feedback()
            section += 1

        print("\n" + "=" * 60)
        print(f"  REPORT COMPLETE ({section-1} sections)")
        print("=" * 60)

        return config

    def save_config(self, filename="cr20a_config.json"):
        """Save the config to a JSON file."""
        config = self.read_all_config()
        serializable = {}
        for k, v in config.items():
            try:
                json.dumps(v)
                serializable[k] = v
            except (TypeError, ValueError):
                serializable[k] = str(v)

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(serializable, f, indent=2, ensure_ascii=False)
        print(f"\nConfig saved: {filename}")


# =========================================================================
# USAGE
# =========================================================================

if __name__ == "__main__":
    ROBOT_IP = "192.168.5.3"

    reader = RobotConfigReader(ROBOT_IP)

    if not reader.connect():
        exit(1)

    try:
        # --- FULL REPORT ---
        reader.read_all_config(
            include_io=True,
            include_feedback=True,
            include_kinematic=True,
            include_force=True,
            include_registers=True,
            include_extra=True,
            di_count=16,
            do_count=16,
        )

        # --- QUICK REPORT (basic info only) ---
        # reader.read_all_config(
        #     include_io=False, include_feedback=False,
        #     include_kinematic=False, include_force=False,
        #     include_registers=False, include_extra=False,
        # )

        # --- SAVE TO JSON ---
        # reader.save_config("cr20a_config.json")

        # --- SINGLE READS ---
        # reader.get_robot_mode()
        # reader.get_pose()
        # reader.get_angle()
        # reader.get_force()
        # reader.get_inverse_kin(-523.65, 236.58, 430.74, 164.50, 42.37, 60.39)
        # reader.check_movj_reachable(0,0,0,0,0,0, 10,20,30,0,90,0)

    finally:
        reader.disconnect()
