import os
from discord import Intents
from lajter.client import Bot
from dotenv import load_dotenv





load_dotenv()
bot_key = os.getenv("BOT_KEY")
owner_id = os.getenv("OWNER_ID")

intents = Intents.default()
intents.message_content = True

client = Bot(intents, owner_id)
client.run(bot_key)
