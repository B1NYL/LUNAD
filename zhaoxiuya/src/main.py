import asyncio
import os
import dotenv
import sob
from logger import printf
from gigi import arm_ctrl, check_fall, joystick_ctrl, listen

lunad_lang = "베트남어"

async def main():
    dotenv.load_dotenv()
    
    sender_token = os.environ.get("LUNAD_TOKEN") or os.environ.get("SENDER_BOT_TOKEN")
    receiver_token = os.environ.get("SOLAD_TOKEN") or os.environ.get("RECEIVER_BOT_TOKEN")
    print(os.environ.get("OPENAI_API_KEY"))
    if not sender_token or not receiver_token:
        printf("봇 토큰이 설정되지 않음.")
        return
    
    await sob.init_bot(sender_token)
            
    await asyncio.gather(
        listen(sender_token, codomain_lang=lunad_lang),
        arm_ctrl(sender_token, my_lang=lunad_lang),
        check_fall(sender_token),
        joystick_ctrl(sender_token)
    )

if __name__ == "__main__":
    asyncio.run(main())
