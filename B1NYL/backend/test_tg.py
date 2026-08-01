import asyncio
import os
from telegram import Bot
import dotenv
dotenv.load_dotenv()
token = os.getenv("LUNAD_TOKEN")
chat_id = os.getenv("GROUP_CHAT_ID")
async def main():
    bot = Bot(token)
    async with bot:
        await bot.send_message(chat_id=chat_id, text="test message")
asyncio.run(main())
