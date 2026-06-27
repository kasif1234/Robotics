# Master Pi Remote-Controlled Embedded Robot - Robotics

A Raspberry Pi 5 based embedded control system for remote navigation, live camera streaming, and servo-based object manipulation using a PS5 DualSense controller.

<img width="1263" height="608" alt="Image" src="https://github.com/user-attachments/assets/aa273e03-87c7-44b1-903b-f616ac41f3c8" />

The system uses two Raspberry Pi 5 units:

- One Raspberry Pi 5 acts as the controller-side unit.
- One Raspberry Pi 5 acts as the robot-side unit.

The controller Raspberry Pi reads PS5 controller inputs and sends real-time control data through WebSockets. The robot Raspberry Pi receives these commands, controls the DC motors and servo motors, and streams live camera frames back to the controller.

---
[Final_Robotics_Report.pdf](https://github.com/user-attachments/files/27852693/Final_Robotics_Report.pdf)
---
[![Watch the video](https://img.youtube.com/vi/2dfTFchEuLg/hqdefault.jpg)](https://www.youtube.com/watch?v=2dfTFchEuLg)
---

## Project Overview

This project demonstrates the integration of real-time control, wireless communication, motor actuation, servo control, computer vision, and embedded power management into one complete system.

The robot can:

- Move forward and backward
- Move left and right
- Rotate clockwise and counterclockwise
- Control a robotic arm using servo motors
- Open and close a gripper
- Stream live camera footage
- Receive real-time PS5 controller commands
- Stop safely when communication is lost

---

## System Architecture

```text
PS5 DualSense Controller
        |
        v
Controller Raspberry Pi 5
        |
        | WebSocket Communication
        v
Robot Raspberry Pi 5
        |
        |-----------------------------|
        |                             |
        v                             v
L298N Motor Drivers             PCA9685 Servo Driver
        |                             |
        v                             v
DC Motors                       Servo Motors
        |                             |
        v                             v
Robot Movement                  Robotic Arm Control

USB Camera
        |
        v
Live Video Stream to Controller Raspberry Pi
```

---

## Main Technologies

| Technology | Purpose |
|---|---|
| Python | Main programming language |
| Raspberry Pi 5 | Embedded processing platform |
| PS5 DualSense Controller | Human-machine control interface |
| Pygame | Reads controller joystick and button inputs |
| WebSockets | Sends real-time control commands and camera frames |
| OpenCV | Captures, encodes, decodes, and displays camera frames |
| NumPy | Converts image bytes into arrays for OpenCV |
| GPIO Zero | Controls GPIO pins and PWM signals for motor drivers |
| PCA9685 | Generates PWM signals for servo control |
| L298N Motor Driver | Controls DC motor speed and direction |
| Asyncio | Handles concurrent network communication |
| Threading | Separates camera display from async communication |

<img width="551" height="735" alt="Image" src="https://github.com/user-attachments/assets/c42c2164-146d-4f6c-b1fe-08171d733057" />



---
## Hardware Requirements

- Raspberry Pi 5 x2
- PS5 DualSense controller
- USB camera
- DC motors x4
- Servo motors
- L298N motor drivers
- PCA9685 servo controller
- Li-ion batteries for motors and servos
- Power bank or suitable power source for Raspberry Pi units
- Buck converter for voltage regulation
- Jumper wires
- Robot chassis
- Common ground connection between control and power circuits

---
<img width="486" height="275" alt="Image" src="https://github.com/user-attachments/assets/68728d11-0163-4231-a799-23796238bc8c" />

---
## Software Requirements

Create a `requirements.txt` file with the following contents:

```txt
websockets
pygame
opencv-python
numpy
gpiozero
adafruit-blinka
adafruit-circuitpython-pca9685
lgpio
```

Install the dependencies using:

```bash
pip install -r requirements.txt
```

On Raspberry Pi OS, you may also need:

```bash
sudo apt update
sudo apt install python3-pip python3-opencv
```

---

## Project Structure

```text
master-pi-robot/
│
├── robot.py
│   └── Runs on the robot Raspberry Pi.
│       Receives controller commands, controls movement,
│       controls servos, streams camera frames, and handles fail-safe logic.
│
├── controller.py
│   └── Runs on the controller Raspberry Pi.
│       Reads PS5 controller inputs, sends control packets,
│       receives camera frames, and displays the video feed.
│
├── wheelsmovement_robotics.py
│   └── Controls the DC motors using GPIO direction pins and PWM speed control.
│
├── Activity2.py
│   └── Controls servo motors using the PCA9685 PWM servo controller.
│
├── servo5_state.txt
│   └── Stores the last servo angle to allow smoother servo transitions.
│
├── requirements.txt
│   └── Contains the required Python dependencies.
│
└── README.md
```

---

## Communication Design

The system uses two WebSocket connections.

| Port | Function |
|---|---|
| 8765 | Camera streaming |
| 5001 | Controller input transmission |

The robot Raspberry Pi listens on:

```python
LISTEN_IP = "10.42.0.1"
CAMERA_PORT = 8765
STICK_PORT = 5001
```

The controller Raspberry Pi connects to:

```python
CAMERA_URI = "ws://10.42.0.1:8765"
STICK_URI = "ws://10.42.0.1:5001"
```

Both Raspberry Pi units must be connected to the same network, and the IP address must match the robot Raspberry Pi address.

---

## Control Packet Format

The controller sends joystick and button data as JSON packets.

Example:

```json
{
  "lx": 0.0,
  "ly": -1.0,
  "rx": 0.0,
  "ry": 0.0,
  "x_state": 150,
  "dpad_angle": 90,
  "triangle_mode": false,
  "ts": 1710000000.0
}
```

| Field | Meaning |
|---|---|
| `lx` | Left joystick horizontal axis |
| `ly` | Left joystick vertical axis |
| `rx` | Right joystick horizontal axis |
| `ry` | Right joystick vertical axis |
| `x_state` | Gripper servo target state |
| `dpad_angle` | Servo angle controlled by D-pad |
| `triangle_mode` | Toggles between lateral movement and rotation |
| `ts` | Timestamp of packet transmission |

---

## PS5 Controller Mapping

| Controller Input | Function |
|---|---|
| Left joystick vertical | Move forward or backward |
| Left joystick horizontal | Move left or right |
| Triangle button | Toggle rotation mode |
| Left joystick horizontal in rotation mode | Rotate clockwise or counterclockwise |
| Right joystick | Control robotic arm servos |
| D-pad up/down | Adjust arm angle |
| Cross button | Toggle gripper position |
| Circle button | Toggle camera display |

---

## Motor Control Logic

The robot uses four DC motors controlled through L298N motor drivers.

Each motor receives direction commands through GPIO pins.

| Value | Motor State |
|---|---|
| `1` | Forward |
| `-1` | Reverse |
| `0` | Stop |

The available movement functions are:

```python
movFwdDC()
movRevDC()
movLeftDC()
movRightDC()
rotateCW()
rotateCCW()
stop()
```

PWM is used to control motor speed:

```python
pwm_left.value = speed_left
pwm_right.value = speed_right
```

---

## Servo Control Logic

Servo motors are controlled using the PCA9685 PWM servo driver at 50 Hz.

The servo angle is mapped to duty cycle using:

```python
duty = int(min_duty + (angle / 180.0) * (max_duty - min_duty))
```

This converts an angle between 0 and 180 degrees into a PWM duty cycle suitable for servo positioning.

The servo control module includes:

```python
set_angle()
set_angle_load()
pickUp()
reset()
load_value()
save_value()
```

The `set_angle_load()` function moves the servo gradually in steps to reduce sudden motion and improve stability.

---

## Important Control Features

### Deadzone Filtering

Small joystick noise is removed using a deadzone.

```python
DEADZONE = 0.2
```

This prevents the robot from moving when the joystick is near the center position.

---

### Speed Tiering

The robot uses two speed levels depending on joystick magnitude.

```text
0.5 speed for smaller joystick input
1.0 speed for larger joystick input
```

This improves control during both slow and fast movement.

---

### Axis Dominance Filtering

The controller checks whether joystick movement is mainly horizontal or vertical.

This helps prevent diagonal joystick noise from triggering unwanted movement commands.

---

### Rotation Mode

The triangle button toggles the left joystick between two modes:

```text
Normal Mode:
Left joystick horizontal = move left or right

Rotation Mode:
Left joystick horizontal = rotate clockwise or counterclockwise
```

---

### Camera Toggle

The circle button toggles the camera display on the controller Raspberry Pi.

Camera frames are captured on the robot Raspberry Pi, encoded using OpenCV, sent through WebSockets, decoded on the controller side, and displayed in a separate window.

---

### Fail-Safe Stop

If the controller connection is lost, the robot automatically stops.

```python
def fail_safe():
    if not left_centered:
        stop()
```

This is important because embedded systems should fail safely instead of continuing uncontrolled motion.

---

## How to Run

### 1. Start the robot-side program

Run this on the robot Raspberry Pi:

```bash
python3 robot.py
```

This starts:

- Camera WebSocket server on port 8765
- Controller input WebSocket server on port 5001
- Motor and servo control logic

---

### 2. Start the controller-side program

Run this on the controller Raspberry Pi:

```bash
python3 controller.py
```

This starts:

- PS5 controller input reading
- WebSocket command transmission
- Camera frame receiving
- Camera display window

---

## Debugging Checklist

When the robot does not behave correctly, debug layer by layer.

```text
Signal → Power → Communication → Actuation → Control Logic → Mechanical Output
```

Common issues include:

| Symptom | Possible Cause |
|---|---|
| Servo jitter | Weak power, unstable ground, PWM noise, high mechanical load |
| Motors not moving | Incorrect GPIO wiring, weak battery, driver issue, wrong PWM pin |
| Robot moves incorrectly | Motor polarity mismatch, incorrect motor direction mapping |
| Camera not displaying | Wrong IP address, WebSocket connection issue, camera not detected |
| Delayed response | Network latency, overloaded Raspberry Pi, slow frame processing |
| Controller not detected | PS5 controller not paired, wrong joystick index, Pygame issue |
| Sudden uncontrolled motion | Missing deadzone, joystick drift, communication packet error |

---

## Engineering Lessons

This project showed that a visible failure is rarely caused by one isolated issue.

Unstable output may come from:

- Voltage drop
- Weak grounding
- PWM instability
- Motor noise
- Communication latency
- Actuator load
- Mechanical resistance
- Incorrect control logic
- Poor wiring
- Power supply limitations

A reliable system requires systematic debugging, not random trial and error.

The best approach is to define the symptom, isolate variables, test one subsystem at a time, measure the output, verify the assumption, and then move to the next layer.

---
<img width="950" height="305" alt="Image" src="https://github.com/user-attachments/assets/a09924b1-89e5-46d9-a8ef-be0d68858e25" />
---


## Future Improvements

- Add wheel encoders for closed-loop speed feedback
- Implement PID control for motor speed regulation
- Add battery voltage monitoring
- Add emergency stop functionality
- Add object detection using computer vision
- Improve servo trajectory planning
- Add logging for control packets and response delay
- Improve modular code organization
- Add unit tests for control logic
- Add a configuration file for IP addresses and ports
- PID Algorithmic Approach

---

## Key Takeaway

A working prototype shows implementation.

A reliable prototype shows engineering discipline.

# Access Master Pi Manual: 
https://docs.hiwonder.com/projects/MasterPi/en/latest/docs/1.getting_ready.html#
