import sys 
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.motor_controller import I2CticMotorController

lf_motor = I2CticMotorController(1, 14, False)
# rf_motor = I2CticMotorController(1, 15, False)

def main():

    while input("enter `y` to indicate zero degree position of the stepper motor: ") != 'y':
        pass
    lf_motor.reset_pos(0)

    while True: 
        deg = float(input("Enter the degree to move to: "))
        lf_motor.move_to_angle_blocking_in_close_dir(deg)
        print("Reached target position")

if __name__ == "__main__":
    try: 
        main()
    finally: 
        lf_motor.tic.deenergize()