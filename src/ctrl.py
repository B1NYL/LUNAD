import sob
import os
import dotenv
import asyncio
import time
import modi_plus as modi
gigi = modi.MODIPlus()
gigi.modules

async def arm_ctrl(dn_ang=30, up_ang=90):
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