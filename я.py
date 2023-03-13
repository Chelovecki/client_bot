import random
import time, asyncio

from pyrogram import Client, enums
import configparser

config = configparser.ConfigParser()
config.read('config.ini')

api_id = config['Telegram']['api_id']
api_hash = config['Telegram']['api_hash']
app = Client('based')


async def find_off_stuff() -> None:
    """
    Функция для нахождения официальных ботов и каналов,
     на которые подписан пользователь

     :exception AttributeError
                    Вызывается, когда мы продолжаем идти по чатам, но их больше нет
                    (если я написал в 100 чатов, то на 101 по счету выйдет ошибка).
                    При желании можно написать counter и посмотреть на каком вылетает ошибка
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
    """Функция для нахождения и логирования всех чатов, где ты писал хоть раз что-либо


    Работа:
        мы итерируемя по всем доступным диалогам 'async for dialog in app.get_dialogs():'.
        В зависимости от типа чата мы выбираем объект файла, в который мы будем логировать информацию.
        Далее, мы идем по всем сообщениям в данном чате с условием (from_user='me'), то есть, ищем мои сообщения.
        После первого найденного сообщения мы выходим из цикла поиска моих сообщений в данном чате  - 'break',
        и дальше итерируемся по чатам


    :var counter_calls (int) - показывает в сколько чатов ты писал


    :exception AttributeError
                    Вызывается, когда мы продолжаем идти по чатам, но их больше нет
                    (если я написал в 100 чатов, то на 101 по счету выйдет ошибка).
                    При желании можно написать counter и посмотреть на каком вылетает ошибка.
                    Когда ошибка произошла, мы понимаем, что чаты закончились, и выводим кол-во
                    того, что нас интересовало: чаты, где мы писали хоть 1 раз.
        """

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
                            # print(f'сообщение: {message.text}, время: {message.date}\n')
                            counter_chats += 1
                            break
            except AttributeError:
                print(f'было найдено {counter_chats} чатов, '
                      f'где Вы когда-либо оставляли сообщение')


async def del_all_old_guys():
    with (open('all_bots_dialogs.txt', 'w+', encoding='UTF-8') as all_bots,
          open('all_supergroups_dialogs.txt', 'w+', encoding='UTF-8') as all_supergroups,
          open('all_groups_dialogs.txt', 'w+', encoding='UTF-8') as all_groups,
          open('all_channels.txt', 'w+', encoding='UTF-8') as all_channels,
          open('all_private_dialogs.txt', 'w+', encoding='UTF-8') as all_self_chats):
        async with app:
            counter_private_cont = counter_private_ne_cont = counter_bots = 0
            counter_super = counter_groups = counter_channels =  0
            async for dialog in app.get_dialogs():
                if random.random(): time.sleep(0.5)
                match dialog.chat.type.name:
                    case 'BOT':
                        all_bots.write(f'бот {dialog.chat.first_name}  (@{dialog.chat.username})\n')
                        counter_bots += 1
                    case 'GROUP':
                        all_groups.write(f'бот {dialog.chat.first_name}  (@{dialog.chat.username})\n')
                        counter_groups += 1
                    case 'SUPERGROUP':
                        all_supergroups.write(f'бот {dialog.chat.first_name}  (@{dialog.chat.username})\n')
                        counter_super += 1
                    case 'CHANNEL':
                        all_channels.write(f'канал {dialog.chat.title}  (@{dialog.chat.username})\n')
                        counter_channels += 1
                    case 'PRIVATE':
                        if dialog.chat.id == app.me.id:
                            all_self_chats.write(f'это твой личный чат @{app.me.id}\n')
                            continue
                        async for message in app.get_chat_history(chat_id=dialog.chat.id, limit=50):
                            print(message)
                            if message.from_user.id != app.me.id:

                                if dialog.chat.username is None:
                                    all_self_chats.write('чат с удаленным пользователем\n')
                                    break

                                if message.from_user.is_contact:
                                    if dialog.chat.last_name:
                                        all_self_chats.write(f'диалог с контактом '
                                                             f'{dialog.chat.first_name} {dialog.chat.last_name}  '
                                                             f'(@{dialog.chat.username})\n')
                                    else:
                                        all_self_chats.write(f'диалог с контактом {dialog.chat.first_name}  (@{dialog.chat.username})\n')
                                    counter_private_cont += 1

                                else:
                                    if dialog.chat.last_name:
                                        all_self_chats.write(f'диалог не с контактом '
                                                             f'{dialog.chat.first_name} {dialog.chat.last_name}  '
                                                             f'(@{dialog.chat.username})\n')
                                    else:
                                        all_self_chats.write(f'диалог не с контактом {dialog.chat.first_name}  (@{dialog.chat.username})\n')
                                    counter_private_ne_cont += 1
                                break
            print(f'было найдено\n'
                  f'{counter_private_ne_cont + counter_private_cont} личных чатов, из которых '
                  f'{counter_private_ne_cont} не твои контакты, {counter_private_cont} твои контакты\n'
                  f'{counter_bots} ботов\t {counter_channels} каналов\n'
                  f'{counter_groups} обычных беседок и {counter_super} больших беседок')


def main_menu():
    print(f'{"ГЛАВНОЕ МЕНЮ":^20}')
    for r, name in enumerate(['4. Получить списки с именами чатов из числа стандартных Telegram типов чатов (Контакты/Не контакты/Группы/Каналы/Боты)',
                              '5. Получить список всех официальных Telegram-каналов, на которые подписан аккаунт.',
                              '9. Получить список всех чатов, где хоть раз писал.']):
        print(f'{r + 1}: {name}')
    dict_funk = {1: del_all_old_guys,
                 2: find_off_stuff,
                 3: fing_all_chats_where_u_wrote}
    match int(input('что запустим? ')):
        case 1:
            start = time.time()  # P.S декоратор у меня не получилось сделать так как при
            # res = funk(*args, **kwargs) вызываетсся какой-то корутиноВый объект
            app.run(dict_funk[1]())
            print('все диалоги/каналы/боты/группы/супергруппы собраны в одноименных файлах')
        case 2:
            start = time.time()  # P.S декоратор у меня не получилось сделать так как при
            # res = funk(*args, **kwargs) вызываетсся какой-то корутиноВый объект
            app.run(dict_funk[2]())
            print('все официальные боты и каналы, на которые ты подписан, собраны в одноименных файлах')
        case 3:
            start = time.time()
            app.run(dict_funk[3]())
            print('ну вроде как сделали')

    print(f'время выполнения задачи:  {round(time.time() - start,1)} сек\n')
    app.run(main_menu())



app.run(main_menu())

