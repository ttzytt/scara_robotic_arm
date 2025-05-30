import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.motor_controller import I2CticMotorController
from src.arm import ArmController
from src.consts import *
from src.kinematics import ParaScaraSetup

lf_motor = I2CticMotorController(1, 14, True)
rf_motor = I2CticMotorController(1, 15, True)
setup = ParaScaraSetup(
    lf_base_len=85 * ur.mm,
    rt_base_len=85 * ur.mm,
    lf_link_len=85 * ur.mm,
    rt_link_len=85 * ur.mm,
    axis_dist=55 * ur.mm,
)
arm_controller = ArmController(setup, lf_motor, rf_motor)


def main():
    while (
        input(
            "Please move the two motors to perpendicular position and enter `y` to continue: "
        )
        != "y"
    ):
        pass
    arm_controller.reset_deg(90, 90)

    while True:
        pos = input("Enter the position to move to (x mm, y mm): ")
        x, y = pos.split(",")
        x = float(x)
        y = float(y)
        arm_controller.move_to_pos_blocking(x * ur.mm, y * ur.mm)
        print("Reached target position")


if __name__ == "__main__":
    try:
        main()
    finally:
        arm_controller.clean_up()
