import asyncio
import os
import dotenv
from sob import listen
from gigi import arm_ctrl, check_fall, joystick_ctrl

async def main():
    dotenv.load_dotenv()
    
    sender_token = os.environ.get("LUNAD_TOKEN") or os.environ.get("SENDER_BOT_TOKEN")
    receiver_token = os.environ.get("SOLAD_TOKEN") or os.environ.get("RECEIVER_BOT_TOKEN")
    
    if not sender_token or not receiver_token:
        print("경고: .env 파일에 LUNAD_TOKEN 또는 SOLAD_TOKEN이 설정되지 않았습니다.")
        print("테스트를 위해 발신용/수신용 봇 토큰을 설정해주세요.")
        return
        
    print("텔레그램 통합 MODI 제어 시스템을 시작합니다...")
    
    # 병렬로 실행할 태스크들
    await asyncio.gather(
        # listen(receiver_token),
        arm_ctrl(sender_token),
        check_fall(sender_token),
        joystick_ctrl(sender_token)
    )

if __name__ == "__main__":
    asyncio.run(main())
