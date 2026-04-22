# Dental Robot Controller

Python-based interface for controlling a Dobot Nova 5 robot with a PS5 DualSense joystick. Targets dental surgery workflows with a tool-coordinate system, drag-teach mode, and a PyQt5 GUI.

## Features

- **Dual Control Modes**
  - **Joint Mode** (J1-J6): Coarse positioning, free of singularity issues
  - **Tool Mode**: Precise rotation around the tool center point (TCP), simulating a flange locked to the patient's face
- **Drag Teach**: Manually drag the robot and capture the pose
- **Saved Positions**: Store Home and Surgery poses, recall with a single button
- **Tool Distance Slider**: 1 cm - 50 cm runtime adjustment
- **PyQt5 GUI**: Status indicators, speed control, live log
- **Automatic Error Recovery**: Auto-recovery from singularity, collision, and Mode 7 issues
- **JSON Configuration**: Every parameter lives in `settings.json`

## Requirements

- Python 3.10+
- Dobot Nova 5 robot (TCP/IP V4 firmware)
- PS5 DualSense joystick
- Network connection: robot default IP `192.168.5.1`

## Installation

```bash
git clone https://github.com/ahmet-f-gumustas/dental-robot-controller.git
cd dental-robot-controller
pip install -r requirements.txt
```

## Usage

### GUI (recommended)

```bash
python3 gui_control.py
```

### Joystick only

```bash
python3 joystick_control.py
```

### Position Setup Workflow

1. Click **Start Joystick**
2. Drive the robot to the home pose with the joystick
3. Click **[SAVE HOME]**
4. Drive the robot to the surgery pose
5. Click **[SAVE SURGERY]**
6. From now on, **D-Pad Left** jumps to home and **D-Pad Right** jumps to the surgery pose
7. Adjust the TCP offset with the tool distance slider (default 35 cm)

## Control Scheme

### Joint Mode
| Control | Function |
|---------|----------|
| Left Stick Y | J1 (base) |
| Left Stick X | J2 (shoulder) |
| Right Stick Y | J3 (elbow) |
| Right Stick X | J4 (wrist 1) |
| L2 / R2 | J5 (wrist 2) |
| D-Pad Y | J6 (tip) |

### Tool Mode (patient face fixed, rotate around the flange)
| Control | Function |
|---------|----------|
| Left Stick | X/Y translation (in tool axes) |
| Right Stick Y | Z translation |
| **Right Stick X** | **Ry rotation** (head left/right) |
| **L2 / R2** | **Rx rotation** (head up/down) |
| **D-Pad Y** | **Rz rotation** (head tilt) |

### Buttons
| Button | Function |
|--------|----------|
| SHARE | Switch mode (Joint <-> Tool) |
| Triangle / X | Speed +/- |
| Square | Stop |
| Circle | Toggle drag mode |
| R1 | Enable |
| L1 | Disable |
| D-Pad Left/Right | Go to Home / Surgery pose |
| L3 / R3 | Save Home / Surgery pose |
| Options | Quit |
| PS | Emergency stop |

## Configuration

`settings.json` is created automatically on first launch:

```json
{
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
```

Saved poses live in `positions.json`:

```json
{
  "home": [264.97, -6.84, -148.73, 89.19, 89.03, -4.99],
  "surgery": [275.02, -48.85, -66.75, 60.7, 83.34, 5.39],
  "tool_distance": 350
}
```

## Project Layout

```
.
├── gui_control.py          # PyQt5 GUI (main application)
├── joystick_control.py     # Core controller class + joystick loop
├── robot_diagnose.py       # Robot diagnostics script
├── tool_test.py            # Tool coordinate system test
├── joystick_test.py        # PS5 button/axis mapping test
├── robot_config_reader.py  # Full robot configuration reader
├── robot_connection_test.py# Simple TCP connection test
├── collision_close.py      # Collision/SafeSkin disabler
├── TCP-IP-Python-V4/       # Official Dobot Python SDK
├── settings.json           # User settings (auto-generated)
└── positions.json          # Saved poses (auto-generated)
```

## Known Limitations

1. **Wrist Singularity**: Cartesian/tool jog throws Error 30 when J5 is near 0 deg / 360 deg. Switch to Joint Mode, bring J5 to ~+/-45 deg, then re-enter Tool Mode.
2. **Single-axis Jog**: Only one axis moves at a time (MoveJog limitation). The most dominant axis is selected.
3. **DualSense Axis Mapping**: Linux SDL2 mapping is non-standard. The correct mapping is hardcoded (Axis 2 = L2, Axis 3 = Right X).

## Common Errors

| Error Code | Reason | Fix |
|------------|--------|-----|
| `-1` | Command rejected (busy) | Retried automatically |
| `-2` | Nothing to stop | Normal, safe to ignore |
| `-6` | Axis/motion type mismatch | Check the `coordtype` parameter |
| `Error 17` | Collision detected | Disabled via `SetCollisionLevel(0)` |
| `Error 30` | Inverse kinematics failed | Singularity - escape via joint jog |
| `Mode 7` | A program is running on the controller | Stopped via `Stop()` |

## Safety Notice

> **Medical-use warning**
>
> This software is intended for research and development. Medical-device certification (CE/FDA, etc.) is required before any use on actual patients. The author assumes no liability for damages arising from the use of this software.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Hardware

- **Robot**: Dobot Nova 5 (ceiling mounted - 180 deg install angle)
- **Joystick**: Sony PS5 DualSense Wireless Controller
- **Link**: Ethernet, TCP/IP V4 protocol (port 29999)
