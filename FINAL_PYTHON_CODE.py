import serial
import cv2
import tkinter as tk
from threading import Thread
from cvzone.HandTrackingModule import HandDetector

# Initialize serial communication with Arduino
arduino_connection = serial.Serial('COM6', 9600, timeout=1)

# Global variables
is_tracking = False
tracking_mode = "Face"
detector = HandDetector(detectionCon=0.8, maxHands=1)
horizontal_position = 90  # Default position
vertical_position = 90  # Default position
consistent_detect_count = 0
last_detected_gesture = None

# Function to send motor control commands to Arduino
def send_motor_command(horizontal_adjust, vertical_adjust):
    global horizontal_position, vertical_position
    horizontal_position = max(0, min(180, horizontal_position + horizontal_adjust))
    vertical_position = max(45, min(162, vertical_position + vertical_adjust))
    command = f"{horizontal_adjust},{vertical_adjust}\r"
    arduino_connection.write(command.encode())
    print(f"Motor Command Sent: {command}")

# Function to reset all motors to initial positions
def reset_motors():
    global horizontal_position, vertical_position
    arduino_connection.write(b"RESET\r")  # Send reset command
    response = arduino_connection.readline().decode().strip()  # Read response
    if response.startswith("INIT"):
        try:
            positions = response.split(":")[1].split(",")
            horizontal_position = int(positions[0])
            vertical_position = int(positions[1])
            update_status("Motors Reset to Initial Positions", "blue")
        except (ValueError, IndexError):
            update_status("Error in Reset Response", "red")
    else:
        update_status("Reset Failed", "red")

# Function to update the status label in the GUI
def update_status(message, color):
    status_label.config(text=message, fg=color)

# Function to enable/disable start/stop buttons
def toggle_buttons(start_enabled):
    start_button.config(state=tk.NORMAL if start_enabled else tk.DISABLED)
    stop_button.config(state=tk.DISABLED if start_enabled else tk.NORMAL)

# Function to handle manual control
def manual_control(horizontal_adjust, vertical_adjust):
    send_motor_command(horizontal_adjust, vertical_adjust)
    update_status(f"Manual Control: H={horizontal_position}°, V={vertical_position}°", "green")

# Function to handle gesture tracking
def gesture_tracking():
    global is_tracking, consistent_detect_count, last_detected_gesture
    is_tracking = True
    update_status("Gesture Tracking: Active", "green")
    toggle_buttons(start_enabled=False)
    send_mode_to_arduino("Gesture Tracking Mode")  # Send mode to Arduino

    video_capture = cv2.VideoCapture(0)

    while is_tracking:
        ret, frame = video_capture.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        hands, img = detector.findHands(frame)

        if hands:
            lm_list = hands[0]
            fingers_up = detector.fingersUp(lm_list)

            if fingers_up == last_detected_gesture:
                consistent_detect_count += 1
            else:
                consistent_detect_count = 1
                last_detected_gesture = fingers_up

            if consistent_detect_count == 8:
                consistent_detect_count = 0
                if fingers_up == [0, 1, 0, 0, 0]:
                    send_motor_command(-9, 0)  # Rotate horizontally left
                elif fingers_up == [0, 1, 1, 0, 0]:
                    send_motor_command(9, 0)   # Rotate horizontally right
                elif fingers_up == [0, 1, 1, 1, 0]:
                    send_motor_command(0, -9)  # Rotate vertically down
                elif fingers_up == [0, 1, 1, 1, 1]:
                    send_motor_command(0, 9)   # Rotate vertically up

        cv2.imshow("Gesture Tracking", img)
        if cv2.waitKey(20) & 0xFF == ord('q'):
            break

    video_capture.release()
    cv2.destroyAllWindows()
    update_status("Gesture Tracking: Inactive", "red")
    send_mode_to_arduino("Idle")  # Send mode to Arduino
    toggle_buttons(start_enabled=True)

