import sys
import os
import numpy as np 
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.motor_controller import I2CticMotorController, StepMode
from src.arm_controller import ArmController
from src.consts import *
from src.kinematics import ParaScaraSetup
import time
lf_motor = I2CticMotorController(1, 15, True, step_mode=StepMode._8)
rf_motor = I2CticMotorController(1, 14, True, step_mode=StepMode._8)
setup = ParaScaraSetup(
    lf_base_len=85 * ur.mm,
    rt_base_len=85 * ur.mm,
    lf_link_len=85 * ur.mm,
    rt_link_len=85 * ur.mm,
    axis_dist=55 * ur.mm,
)
arm_controller = ArmController(setup, lf_motor, rf_motor)

Y_MM = 100
MIN_X_MM = -80
MAX_X_MM = 130

def main():
    while (
        input(
            "Please move the two motors to perpendicular position and enter `y` to continue: "
        )
        != "y"
    ):
        pass
    arm_controller.reset_deg(90, 90)

    while(
        input(
            "Please enter `y` to start: "
        ) != 'y'
    ): 
        pass


    while True:
        for idx, cur_x in enumerate(np.linspace(MIN_X_MM, MAX_X_MM, 100)):
            arm_controller.move_to_pos(cur_x * ur.mm, Y_MM * ur.mm)
            if idx == 0: arm_controller.block_until_reach()
            time.sleep(.005)
        arm_controller.block_until_reach()

        for idx, cur_x in enumerate(reversed(np.linspace(MIN_X_MM, MAX_X_MM, 100))):
            arm_controller.move_to_pos(cur_x * ur.mm, Y_MM * ur.mm)
            if idx == 0:
                arm_controller.block_until_reach()
            time.sleep(0.005)
        arm_controller.block_until_reach()

if __name__ == "__main__":
    try:
        main()
    finally:
        arm_controller.clean_up()
