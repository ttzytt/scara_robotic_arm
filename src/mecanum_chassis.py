from gpiozero import Motor

class MecanumChassis:
    def __init__(self, 
                 lf_tp_motor: Motor, 
                 rt_tp_motor: Motor, 
                 lf_bt_motor: Motor, 
                 rt_bt_motor: Motor, 
                 lf_tp_motor_coef : float = 1.0, 
                 rt_tp_motor_coef : float = 1.0,
                 lf_bt_motor_coef : float = 1.0,
                 rt_bt_motor_coef : float = 1.0,
                 ):
        self.lf_tp_motor = lf_tp_motor
        self.rt_tp_motor = rt_tp_motor
        self.lf_bt_motor = lf_bt_motor
        self.rt_bt_motor = rt_bt_motor
        self.lf_tp_motor_coef = lf_tp_motor_coef
        self.rt_tp_motor_coef = rt_tp_motor_coef
        self.lf_bt_motor_coef = lf_bt_motor_coef
        self.rt_bt_motor_coef = rt_bt_motor_coef
        self.lf_tp_motor.forward(0)
        self.rt_tp_motor.forward(0)
        self.lf_bt_motor.forward(0)
        self.rt_bt_motor.forward(0)
    
    def move(self, x: float, y: float, heading: float):
        """
        x: forward/backward  (−1...1)
        y: left/right        (−1...1)
        heading: rotation    (−1...1)
        """

        # 1) compute raw wheel speeds
        lf =  x + y + heading   # left-front
        rf =  x - y - heading   # right-front
        lb =  x - y + heading   # left-back
        rb =  x + y - heading   # right-back

        # 2) find the largest magnitude
        max_mag = max(abs(lf), abs(rf), abs(lb), abs(rb), 1.0)

        # 3) normalize so max magnitude is 1.0
        lf /= max_mag
        rf /= max_mag
        lb /= max_mag
        rb /= max_mag

        # 4) apply your per-motor coefficients and send to GPIOZero
        self.lf_tp_motor.value = lf * self.lf_tp_motor_coef
        self.rt_tp_motor.value = rf * self.rt_tp_motor_coef
        self.lf_bt_motor.value = lb * self.lf_bt_motor_coef
        self.rt_bt_motor.value = rb * self.rt_bt_motor_coef
