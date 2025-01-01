import asyncio
from discord import Client


class Bot(Client):
    def __init__(self, intents, owner):
        self.owner = int(owner)
        super().__init__(intents=intents)

    async def on_ready(self):
        print(f'Logged in as {self.user}')

    async def on_message(self, message):
        print(f'Message from {message.author}: {message.content}')
        async with message.channel.typing():
            await asyncio.sleep(20)
        await message.channel.send("Done!")

        print(message.author.id)
        print(self.owner)
        if self.owner == message.author.id:
            print("They are my owner")