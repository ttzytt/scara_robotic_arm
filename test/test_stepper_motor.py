from smbus2 import SMBus
from ticlib import ticlib
from ticlib import TicI2C, SMBus2Backend
from time import sleep

bus = SMBus(1)  # Represents /dev/i2c-3
address = 14  # Address of the Tic, that is its device number
backend = SMBus2Backend(bus, address)

tic = TicI2C(backend)
tic2 = TicI2C(SMBus2Backend(bus, 15))
tic.halt_and_set_position(0)
tic2.halt_and_set_position(0)
tic.energize()
tic2.energize()
tic.exit_safe_start()
tic2.exit_safe_start()

positions = [50, 30, 80, 0]
for position in positions:
    tic.set_target_position(position)
    tic2.set_target_position(position)
    cur_pos = tic.get_current_position()
    cur_pos2 = tic2.get_current_position()
    while cur_pos != position or cur_pos2 != position: 
        cur_pos = tic.get_current_position()
        cur_pos2 = tic2.get_current_position()
        print("cur_pos: ", cur_pos, " tar pos ", tic.get_target_position())


tic.deenergize()
tic2.deenergize()
tic.enter_safe_start()
tic2.enter_safe_start()