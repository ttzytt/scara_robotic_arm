from gpiozero import Servo
# Initialize servo on GPIO17
servo = Servo(17)
servo.mid()  # Set to center initially
print("Servo initialized to middle position (0.0).")

print("Enter a value between -1 (min/left) and 1 (max/right) to move the servo.")
print("Type 'exit' to quit.")

while True:
    try:
        command = input("Enter position [-1 to 1]: ").strip()
        if command.lower() == 'exit':
            print("Exiting...")
            break
        value = float(command)
        if -1 <= value <= 1:
            servo.value = value
            print(f"Moved servo to {value}")
        else:
            print("Please enter a value between -1 and 1.")
    except ValueError:
        print("Invalid input. Enter a number between -1 and 1 or type 'exit'.")
