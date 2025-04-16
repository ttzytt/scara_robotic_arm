from smbus2 import SMBus
from ticlib import TicI2C, SMBus2Backend
from ticlib.ticlib import TicBase
from enum import Enum
from dataclasses import dataclass
from typing import Optional


class StepMode(Enum):
    @dataclass
    class ModeInfo:
        mode_code: int
        divisor: int

    _1 = ModeInfo(0, 1)
    _2 = ModeInfo(1, 2)
    _4 = ModeInfo(2, 4)
    _8 = ModeInfo(3, 8)
    _16 = ModeInfo(4, 16)
    _32 = ModeInfo(5, 32)
    _64 = ModeInfo(6, 64)

    @property
    def mode_code(self):
        return self.value.mode_code

    @property
    def divisor(self):
        return self.value.divisor


class TicMotorController:
    def __init__(
        self,
        tic_base: TicBase,
        is_reversed: bool,
        step_mode: StepMode = StepMode._2,
        gear_ratio: float = 1,
        max_deg_per_sec: float = 360,
        max_acc_deg_per_sec2: float = 1800,
        deg_per_step: float = 1.8,
    ) -> None:
        self.tic = tic_base
        self.is_reversed = is_reversed
        self.step_mode = step_mode
        self.gear_ratio = gear_ratio
        self.max_deg_per_sec = max_deg_per_sec
        self.max_acc_deg_per_sec2 = max_acc_deg_per_sec2

        self.tic.deenergize()
        self.tic.set_step_mode(step_mode.mode_code)

        self.deg_per_micro_step = deg_per_step / step_mode.divisor * gear_ratio
        self.set_spd(max_deg_per_sec)
        self.set_acc(max_acc_deg_per_sec2)
        self.mstep_per_rev = round(360 / self.deg_per_micro_step)

    def set_spd(self, max_deg_per_sec: float):
        max_mstep_per_sec = round(max_deg_per_sec / self.deg_per_micro_step * 100_00)
        self.tic.set_max_speed(max_mstep_per_sec)

    def set_acc(self, max_acc_deg_per_sec2: float):
        max_mstep_per_sec2 = round(max_acc_deg_per_sec2 / self.deg_per_micro_step * 100)
        self.tic.set_max_acceleration(max_mstep_per_sec2)
        self.tic.set_max_deceleration(max_mstep_per_sec2)

    def reset_pos(self, cur_deg: float):
        step = self.deg_to_step(cur_deg)
        if self.is_reversed:
            step = -step
        self.tic.halt_and_set_position(step)
        self.tic.exit_safe_start()
        self.tic.energize()

    def move_to_angle(
        self,
        tar_deg: float,
        is_cw: bool,
        max_deg_per_sec: Optional[float] = None,
        max_acc_deg_per_sec2: Optional[float] = None,
    ):
        cur_step = self.get_current_position()
        cur_deg = self.step_to_deg(cur_step)
        disp = self.calc_deg_disp(cur_deg, tar_deg, is_cw)
        disp_step = self.deg_to_step(disp, is_cw)
        tar_step = cur_step + disp_step
        if max_deg_per_sec is not None:
            self.set_spd(max_deg_per_sec)
        if max_acc_deg_per_sec2 is not None:
            self.set_acc(max_acc_deg_per_sec2)
        self.set_target_position(tar_step)

    def move_to_angle_in_close_dir(
        self, 
        tar_deg: float,
        max_deg_per_sec: Optional[float] = None,
        max_acc_deg_per_sec2: Optional[float] = None,
    ): 
        cur_step = self.get_current_position()
        cur_deg = self.step_to_deg(cur_step)
        disp_cw = self.calc_deg_disp(cur_deg, tar_deg, True)
        disp_ccw = self.calc_deg_disp(cur_deg, tar_deg, False)
        disp = disp_cw if abs(disp_cw) < abs(disp_ccw) else disp_ccw
        self.move_to_angle(tar_deg, disp > 0, max_deg_per_sec, max_acc_deg_per_sec2)

    def move_to_angle_blocking(
        self,
        tar_deg: float,
        is_cw: bool,
        max_deg_per_sec: Optional[float] = None,
        max_acc_deg_per_sec2: Optional[float] = None,
    ):
        self.move_to_angle(tar_deg, is_cw, max_deg_per_sec, max_acc_deg_per_sec2)
        self.block_until_reach()
    def deg_to_step(self, deg: float, is_positive: bool = True) -> int:
        deg = self.wrap_deg(deg, is_positive)
        return round(deg / self.deg_per_micro_step)

    def move_to_angle_blocking_in_close_dir(
        self, 
        tar_deg: float,
        max_deg_per_sec: Optional[float] = None,
        max_acc_deg_per_sec2: Optional[float] = None,
    ):
        self.move_to_angle_in_close_dir(tar_deg, max_deg_per_sec, max_acc_deg_per_sec2)
        self.block_until_reach()

    def step_to_deg(self, step: int, is_positive: bool = True) -> float:
        step = self.wrap_step(step, is_positive)
        return step * self.deg_per_micro_step

    @staticmethod
    def wrap_deg(deg: float, is_positive: bool) -> float:
        return deg % 360 if is_positive else deg % -360

    def wrap_step(self, step: int, is_positive: bool) -> int:
        return step % self.mstep_per_rev if is_positive else -step % self.mstep_per_rev

    @classmethod
    def calc_deg_disp(cls, cur_deg: float, tar_deg: float, is_cw: bool) -> float:
        return cls.wrap_deg(tar_deg - cur_deg, is_cw)

    def set_target_position(self, tar_step: int):
        if self.is_reversed:
            tar_step = -tar_step
        self.tic.set_target_position(tar_step)

    def get_current_position(self):
        if self.is_reversed:
            return -self.tic.get_current_position()
        return self.tic.get_current_position()

    def get_target_position(self):
        if self.is_reversed:
            return -self.tic.get_target_position()
        return self.tic.get_target_position()

    def is_moving(self):
        if (self.get_current_position != self.get_target_position()):
            print(f"current: {self.get_current_position()}, target: {self.get_target_position()}")
        return self.get_current_position() != self.get_target_position()

    def block_until_reach(self):
        while self.is_moving():
            pass


class I2CticMotorController(TicMotorController):
    def __init__(
        self,
        bus_num: int,
        address: int,
        is_reversed: bool,
        step_mode: StepMode = StepMode._2,
        gear_ratio: float = 1,
        max_deg_per_sec: float = 360,
        max_acc_deg_per_sec2: float = 1800,
        deg_per_step: float = 1.8,
    ) -> None:
        bus = SMBus(bus_num)
        backend = SMBus2Backend(bus, address)
        tic = TicI2C(backend)
        super().__init__(
            tic,
            is_reversed,
            step_mode,
            gear_ratio,
            max_deg_per_sec,
            max_acc_deg_per_sec2,
            deg_per_step,
        )
