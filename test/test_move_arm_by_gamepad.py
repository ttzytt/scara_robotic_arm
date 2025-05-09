import sys
import os
import time

import pygame
import numpy as np

# add your project root to PATH
sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    ),
)

from src.motor_controller import I2CticMotorController, StepMode
from src.arm_controller import ArmController
from src.kinematics import ParaScaraSetup
import src.consts as C
import pint

# unit registry
ur = pint.UnitRegistry()

# --- CONFIGURABLE PARAMS ---
# maximum Cartesian speed (mm/s) when stick is pushed all the way
MAX_SPEED_MM_S = 50.0

# starting position
START_X_MM = 100.0
START_Y_MM = 100.0

# pygame joystick axis indices (left stick)
AXIS_X = 0
AXIS_Y = 1

# ---------------------------

def init_arm() -> ArmController:
    # build your motors & kinematics just like your ref code
    lf_motor = I2CticMotorController(
        1, 15, True, step_mode=StepMode._8
    )
    rf_motor = I2CticMotorController(
        1, 14, True, step_mode=StepMode._8
    )
    setup = ParaScaraSetup(
        lf_base_len=85 * ur.mm,
        rt_base_len=85 * ur.mm,
        lf_link_len=85 * ur.mm,
        rt_link_len=85 * ur.mm,
        axis_dist=55 * ur.mm,
    )
    return ArmController(setup, lf_motor, rf_motor)

def wait_for_reset(arm: ArmController):
    # same prompts as your reference
    while input(
        "Please move the two motors to perpendicular position and enter `y` to continue: "
    ).lower() != "y":
        pass
    arm.reset_deg(90, 90)
    START_X_MM = arm.get_current_state()[0].end_effector_pos[0].to(ur.mm).m
    START_Y_MM = arm.get_current_state()[0].end_effector_pos[1].to(ur.mm).m

    while input("Enter `y` to start joystick‐control loop: ").lower() != "y":
        pass

def main():
    # 1) initialize arm
    arm = init_arm()

    try:
        # 2) reset to home
        wait_for_reset(arm)

        # 3) init pygame joystick
        pygame.init()
        pygame.joystick.init()
        if pygame.joystick.get_count() == 0:
            print("❌ No joystick found. Please plug in a gamepad and retry.")
            return
        js = pygame.joystick.Joystick(0)
        js.init()
        print(f"🎮 Using joystick: {js.get_name()}")

        # 4) set up integration state
        target_x = START_X_MM
        target_y = START_Y_MM
        last_time = time.time()

        clock = pygame.time.Clock()
        running = True
        while running:
            # a) handle quit
            for evt in pygame.event.get():
                if evt.type == pygame.QUIT:
                    running = False

            # b) read axes
            # note: many controllers report up as negative, so we invert Y
            raw_x = js.get_axis(AXIS_X)  # −1 .. +1
            raw_y = -js.get_axis(AXIS_Y)  # invert so up is +

            # c) compute dt
            now = time.time()
            dt = now - last_time
            last_time = now

            # d) integrate to get new target (in mm)
            target_x += raw_x * MAX_SPEED_MM_S * dt
            target_y += raw_y * MAX_SPEED_MM_S * dt

            # e) clamp within your workspace if desired
            # target_x = np.clip(target_x, MIN_X_MM, MAX_X_MM)
            # target_y = np.clip(target_y, MIN_Y_MM, MAX_Y_MM)

            # f) send new target to arm
            arm.move_to_pos(target_x * ur.mm, target_y * ur.mm)

            # g) read back & print current end‐effector pos
            state = arm.get_current_state()[0]
            cur_x = state.end_effector_pos[0].to(ur.mm).m
            cur_y = state.end_effector_pos[1].to(ur.mm).m
            print(f"→ Target: ({target_x:.1f}, {target_y:.1f}) mm  |  "
                  f"Actual: ({cur_x:.1f}, {cur_y:.1f}) mm")

            # h) cap loop rate
            clock.tick(60)

    finally:
        print("Cleaning up…")
        arm.clean_up()
        pygame.quit()

if __name__ == "__main__":
    main()
