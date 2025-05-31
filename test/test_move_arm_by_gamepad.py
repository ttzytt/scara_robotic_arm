import sys
import os
import time

import pygame
from pprint import pprint

# add your project root to PATH
sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    ),
)

from src.motor_controller import I2CticMotorController, StepMode
from src.arm import Arm, LinkAngleChecker
from src.kinematics import ParaScaraSetup
from src.consts import ur
import time

# --- CONFIGURABLE PARAMS ---
# maximum Cartesian speed (mm/s) when stick is pushed all the way
MAX_SPEED_MM_S = 150.0

# starting position
START_X_MM = 0
START_Y_MM = 100.0

# pygame joystick axis indices (left stick)
AXIS_X = 0
AXIS_Y = 1

# ---------------------------

def init_arm() -> Arm:
    # build your motors & kinematics just like your ref code
    lf_motor = I2CticMotorController(
        1, 15, True, step_mode=StepMode._8
    )
    rf_motor = I2CticMotorController(
        1, 14, True, step_mode=StepMode._8
    )
    lf_motor.tic.set_current_limit(9) 
    rf_motor.tic.set_current_limit(9)
    setup = ParaScaraSetup(
        lf_base_len=85 * ur.mm,
        rt_base_len=85 * ur.mm,
        lf_link_len=85 * ur.mm,
        rt_link_len=85 * ur.mm,
        axis_dist=55 * ur.mm,
    )
    return Arm(setup, lf_motor, rf_motor, LinkAngleChecker(setup))

def wait_for_reset(arm: Arm):
    # same prompts as your reference
    while input(
        "Please move the two motors to perpendicular position and enter `y` to continue: "
    ).lower() != "y":
        pass
    arm.reset_deg(90, 90)
    print(f"Starting position: ({START_X_MM:.1f}, {START_Y_MM:.1f}) mm")
    while input("Enter `y` to start joystick‐control loop: ").lower() != "y":
        pass

def main():
    # 1) initialize arm
    arm = init_arm()

    try:
        # 2) reset to home
        wait_for_reset(arm)

        print("init state")
        pprint(arm.get_current_state(mode='o')[0].to_unit(ur.mm, ur.deg))
        prev_state = arm.get_current_state(mode='o')[0]
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
            st_time = time.time()
            # a) handle quit
            for evt in pygame.event.get():
                if evt.type == pygame.QUIT:
                    running = False

            # b) read axes
            # note: many controllers report up as negative, so we invert Y
            raw_x = js.get_axis(AXIS_X)  # −1 .. +1
            raw_y = -js.get_axis(AXIS_Y)  # invert so up is +
            if abs(raw_x) < 0.05:
                raw_x = 0.0
            if abs(raw_y) < 0.05:
                raw_y = 0.0
            print(f"raw_x: {raw_x:.2f}, raw_y: {raw_y:.2f}")
            # c) compute dt
            now = time.time()
            dt = now - last_time
            last_time = now

            # d) integrate to get new target (in mm)
            dx = raw_x * MAX_SPEED_MM_S * dt
            dy = raw_y * MAX_SPEED_MM_S * dt
            target_x += dx
            target_y += dy

            # e) clamp within your workspace if desired
            # target_x = np.clip(target_x, MIN_X_MM, MAX_X_MM)
            # target_y = np.clip(target_y, MIN_Y_MM, MAX_Y_MM)

            # f) send new target to arm
            try:
                if not arm.is_pos_valid(target_x * ur.mm, target_y * ur.mm):
                    target_x -= dx
                    target_y -= dy
                    continue
            except (IndexError, ValueError) as e:
                target_x -= dx
                target_y -= dy
                print(e)
                print("previous state")
                pprint(prev_state.to_unit(ur.mm, ur.deg))
                continue
            
            try:
                arm.move_to_pos(target_x * ur.mm, target_y * ur.mm)
            except ValueError as e:
                target_x -= dx
                target_y -= dy
                print(e)
                print("previous state")
                pprint(prev_state.to_unit(ur.mm, ur.deg))
                continue
            # g) read back & print current end‐effector pos
            

            try:
                state = arm.get_current_state(mode='oi')[0]
            except IndexError as e:
                target_x -= dx
                target_y -= dy
                print(e)
                print("previous state")
                pprint(prev_state.to_unit(ur.mm, ur.deg))
                continue
            cur_x = state.end_effector_pos[0].to(ur.mm).m
            cur_y = state.end_effector_pos[1].to(ur.mm).m
            print(f"→ Target: ({target_x:.1f}, {target_y:.1f}) mm  |  "
                  f"Actual: ({cur_x:.1f}, {cur_y:.1f}) mm")

            # h) cap loop rate
            ed_time = time.time() 
            print(f"Loop time: {ed_time - st_time:.3f} s")
            clock.tick(60)

    finally:
        print("Cleaning up…")
        arm.clean_up()
        pygame.quit()

if __name__ == "__main__":
    main()
