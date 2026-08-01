import sob
import os
import dotenv
import asyncio
import time
import modi_plus as modi
import math
from logger import printf

GIGI = None

def init_gigi():
    global GIGI
    if GIGI:
        return GIGI
    GIGI = modi.MODIPlus()
    print(GIGI.modules)
    return GIGI

async def arm_ctrl(sender_token, dn_ang=135, up_ang=210, my_lang="베트남어"):
    gigi = init_gigi()
    now_ang = up_ang
    motor = gigi.motors[0]
    butoon = gigi.buttons[0]
    is_recording = False
    
    printf(f"{butoon.toggled}")
    
    async def record_and_send():
        try:
            async def countdown(sec):
                for i in range(sec, 0, -1):
                    printf(f"{i}...")
                    await asyncio.sleep(1)
            printf("녹음 시작 (5초)...")
            record_task = asyncio.to_thread(sob.rec, 5)
            count_task = countdown(5)
            audio_path, _ = await asyncio.gather(record_task, count_task)
            printf("변환 중...")
            text = await asyncio.to_thread(sob.s2t, audio_path)
            printf(f"인식된 텍스트: {text}")
            printf(f"번역 작업을 진행하겠읍니다.")
            text = sob.translate(text, {my_lang}, "한국어")
            printf(f"번역 결과: {text}")
            if text:
                await sob.send(sender_token, f"음성 메시지: \n{text}")
                printf("아무쪼록 텍스트를 잘 보냈읍니다.")
        except Exception as e:
            printf(f"STT 처리 오류: {e}")
            
    while True:
        if butoon.toggled:
            now_ang = up_ang
        else:
            now_ang = dn_ang
            
        motor.set_angle(now_ang)
        
        if now_ang == up_ang and not is_recording:
            is_recording = True
            asyncio.create_task(record_and_send())
            
        if now_ang == dn_ang:
            is_recording = False
            
        await asyncio.sleep(0.01) 

async def check_fall(sender_token, threshold=80):
    gigi = init_gigi()
    imu = gigi.imus[0]
    has_fall = False
    while True:
        ang = imu.angle
        ang = (ang[0], ang[1]+90)
        tmp = math.sqrt(ang[0]**2+ang[1]**2)
        if threshold < tmp:
            if not has_fall:
                await sob.send(sender_token, f"낙상 발생: @{time.time()}")
                await asyncio.sleep(0.5)
            has_fall = True
        await asyncio.sleep(0.01)

async def joystick_ctrl(sender_token):
    gigi = init_gigi()
    if not gigi.joysticks:
        printf("조이스틱 연결 안 됨")
        return
        
    joystick = gigi.joysticks[0]
    last_msg = None
    
    while True:
        msg = None
        try:
            direction = getattr(joystick, 'direction', "CENTER")
            if direction == "UP": msg = "단축표현: 도와주세요!"
            elif direction == "DOWN": msg = "단축표현: 괜찮습니다!"
            elif direction == "LEFT": msg = "단축표현: 아파요!"
            elif direction == "RIGHT": msg = "단축표현: 안전합니다!"
            if not msg:
                if getattr(joystick, 'up', False) == True or (callable(getattr(joystick, 'up', None)) and joystick.up()):
                    msg = "단축표현: 도와주세요!"
                elif getattr(joystick, 'down', False) == True or (callable(getattr(joystick, 'down', None)) and joystick.down()):
                    msg = "단축표현: 괜찮습니다!"
                elif getattr(joystick, 'left', False) == True or (callable(getattr(joystick, 'left', None)) and joystick.left()):
                    msg = "단축표현: 아파요!"
                elif getattr(joystick, 'right', False) == True or (callable(getattr(joystick, 'right', None)) and joystick.right()):
                    msg = "단축표현: 안전합니다!"
        except Exception as e:
            pass
            
        if msg and msg != last_msg:
            await sob.send(sender_token, f"환자 상태: {msg}")
            
        if not msg:
            last_msg = None
        else:
            last_msg = msg
            
        await asyncio.sleep(0.1)