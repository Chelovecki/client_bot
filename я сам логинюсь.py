from pyrogram import Client
import configparser

from collections.abc import Iterable
config = configparser.ConfigParser()
config.read('config.ini')

api_id = config['Telegram']['api_id']
api_hash = config['Telegram']['api_hash']
app = Client('my_account', api_id, api_hash)


async def main() -> None:
    """
    Основная функция для нахождения официальных ботов и каналов,
     на которые подписан пользователь"""
    with(open('official_channels.txt', 'w+', encoding='utf-8') as channels,
         open('official_bots.txt', 'w+', encoding='utf-8') as bots):
        async with app:
            try:
                async for dialog in app.get_dialogs():
                    if dialog.chat.is_verified and dialog.chat.type.CHANNEL:
                        if dialog.chat.type.name == 'BOT':
                            bots.write(f'name = {dialog.chat.first_name}, @{dialog.chat.username}\n')
                        elif dialog.chat.type.name != 'PRIVATE' and dialog.chat.type.name != 'BOT':
                            channels.write(f'name = {dialog.chat.title} (@{dialog.chat.username})\n')

            except AttributeError:
                pass

app.run(main())
print('программа завершила работу')

