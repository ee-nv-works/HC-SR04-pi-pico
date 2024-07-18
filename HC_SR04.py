from machine import Pin, PWM
from rp2 import PIO, StateMachine, asm_pio
import time
import utime

'''
Pins for the HC-SR04
'''
#Output of signal from the pi pico to HC-SR04 to trigger the echo
#It's supposed to be 10us but it seemed to just trigger off of the falling edge?
trigger0 = Pin(14, Pin.OUT)

#The signal output from the HC-SR04
echo0 = Pin(15, Pin.IN, Pin.PULL_DOWN)

'''
Temp sensor
'''
#init temp
sensor_temp = machine.ADC(4)
conv_factor = 3.3/65535
#Temp calc
read_temp = sensor_temp.read_u16()*conv_factor
sys_temp = 27 - (read_temp - 0.706)/0.001721
#globals
timer_up=0
timer_down=0

#interrupt function
def intrpt_trig(x_i):
    global timer_up, timer_down
    if x_i.value() == 1:
        timer_up = utime.ticks_us()
    if x_i.value() == 0:
        timer_down = utime.ticks_us()

#init the utime as the first call of it is wildly inaccurate
utime.sleep_us(5)

#interrupt handler
echo0.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=intrpt_trig)

#Function that takes in the trigger output pin and then taking multiple samples
#Then outputs the average of the mode of the interrupts
#It returns the distance in inches
def trig_echo(trigger_x):
    list_1 =[]
    for i in range(24):
        #the "10us" pulse. In testing the time it mainly triggers off the following edge
        trigger_x.high()
        utime.sleep_us(5)
        trigger_x.low()

        final_time = utime.ticks_diff(timer_down,timer_up)

        #Filter for min & max allowable time for sensor roughly
        if final_time > 100 and final_time < 24000:
            dist_in = (((331+(0.606*sys_temp))*final_time*0.000001) * 39.37008) * 0.5
            list_1.append(dist_in)
        #24ms is the max time for the sensor
        utime.sleep_ms(24)
    
    #remove max and min from list_1
    list_1.remove(max(list_1))
    list_1.remove(min(list_1))
    
    #Get the Average
    out = sum(list_1)/len(list_1)
    
    return out

while True:
    f_dist = trig_echo(trigger0)
    print("Distance",f_dist,"in")
