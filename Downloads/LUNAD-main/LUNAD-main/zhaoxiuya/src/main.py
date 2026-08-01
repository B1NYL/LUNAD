import asyncio
import os
import dotenv
import sob
import modi_plus as modi
from logger import printf
from gigi import arm_ctrl, check_fall, joystick_ctrl, listen

lunad_lang = "중국어"

async def main():
    dotenv.load_dotenv()
    # printf(f"{modi.Speaker.preset_musics()}")
    
    sender_token = os.environ.get("ABHAN_TOKEN") or os.environ.get("SENDER_BOT_TOKEN")
    receiver_token = os.environ.get("SOLAD_TOKEN") or os.environ.get("RECEIVER_BOT_TOKEN")
    printf(os.environ.get("OPENAI_API_KEY"))
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
