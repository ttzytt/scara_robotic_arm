from src.mecanum_chassis import MecanumChassis
from src.arm import Arm, LinkAngleChecker
from src.pusher import Pusher
from src.motor_controller import I2CticMotorController, StepMode
from src.consts import ur
from src.kinematics import ParaScaraSetup
from dataclasses import dataclass
from typing import Self
from gpiozero import Motor


@dataclass
class Robot:
    chassis: MecanumChassis
    arm: Arm
    pusher: Pusher

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.arm.clean_up()


def _get_default_robot() -> Robot:
    lf_step_motor = I2CticMotorController(
        bus_num=1, address=15, is_reversed=True, step_mode=StepMode._4
    )

    rt_step_motor = I2CticMotorController(
        bus_num=1, address=14, is_reversed=True, step_mode=StepMode._4
    )

    CURRENT_LIMIT = 9
    lf_step_motor.tic.set_current_limit(CURRENT_LIMIT)
    rt_step_motor.tic.set_current_limit(CURRENT_LIMIT)

    arm_setup = ParaScaraSetup(
        lf_base_len=85 * ur.mm,
        rt_base_len=85 * ur.mm,
        lf_link_len=85 * ur.mm,
        rt_link_len=85 * ur.mm,
        axis_dist=55 * ur.mm,
    )

    arm = Arm(
        setup=arm_setup,
        lf_motor=lf_step_motor,
        rt_motor=rt_step_motor,
        workspace_checker=LinkAngleChecker(arm_setup),
    )

    lf_tp_dc_motor = Motor(forward=15, backward=14, pwm=True)
    rt_tp_dc_motor = Motor(forward=24, backward=23, pwm=True)
    rt_bt_dc_motor = Motor(forward=25, backward=8, pwm=True)
    lf_bt_dc_motor = Motor(forward=7, backward=1, pwm=True)

    chassis = MecanumChassis(
        lf_tp_motor=lf_tp_dc_motor,
        rt_tp_motor=rt_tp_dc_motor,
        lf_bt_motor=lf_bt_dc_motor,
        rt_bt_motor=rt_bt_dc_motor,
        lf_tp_motor_coef=1.0,
        rt_tp_motor_coef=1.0,
        lf_bt_motor_coef=1.0,
        rt_bt_motor_coef=1.0,
    )

    pusher = Pusher(pin=17, servo_rg=(-1, 1), _reversed=False)

    return Robot(chassis=chassis, arm=arm, pusher=pusher)


DEFAULT_ROBOT = _get_default_robot()