# Function to handle face tracking
def face_tracking():
    global is_tracking, horizontal_position, vertical_position
    is_tracking = True
    update_status("Face Tracking: Active", "green")
    toggle_buttons(start_enabled=False)
    send_mode_to_arduino("Face Tracking Mode")  # Send mode to Arduino

    video_capture = cv2.VideoCapture(0)
    face_detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    screen_width = 640  # Default video capture width
    screen_height = 480  # Default video capture height

    while is_tracking:
        ret, frame = video_capture.read()
        if not ret:
            break

        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_detector.detectMultiScale(gray_frame, 1.1, 4)

        if len(faces) > 0:
            x, y, w, h = faces[0]
            face_center_x = x + w // 2
            face_center_y = y + h // 2

            horizontal_adjust = int((face_center_x - screen_width // 2) / 20)
            vertical_adjust = int((screen_height // 2 - face_center_y) / 20)

            send_motor_command(horizontal_adjust, vertical_adjust)

            # Draw a rectangle around the face
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

        cv2.imshow("Face Tracking", frame)
        if cv2.waitKey(20) & 0xFF == ord('q'):
            break

    video_capture.release()
    cv2.destroyAllWindows()
    update_status("Face Tracking: Inactive", "red")
    send_mode_to_arduino("Idle")  # Send mode to Arduino
    toggle_buttons(start_enabled=True)

# Function to handle manual tracking
def manual_tracking():
    send_mode_to_arduino("Manual Tracking Mode")  # Send mode to Arduino
    update_status("Manual Tracking Mode: Active", "green")
    toggle_buttons(start_enabled=False)
    # Here we can add logic for manual control or other functionality as needed

# Function to send the current mode to Arduino
def send_mode_to_arduino(mode):
    arduino_connection.write(f"MODE:{mode}\r".encode())
    print(f"Mode Sent to Arduino: {mode}")

# Function to start tracking based on the selected mode
def start_tracking():
    global tracking_mode, is_tracking
    if is_tracking:
        return  # Avoid starting another tracking if one is already running
    tracking_mode = mode_var.get()
    if tracking_mode == "Gesture":
        Thread(target=gesture_tracking).start()
    elif tracking_mode == "Face":
        Thread(target=face_tracking).start()
    elif tracking_mode == "Manual":
        Thread(target=manual_tracking).start()

# Function to stop tracking
def stop_tracking():
    global is_tracking
    is_tracking = False
    update_status("Tracking Stopped", "red")
    toggle_buttons(start_enabled=True)

# Tkinter GUI setup
root = tk.Tk()
root.title("Tracking Control Panel")

mode_var = tk.StringVar(value="Face")

frame = tk.Frame(root)
frame.pack(pady=10)

tk.Label(frame, text="Select Tracking Mode:").grid(row=0, column=0, padx=5, pady=5)
tk.Radiobutton(frame, text="Face Tracking", variable=mode_var, value="Face").grid(row=0, column=1, padx=5, pady=5)
tk.Radiobutton(frame, text="Gesture Tracking", variable=mode_var, value="Gesture").grid(row=0, column=2, padx=5, pady=5)
tk.Radiobutton(frame, text="Manual Tracking", variable=mode_var, value="Manual").grid(row=0, column=3, padx=5, pady=5)

# Add instructions text
instructions = """
Welcome to the Gesture Tracking Software!
Here's how to use the application:

1. Gesture Tracking:
   Select this mode to track and respond to hand gestures. \n - Index finger up to rotate left \n - index and middle fingers up to rotate right \n - index, middle, and ring fingers up to rotate up \n - all fingers up (excluding thumb) to rotate down

2. Face Tracking:
   Switch to this mode to track faces in real time.

3. Manual Control:
   Use arrow keys or the buttons on-screen to control the device manually.

Make your selection by clicking on one of the buttons below.
"""
instructions_label = tk.Label(root, text=instructions, font=("Helvetica", 12), justify="left", wraplength=550)
instructions_label.pack(pady=10)

start_button = tk.Button(frame, text="Start Tracking", command=start_tracking)
start_button.grid(row=1, column=0, padx=5, pady=5)

stop_button = tk.Button(frame, text="Stop Tracking", command=stop_tracking, state=tk.DISABLED)
stop_button.grid(row=1, column=1, padx=5, pady=5)

reset_button = tk.Button(frame, text="Reset Motors", command=reset_motors)
reset_button.grid(row=1, column=2, padx=5, pady=5)

manual_frame = tk.Frame(root)
manual_frame.pack(pady=10)

tk.Label(manual_frame, text="Manual Control:").grid(row=0, column=0, columnspan=3)

tk.Button(manual_frame, text="Up", command=lambda: manual_control(0, 9)).grid(row=1, column=1)
tk.Button(manual_frame, text="Left", command=lambda: manual_control(-9, 0)).grid(row=2, column=0)
tk.Button(manual_frame, text="Right", command=lambda: manual_control(9, 0)).grid(row=2, column=2)
tk.Button(manual_frame, text="Down", command=lambda: manual_control(0, -9)).grid(row=3, column=1)

status_label = tk.Label(root, text="Status: Idle", fg="blue")
status_label.pack(pady=10)

# Start the Tkinter main loop
root.mainloop()
