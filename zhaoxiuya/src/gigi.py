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

async def arm_ctrl(sender_token, dn_ang=30, up_ang=90):
    gigi = init_gigi()
    now_ang = up_ang
    motor = gigi.motors[0]
    butoon = gigi.buttons[0]
    is_recording = False
    
    async def record_and_send():
        try:
            print("녹음 시작 (5초)...")
            audio_path = await asyncio.to_thread(sob.rec, 5)
            print("STT 변환 중...")
            text = await asyncio.to_thread(sob.s2t, audio_path)
            print(f"인식된 텍스트: {text}")
            if text:
                await sob.send(sender_token, f"🎙️ 환자 음성 메시지:\n{text}")
        except Exception as e:
            print(f"STT 처리 오류: {e}")
            
    while True:
        if butoon.toggled:
            now_ang = up_ang
        else:
            now_ang = dn_ang
            
        motor.set_angle(now_ang)
        
        # 버튼으로 인해 팔이 내려간 상태일 때 한 번 녹음 실행
        if now_ang == dn_ang and not is_recording:
            is_recording = True
            asyncio.create_task(record_and_send())
            
        # 팔이 다시 올라가면 녹음 플래그 초기화
        if now_ang == up_ang:
            is_recording = False
            
        await asyncio.sleep(0.01) 

async def check_fall(sender_token, threshold=80):
    gigi = init_gigi()
    imu = gigi.imus[0]
    while True:
        ang = imu.angle
        ang = (ang[0], ang[1]+90)
        tmp = math.sqrt(ang[0]**2+ang[1]**2)
        if threshold < tmp:
            await sob.send(sender_token, f"🚨 낙상 발생! @{time.time()}")
            await asyncio.sleep(0.5)
        await asyncio.sleep(0.01)

async def joystick_ctrl(sender_token):
    gigi = init_gigi()
    if not gigi.joysticks:
        print("조이스틱 모듈을 찾을 수 없습니다.")
        return
        
    joystick = gigi.joysticks[0]
    last_msg = None
    
    while True:
        msg = None
        try:
            # PyMODI joystick property check
            direction = getattr(joystick, 'direction', "CENTER")
            if direction == "UP": msg = "🆘 도와주세요!"
            elif direction == "DOWN": msg = "👌 괜찮습니다!"
            elif direction == "LEFT": msg = "🤕 아파요!"
            elif direction == "RIGHT": msg = "🛡️ 안전합니다!"
            
            if not msg:
                if getattr(joystick, 'up', False) == True or (callable(getattr(joystick, 'up', None)) and joystick.up()):
                    msg = "🆘 도와주세요!"
                elif getattr(joystick, 'down', False) == True or (callable(getattr(joystick, 'down', None)) and joystick.down()):
                    msg = "👌 괜찮습니다!"
                elif getattr(joystick, 'left', False) == True or (callable(getattr(joystick, 'left', None)) and joystick.left()):
                    msg = "🤕 아파요!"
                elif getattr(joystick, 'right', False) == True or (callable(getattr(joystick, 'right', None)) and joystick.right()):
                    msg = "🛡️ 안전합니다!"
        except Exception as e:
            pass
            
        if msg and msg != last_msg:
            await sob.send(sender_token, f"🕹️ 환자 상태: {msg}")
            
        if not msg:
            last_msg = None
        else:
            last_msg = msg
            
        await asyncio.sleep(0.1)