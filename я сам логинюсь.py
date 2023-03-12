import time

from pyrogram import Client
import configparser

star_sis = time.time()
config = configparser.ConfigParser()
config.read('config.ini')

api_id = config['Telegram']['api_id']
api_hash = config['Telegram']['api_hash']
app = Client('my_account', api_id, api_hash)


async def find_off_stuff() -> None:
    """
    Функция для нахождения официальных ботов и каналов,
     на которые подписан пользователь

     :exception AttributeError
     """
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


async def fing_all_chats_where_u_wrote():
    with (open('dialog_with_bot.txt', 'w+', encoding='UTF-8') as bot_file,
          open('dialog_in_supergroups.txt', 'w+', encoding='UTF-8') as super_group_file,
          open('dialog_in_groups.txt', 'w+', encoding='UTF-8') as group_file):
        async with app:
            counter_chats = 0
            try:
                async for dialog in app.get_dialogs():
                    file_to_write = None
                    match dialog.chat.type.name:
                        case 'BOT':
                            print(f'это бот {dialog.chat.title}')
                            file_to_write = bot_file
                        case 'GROUP':
                            print(f'это группа {dialog.chat.title}')
                            file_to_write = group_file
                        case 'SUPERGROUP':
                            print(f'это супергруппа {dialog.chat.title}')
                            file_to_write = super_group_file
                        case 'CHANNEL':
                            print(f'это канал {dialog.chat.title}')

                    if file_to_write:
                        async for message in app.search_messages(dialog.chat.id, from_user='me'):
                            file_to_write.write(f'чат {dialog.chat.title}  (@{dialog.chat.username})\n'
                                                f'текст: {message.text}, дата: {message.date}\n\n')
                            #print(f'сообщение: {message.text}, время: {message.date}\n')
                            counter_chats += 1
                            break
            except AttributeError:
                print(f'было найдено {counter_chats} чатов, '
                      f'где Вы когда-либо оставляли сообщение')



for r, name in enumerate(['5. Получить список всех официальных Telegram-каналов, на которые подписан аккаунт.',
                          '9. Получить список всех чатов, где хоть раз писал.']):
    print(f'{r + 1}: {name}')
dict_funk = {1: find_off_stuff,
             2: fing_all_chats_where_u_wrote}
print(f'программа инициализировалась за {round(time.time() - star_sis, 5)} сек')
match int(input('что запустим? ')):
    case 1:
        start = time.time()  # P.S декоратор у меня не получилось сделать так как при
        # res = funk(*args, **kwargs) вызываетсся какой-то корутиноВый объект
        app.run(dict_funk[1]())
        print('все официальные боты и каналы, на которые ты подписан, собраны в одноименных файлах')
    case 2:
        start = time.time()
        app.run(dict_funk[2]())
        print('ну вроде как сделали')
print(f'время выполнения задачи:  {time.time() - start} сек')
