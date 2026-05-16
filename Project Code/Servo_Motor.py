from gpiozero import DigitalOutputDevice, PWMOutputDevice
import time
LF_IN1, LF_IN2 = 17, 22
LB_IN1, LB_IN2 = 24, 25
RF_IN1, RF_IN2 = 6, 5
RB_IN1, RB_IN2 = 26, 16
PWM1_PIN = 12
PWM2_PIN = 13

lf_in1 = DigitalOutputDevice(LF_IN1)
lf_in2 = DigitalOutputDevice(LF_IN2)
lb_in1 = DigitalOutputDevice(LB_IN1)
lb_in2 = DigitalOutputDevice(LB_IN2)
rf_in1 = DigitalOutputDevice(RF_IN1)
rf_in2 = DigitalOutputDevice(RF_IN2)
rb_in1 = DigitalOutputDevice(RB_IN1)
rb_in2 = DigitalOutputDevice(RB_IN2)
pwm_left = PWMOutputDevice(PWM1_PIN, frequency=1000)

pwm_right = PWMOutputDevice(PWM2_PIN, frequency=1000)

def set_motors(lf, lb, rf, rb, speed_left=1, speed_right=1):
    rf_in1.value = 1 if rf == 1 else 0
    rf_in2.value = 1 if rf == -1 else 0
    lb_in1.value = 1 if lb == 1 else 0 
    lb_in2.value = 1 if lb == -1 else 0
    lf_in1.value = 1 if lf == 1 else 0
    lf_in2.value = 1 if lf == -1 else 0
    rb_in1.value = 1 if rb == 1 else 0
    rb_in2.value = 1 if rb == -1 else 0
    pwm_right.value= speed_right
    pwm_left.value = speed_left 
   

def movFwdDC(speed_left=1, speed_right=1):
    set_motors(1,1,1,1,speed_left, speed_right)
    
def movRevDC(speed_left=1, speed_right=1):
    set_motors(-1, -1, -1, -1, speed_left, speed_right)
    
def movLeftDC(speed_left=1, speed_right=1):
    set_motors(1, -1, 1, -1, speed_left, speed_right)
    
def movRightDC(speed_left=1, speed_right=1):
    set_motors(-1, 1, -1, 1, speed_left, speed_right)

def rotateCW(speed_left=1, speed_right=1):
    set_motors(1, 1, -1, -1, speed_left, speed_right)
    
def rotateCCW(speed_left=1, speed_right=1):
    set_motors(-1, -1, 1, 1, speed_left, speed_right)

def circle():
    set_motors(1,1,0,1,0.45,0.5)

def stop():
    set_motors(0,0,0,0,0,0)
