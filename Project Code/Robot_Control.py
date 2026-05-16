import asyncio
import json
import cv2
import websockets
from Activity2 import *
from wheelsmovement_robotics import *


# Network config
LISTEN_IP   = "10.42.0.1"
CAMERA_PORT = 8765
STICK_PORT  = 5001

# Camera setup
camera = cv2.VideoCapture(0)

# Tunable constants
DEADZONE         = 0.2
MIDWAY_THRESHOLD = 0.5
SERVO_STEP       = 2

# Servo state
servo_h_angle   = 90
servo_v_angle   = 90
last_dpad_angle = 90
last_x_state    = 0

set_angle_load(7, servo_h_angle)
set_angle(6, servo_v_angle)
set_angle(4, last_dpad_angle)
set_angle(0, 0)

# Latch flags
left_centered  = True
right_centered = True


def apply_deadzone(value):
    return 0.0 if abs(value) < DEADZONE else value


def speed_tier(magnitude):
    return 0.5 if magnitude <= MIDWAY_THRESHOLD else 1.0


def handle_left_stick(lx, ly, rotate_mode):
    global left_centered

    lx = apply_deadzone(lx)
    ly = apply_deadzone(ly)

    if lx == 0.0 and ly == 0.0:
        if not left_centered:
            stop()
            left_centered = True
        return

    left_centered = False

    if ly != 0.0:
        # Vertical axis: always forward/back regardless of mode
        pwm = speed_tier(abs(ly))
        if ly < 0:
            movFwdDC(pwm, pwm)
        else:
            movRevDC(pwm, pwm)
    else:
        # Horizontal axis: normal or rotation mode
        pwm = speed_tier(abs(lx))
        if rotate_mode:
            if lx < 0:
                rotateCCW(pwm, pwm)
            else:
                rotateCW(pwm, pwm)
        else:
            if lx < 0:
                movLeftDC(pwm, pwm)
            else:
                movRightDC(pwm, pwm)
def handle_right_stick(rx, ry):
    global servo_h_angle, servo_v_angle, right_centered

    rx = apply_deadzone(rx)
    ry = apply_deadzone(ry)

    if rx == 0.0 and ry == 0.0:
        right_centered = True
        return

    if not right_centered:
        return

    if rx != 0.0:
        delta = -rx * SERVO_STEP
        new_h = max(0, min(180, servo_h_angle + delta))
        if int(new_h) != int(servo_h_angle):
            servo_h_angle = new_h
            set_angle_load(7, int(servo_h_angle))

    if ry != 0.0:
        delta = -ry * SERVO_STEP
        new_v = max(0, min(180, servo_v_angle + delta))
        if int(new_v) != int(servo_v_angle):
            servo_v_angle = new_v
            set_angle(6, int(servo_v_angle))


def handle_x_state(x_state):
    global last_x_state
    if x_state != last_x_state:
        set_angle(0, x_state)
        last_x_state = x_state
        print("set_load(0, " + str(x_state) + ")")


def handle_dpad_angle(angle):
    global last_dpad_angle
    if angle != last_dpad_angle:
        set_angle(4, angle)
        last_dpad_angle = angle
        print("set_angle(4, " + str(angle) + ")")


def fail_safe():
    global left_centered, right_centered
    if not left_centered:
        stop()
        left_centered = True
    right_centered = True
async def camera_handler(websocket):
    print("Camera client connected")
    try:
        while True:
            ret, frame = camera.read()
            if not ret:
                await asyncio.sleep(0.01)
                continue
            _, buffer = cv2.imencode(".jpg", frame)
            await websocket.send(buffer.tobytes())
            await asyncio.sleep(0.03)
    except websockets.ConnectionClosed:
        print("Camera client disconnected")


async def stick_handler(websocket):
    print("Stick client connected: " + str(websocket.remote_address))
    try:
        async for message in websocket:
            try:
                payload = json.loads(message)

                rotate_mode = payload.get("triangle_mode", False)

                handle_left_stick(payload["lx"], payload["ly"], rotate_mode)
                handle_right_stick(payload["rx"], payload["ry"])

                if "x_state" in payload:
                    handle_x_state(payload["x_state"])
                if "dpad_angle" in payload:
                    handle_dpad_angle(payload["dpad_angle"])

            except (json.JSONDecodeError, KeyError) as e:
                print("Bad packet: " + str(e))
    except websockets.ConnectionClosed:
        print("Stick client disconnected")
    finally:
        fail_safe()


async def main():
    async with websockets.serve(camera_handler, LISTEN_IP, CAMERA_PORT,
                                max_size=None), \
               websockets.serve(stick_handler, LISTEN_IP, STICK_PORT,
                                ping_interval=1, ping_timeout=2):
        print("Camera on port " + str(CAMERA_PORT) + ", sticks on port " + str(STICK_PORT))
        await asyncio.Future()


try:
    asyncio.run(main())
except KeyboardInterrupt:
    stop()
    camera.release()
