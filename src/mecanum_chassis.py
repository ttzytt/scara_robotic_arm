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
    
    def move(self, x : float, y : float, heading : float):
        """
        Move the chassis in the specified direction with the specified speed.
        x: forward/backward speed
        y: left/right speed
        heading: rotation speed
        """
        lf_tp_speed = x + y + heading
        rt_tp_speed = x - y - heading
        lf_bt_speed = x - y + heading
        rt_bt_speed = x + y - heading

        self.lf_tp_motor.value = lf_tp_speed * self.lf_tp_motor_coef
        self.rt_tp_motor.value = rt_tp_speed * self.rt_tp_motor_coef
        self.lf_bt_motor.value = lf_bt_speed * self.lf_bt_motor_coef
        self.rt_bt_motor.value = rt_bt_speed * self.rt_bt_motor_coef