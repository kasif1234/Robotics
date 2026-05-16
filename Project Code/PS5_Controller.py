import asyncio
import json
import time
import threading
import queue
import pygame
import numpy as np
import cv2
import websockets

# Network config
RECEIVER_IP = "10.42.0.1"
CAMERA_URI = "ws://10.42.0.1:8765"
STICK_URI = "ws://10.42.0.1:5001"

LOOP_DELAY = 0.02

# PS5 DualSense axis mapping
AXIS_LX = 0
AXIS_LY = 1
AXIS_RX = 3
AXIS_RY = 4

# PS5 button and hat mapping
BTN_CROSS = 0
BTN_CIRCLE = 1
BTN_TRIANGLE = 2
HAT_INDEX = 0

# Servo steps
SERVO_STEP = 4
DPAD_STEP = 4

# D-pad angle state for channel 4
DPAD_ANGLE_MIN = 0
DPAD_ANGLE_MAX = 180
DPAD_ANGLE_INIT = 90

dpad_angle = DPAD_ANGLE_INIT

# Pygame setup
pygame.init()
pygame.joystick.init()
joystick = pygame.joystick.Joystick(0)
joystick.init()

print("Connected: " + joystick.get_name())
print("Axes: " + str(joystick.get_numaxes()))
print("Buttons: " + str(joystick.get_numbuttons()))
print("Hats: " + str(joystick.get_numhats()))

# Shared state
x_toggle_state = 0
triangle_mode = False
prev_cross = False
prev_circle = False
prev_triangle = False

# Camera enable/disable event
# set means show, cleared means hide
camera_event = threading.Event()

# Frame queue: async receiver to display thread
frame_queue = queue.Queue(maxsize=2)


def axis_is_dominant_horizontal(x, y, ratio=2.5):
    return abs(x) > abs(y) * ratio


def axis_is_dominant_vertical(x, y, ratio=1.2):
    return abs(y) >= abs(x) * ratio


def display_thread():
    window_name = "Robot Camera"
    window_open = False

    while True:
        if camera_event.is_set():
            try:
                frame_bytes = frame_queue.get_nowait()
                np_arr = np.frombuffer(frame_bytes, np.uint8)
                frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            except queue.Empty:
                frame = None

            if not window_open:
                cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
                cv2.setWindowProperty(window_name,
                                      cv2.WND_PROP_FULLSCREEN,
                                      cv2.WINDOW_FULLSCREEN)
                window_open = True

            if frame is not None:
                cv2.imshow(window_name, frame)

            key = cv2.waitKey(1)
            if key == 27:
                camera_event.clear()
                cv2.destroyWindow(window_name)
                window_open = False

        else:
            if window_open:
                cv2.destroyWindow(window_name)
                cv2.waitKey(1)
                window_open = False

            time.sleep(0.02)
async def stick_sender():
    global prev_cross, prev_circle, prev_triangle
    global x_toggle_state, triangle_mode, dpad_angle

    while True:
        try:
            print("Connecting stick sender to " + STICK_URI)
            async with websockets.connect(STICK_URI, ping_interval=1, ping_timeout=2) as ws:
                print("Stick sender connected.")
                while True:
                    pygame.event.pump()

                    lx = joystick.get_axis(AXIS_LX)
                    ly = joystick.get_axis(AXIS_LY)
                    rx = joystick.get_axis(AXIS_RX)
                    ry = joystick.get_axis(AXIS_RY)

                    if axis_is_dominant_horizontal(lx, ly, ratio=2.5):
                        ly = 0.0
                    elif axis_is_dominant_vertical(lx, ly, ratio=1.2):
                        lx = 0.0
                    else:
                        lx = ly = 0.0

                    if axis_is_dominant_horizontal(rx, ry, ratio=2.5):
                        ry = 0.0
                    elif axis_is_dominant_vertical(rx, ry, ratio=1.2):
                        rx = 0.0
                    else:
                        rx = ry = 0.0

                    hat_x, hat_y = joystick.get_hat(HAT_INDEX)
                    if hat_y == 1:
                        dpad_angle = max(DPAD_ANGLE_MIN, dpad_angle - DPAD_STEP)
                    elif hat_y == -1:
                        dpad_angle = min(DPAD_ANGLE_MAX, dpad_angle + DPAD_STEP)

                    cross_now = joystick.get_button(BTN_CROSS) == 1
                    circle_now = joystick.get_button(BTN_CIRCLE) == 1
                    triangle_now = joystick.get_button(BTN_TRIANGLE) == 1

                    cross_pressed = cross_now and not prev_cross
                    circle_pressed = circle_now and not prev_circle
                    triangle_pressed = triangle_now and not prev_triangle

                    prev_cross = cross_now
                    prev_circle = circle_now
                    prev_triangle = triangle_now

                    if cross_pressed:
                        x_toggle_state = 150 if x_toggle_state == 0 else 0
                        print("X pressed -> set_load target: " + str(x_toggle_state))
                    if circle_pressed:
                        if camera_event.is_set():
                            camera_event.clear()
                            print("O pressed -> camera off")
                        else:
                            camera_event.set()
                            print("O pressed -> camera on")

                    if triangle_pressed:
                        triangle_mode = not triangle_mode
                        print("Triangle pressed -> rotate mode: " + str(triangle_mode))

                    payload = json.dumps({
                        "lx": lx,
                        "ly": ly,
                        "rx": rx,
                        "ry": ry,
                        "x_press": cross_pressed,
                        "x_state": x_toggle_state,
                        "dpad_angle": int(dpad_angle),
                        "triangle_mode": triangle_mode,
                        "ts": time.time(),
                    })

                    await ws.send(payload)
                    await asyncio.sleep(LOOP_DELAY)

        except (websockets.ConnectionClosed, OSError) as e:
            print("Stick sender lost: " + str(e) + ". Retrying in 1s...")
            await asyncio.sleep(1)
async def video_receiver():
    while True:
        try:
            print("Connecting video receiver to " + CAMERA_URI)
            async with websockets.connect(CAMERA_URI, max_size=None) as ws:
                print("Video receiver connected.")
                while True:
                    frame_bytes = await ws.recv()

                    if camera_event.is_set():
                        try:
                            frame_queue.put_nowait(frame_bytes)
                        except queue.Full:
                            try:
                                frame_queue.get_nowait()
                            except queue.Empty:
                                pass
                            frame_queue.put_nowait(frame_bytes)

                    await asyncio.sleep(0)

        except (websockets.ConnectionClosed, OSError) as e:
            print("Video receiver lost: " + str(e) + ". Retrying in 1s...")
            await asyncio.sleep(1)


async def async_main():
    await asyncio.gather(
        stick_sender(),
        video_receiver(),
    )


if __name__ == "__main__":
    t = threading.Thread(target=display_thread, daemon=True)
    t.start()

    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        pass
    finally:
        cv2.destroyAllWindows()
        pygame.quit()
