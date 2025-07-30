from aiohttp import web
from plugins import web_server
import asyncio
import pyromod.listen
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from datetime import datetime
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from config import *

name = """ BY CODEFLIX BOTS """

# MongoDB Setup
db_client = AsyncIOMotorClient(MONGO_DB_URI)
db = db_client[DB_NAME]
users_collection = db["users"]

async def send_restart_message_to_all_users(bot):
    all_users = users_collection.find({})
    async for user in all_users:
        user_id = user.get("user_id")
        if not user_id:
            continue
        try:
            await bot.send_message(
                chat_id=user_id,
                text="<b><blockquote>🤖 Bᴏᴛ Rᴇsᴛᴀʀᴛᴇᴅ ʙʏ @RMxBots</blockquote></b>"
            )
            await asyncio.sleep(0.3)  # Flood control
        except Exception as e:
            print(f"❌ Failed to send message to {user_id}: {e}")

class Bot(Client):
    def __init__(self):
        super().__init__(
            name="Bot",
            api_hash=API_HASH,
            api_id=APP_ID,
            plugins={"root": "plugins"},
            workers=TG_BOT_WORKERS,
            bot_token=TG_BOT_TOKEN
        )
        self.LOGGER = LOGGER

    async def start(self):
        await super().start()
        usr_bot_me = await self.get_me()
        self.uptime = datetime.now()

        try:
            db_channel = await self.get_chat(CHANNEL_ID)
            self.db_channel = db_channel
            test = await self.send_message(chat_id=db_channel.id, text="Test Message")
            await test.delete()
        except Exception as e:
            self.LOGGER(__name__).warning(e)
            self.LOGGER(__name__).warning(f"Make sure bot is admin in DB Channel and check CHANNEL_ID value. Current: {CHANNEL_ID}")
            self.LOGGER(__name__).info("\nBot Stopped. Join https://t.me/CodeflixSupport for support")
            sys.exit()

        self.set_parse_mode(ParseMode.HTML)
        self.username = usr_bot_me.username
        self.LOGGER(__name__).info(f"Bot Running..! Made by @Codeflix_Bots")

        # Start Web Server
        app = web.AppRunner(await web_server())
        await app.setup()
        await web.TCPSite(app, "0.0.0.0", PORT).start()

        try:
            await self.send_message(OWNER_ID, text="<b><blockquote>🤖 Bᴏᴛ Rᴇsᴛᴀʀᴛᴇᴅ ʙʏ @RMxBots</blockquote></b>")
        except:
            pass

        # ✅ Send restart message to all users
        try:
            await send_restart_message_to_all_users(self)
        except Exception as err:
            print(f"⚠️ Error sending to all users: {err}")

    async def stop(self, *args):
        await super().stop()
        self.LOGGER(__name__).info("Bot stopped.")

    def run(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.start())
        self.LOGGER(__name__).info("Bot is now running. Thanks to @rohit_1888")
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            self.LOGGER(__name__).info("Shutting down...")
        finally:
            loop.run_until_complete(self.stop())

# Add /start handler to collect users
@Client.on_message(filters.private & filters.command("start"))
async def start_handler(client, message):
    user_id = message.from_user.id
    if not await users_collection.find_one({"user_id": user_id}):
        await users_collection.insert_one({"user_id": user_id})
    await message.reply_text(
        "👋 Welcome! I'm active and running.\n\n🔁 You'll be notified when restarted.",
        quote=True
    )

# Run bot
if __name__ == "__main__":
    Bot().run()
