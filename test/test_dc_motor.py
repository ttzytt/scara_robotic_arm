from gpiozero import OutputDevice
from time import sleep

# Define the two GPIO pins as outputs
motor_pin1 = OutputDevice(15)
motor_pin2 = OutputDevice(14)


# Rotate in one direction
motor_pin1.on()
motor_pin2.off()
sleep(2)

# Rotate in the opposite direction
motor_pin1.off()
motor_pin2.on()
sleep(2)

# Stop the motor
motor_pin1.off()
motor_pin2.off()
