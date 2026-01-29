import serial
import time
import tkinter as tk
from tkinter import messagebox

# --- Serial Setup ---
try:
    # Change '/dev/ttyACM0' to your actual Pi/Arduino port
    ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
    time.sleep(2) 
except Exception as e:
    print(f"Connection Error: {e}")

def run_sequence():
    if not ser.is_open:
        messagebox.showerror("Error", "Arduino not connected!")
        return

    # Iterate through servos 1 to 10 in order
    for i in range(1, 11):
        # Check if the tickbox for this servo is active
        if servo_vars[i].get():
            print(f"Activating Servo {i}...")
            ser.write(f"{i}\n".encode())
            
            # We wait for the servo to finish (2 seconds total in Arduino)
            # plus a tiny bit of buffer for serial communication
            time.sleep(2.2) 

    print("Sequence Complete.")

# --- UI Setup ---
root = tk.Tk()
root.title("Servo Sequence Controller")
root.geometry("350x600")

tk.Label(root, text="Select Servos for Sequence", font=("Arial", 12, "bold")).pack(pady=10)

# Dictionary to hold the state of each checkbox (True/False)
servo_vars = {}

# Create two frames to organize 1-5 and 6-10 visually
frame_left = tk.Frame(root)
frame_left.pack(side=tk.LEFT, padx=20, fill=tk.Y)

frame_right = tk.Frame(root)
frame_right.pack(side=tk.RIGHT, padx=20, fill=tk.Y)

for i in range(1, 11):
    var = tk.BooleanVar()
    servo_vars[i] = var
    
    # Place 1-5 in the left frame, 6-10 in the right
    target_frame = frame_left if i <= 5 else frame_right
    
    cb = tk.Checkbutton(target_frame, text=f"Servo {i}", variable=var, font=("Arial", 10))
    cb.pack(anchor="w", pady=5)

# --- Control Buttons ---
btn_frame = tk.Frame(root)
btn_frame.pack(side=tk.BOTTOM, pady=20)

start_btn = tk.Button(
    btn_frame, 
    text="START SEQUENCE", 
    command=run_sequence,
    bg="#4CAF50", 
    fg="white",
    font=("Arial", 10, "bold"),
    padx=10,  # Horizontal internal padding
    pady=10   # Vertical internal padding
)
start_btn.pack(pady=5)

def clear_all():
    for var in servo_vars.values():
        var.set(False)

clear_btn = tk.Button(btn_frame, text="Clear All", command=clear_all)
clear_btn.pack()

root.mainloop()