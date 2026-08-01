import sob
import os
import dotenv
import asyncio
import time
import modi_plus as modi
import math

GIGI = None

def init_gigi():
    global GIGI
    if GIGI:
        return GIGI
    GIGI = modi.MODIPlus()
    print(GIGI.modules)
    return GIGI

async def arm_ctrl(dn_ang=30, up_ang=90):
    gigi = init_gigi()
    now_ang = up_ang
    motor = gigi.motors[0]
    butoon = gigi.buttons[0]
    while True:
        if butoon.toggled:
            now_ang = up_ang
        else:
            now_ang = dn_ang
        motor.set_angle(now_ang)
        await asyncio.sleep(0.01) 

async def check_fall(threshold=80):
    gigi = init_gigi()
    imu = gigi.imus[0]
    while True:
        ang = imu.angle
        ang = (ang[0], ang[1]+90)
        tmp = math.sqrt(ang[0]**2+ang[1]**2)
        if threshold < tmp:
            return True
        await asyncio.sleep(0.01) 