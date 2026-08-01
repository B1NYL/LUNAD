import sob
import os
import dotenv
import asyncio
import time
import modi_plus as modi
gigi = modi.MODIPlus()
gigi.modules

UP_ANG = 90
DN_ANG = 45
async def arm_ctrl():
    now_ang = UP_ANG
    motor = gigi.motors[0]
    butoon = gigi.buttons[0]
    while True:
        if butoon.toggled:
            now_ang = UP_ANG
        else:
            now_ang = DN_ANG
        motor.set_angle(now_ang)
        await asyncio.sleep(0.01) 