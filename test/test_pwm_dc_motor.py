# from gpiozero import PWMOutputDevice
# from time import sleep

# # Define the two GPIO pins as outputs
# motor_pin1 = PWMOutputDevice(15)
# motor_pin2 = PWMOutputDevice(14)


# # Rotate in one direction
# motor_pin1.value = 1  # Full speed in one direction
# motor_pin2.off()
# sleep(2)

# # Rotate in the opposite direction
# motor_pin1.off()
# motor_pin2.value = .5
# sleep(2)

# # Stop the motor
# motor_pin1.off()
# motor_pin2.off()


from gpiozero import Motor
from time import sleep

motor = Motor(forward=7, backward=1, pwm=True)

motor.forward(0.5)  # Run forward at 50% speed
sleep(2)
motor.backward(1)   # Run backward at 100% speed
sleep(2)
motor.stop()
