import random, time, json, os

from pyrogram import Client, enums
import configparser

config = configparser.ConfigParser()
config.read('config.ini')
api_id = config['Telegram']['api_id']
api_hash = config['Telegram']['api_hash']
app = Client('me_session', api_id, api_hash)




def write_in_json(path, dictionary):
    with open(path, 'w', encoding='UTF-8') as file:
        json.dump(dictionary, file, ensure_ascii=False, indent=4)

def read_from_json(name_and_path):
    file = open(name_and_path, 'r', encoding='UTF-8')
    dictionary = json.load(file)
    file.close()
    return dictionary


async def update_data(abs_path_database):
    database_dict = {'BOT': [],
                     'GROUP': [],
                     'SUPERGROUP': [],
                     'CHANNEL': [],
                     'PRIVATE': {
                         'CONTACT': [],
                         'NOT CONTACT': [],
                         'DELETED': []
                     }}
    async with app:
        async for dialog in app.get_dialogs():
            print(dialog.chat.type.name)
            match dialog.chat.type.name:
                case 'BOT':
                    database_dict['BOT'].append(dialog.chat.id)
                case 'GROUP':
                    database_dict['GROUP'].append(dialog.chat.id)
                case 'SUPERGROUP':
                    database_dict['SUPERGROUP'].append(dialog.chat.id)
                case 'CHANNEL':
                    database_dict['CHANNEL'].append(dialog.chat.id)
                case 'PRIVATE':
                    if dialog.chat.id == 777000:
                        continue
                    if dialog.top_message.from_user.is_self:
                        continue

                    some_user = await app.get_users(dialog.chat.id)
                    if some_user.is_deleted:
                        database_dict['PRIVATE']['DELETED'].append(some_user.id)
                    elif some_user.is_contact:
                        database_dict['PRIVATE']['CONTACT'].append(some_user.id)
                    else:
                        database_dict['PRIVATE']['NOT CONTACT'].append(some_user.id)
            write_in_json(abs_path_database, database_dict)

async def official_bots_channels() -> None:
    """
    Функция для нахождения официальных ботов и каналов,
     на которые подписан пользователь

     :exception AttributeError
                    Вызывается, когда мы продолжаем идти по чатам, но их больше нет
                    (если я написал в 100 чатов, то на 101 по счету выйдет ошибка).
                    При желании можно написать counter и посмотреть на каком вылетает ошибка
     """
    with open('верифицированные каналы и боты.txt', 'w+', encoding='utf-8') as file:
        async with app:
            try:
                async for dialog in app.get_dialogs():
                    if dialog.chat.is_verified and dialog.chat.type.CHANNEL:
                        if dialog.chat.type.name == 'BOT':
                            file.write(f'бот {dialog.chat.first_name}, @{dialog.chat.username}\n')
                        elif dialog.chat.type.name != 'PRIVATE' and dialog.chat.type.name != 'BOT':
                            file.write(f'канал {dialog.chat.title} (@{dialog.chat.username})\n')

            except AttributeError:
                pass


async def once_wrote():
    """Функция для нахождения и логирования всех чатов, где ты писал хоть раз что-либо


    Работа:
        мы итерируемя по всем доступным диалогам 'async for dialog in app.get_dialogs():'.
        В зависимости от типа чата мы выбираем объект файла, в который мы будем логировать информацию.
        Далее, мы идем по всем сообщениям в данном чате с условием (from_user='me'), то есть, ищем мои сообщения.
        После первого найденного сообщения мы выходим из цикла поиска моих сообщений в данном чате  - 'break',
        и дальше итерируемся по чатам

    Из неприятного:
        Пока ищешь свое последнее сообщение, легко словить time.sleep() от тг на 6-30 сек
        ```[me_session] Waiting for 21 seconds before continuing (required by "messages.Search")```


    :var counter_calls (int) - показывает в сколько чатов ты писал


    :exception AttributeError
                    Вызывается, когда мы продолжаем идти по чатам, но их больше нет
                    (если я написал в 100 чатов, то на 101 по счету выйдет ошибка).
                    При желании можно написать counter и посмотреть на каком вылетает ошибка.
                    Когда ошибка произошла, мы понимаем, что чаты закончились, и выводим кол-во
                    того, что нас интересовало: чаты, где мы писали хоть 1 раз.
        """

    with (open('боты, супергруппы, группы.txt', 'w+', encoding='UTF-8') as except_private_file,
          open('личные диалоги.txt', 'w+', encoding='UTF-8') as private_file):
        async with app:
            counter_chats = 0
            async for dialog in app.get_dialogs():

                match dialog.chat.type.name:
                    case 'BOT':
                        print(f'это бот {dialog.chat.first_name}')
                        except_private_file.write(f'бот {dialog.chat.first_name}  (@{dialog.chat.username})\n')
                    case 'GROUP':
                        print(f'это группа {dialog.chat.first_name}')
                        except_private_file.write(f'группа {dialog.chat.first_name}  (@{dialog.chat.username})\n')
                    case 'SUPERGROUP':
                        print(f'это супергруппа {dialog.chat.title}')
                        except_private_file.write(f'супергруппа {dialog.chat.title}  (@{dialog.chat.username})\n')
                    case 'CHANNEL':
                        if dialog.chat.is_creator:
                            print(f'это канал {dialog.chat.title}')
                            except_private_file.write(f'канал {dialog.chat.title}  (@{dialog.chat.username})\n')
                    case 'PRIVATE':
                        async for message in app.search_messages(dialog.chat.id, from_user='me'):
                            print(f'сообщение: {message.text}, время: {message.date}')
                            private_file.write(f'чат {dialog.chat.first_name} {dialog.chat.last_name}  (@{dialog.chat.username})\n'
                                                f'текст: {message.text}, дата: {message.date}\n\n')
                            counter_chats += 1
                            break


async def get_all_chats():
    async with app:
        counter_private_cont = counter_private_ne_cont = counter_bots = 0
        counter_super = counter_groups = counter_channels = 0
        with open(f'все диалоги.txt', 'w+', encoding='UTF-8') as file:
            async for dialog in app.get_dialogs():
                match dialog.chat.type.name:
                    case 'CHANNEL':
                        counter_channels += 1
                        print(f'канал {dialog.chat.title} (@{dialog.chat.username}')
                        file.write(f'канал: {dialog.chat.title} (@{dialog.chat.username})\n')
                    case 'BOT':
                        counter_bots += 1
                        print(f'бот {dialog.chat.first_name} (@{dialog.chat.username}')
                        file.write(f'бот: {dialog.chat.first_name} (@{dialog.chat.username})\n')
                    case 'GROUP':
                        counter_groups += 1
                        print(f'{dialog.chat.first_name} (@{dialog.chat.username})\n')
                        file.write(f'беседа: {dialog.chat.first_name} (@{dialog.chat.username})\n')
                    case 'SUPERGROUP':
                        counter_super += 1
                        print(f'супербеседа: {dialog.chat.first_name} (@{dialog.chat.username}')
                        file.write(f'супербеседа: {dialog.chat.first_name} (@{dialog.chat.username})\n')
                    case 'PRIVATE':
                        # это у нас диалог с телеграмом
                        # (куда еще коды приходят для авторизации)
                        if dialog.chat.id == 777000:
                            continue
                        # это наш личный чат (Избранное, оно же Saved Messaged)
                        if dialog.top_message.from_user.is_self:
                            continue

                        some_user = await app.get_users(dialog.chat.id)
                        if some_user.is_contact:
                            counter_private_cont += 1
                            print(f'чат с не контактом {some_user.first_name} {some_user.last_name}  (@{some_user.username})\n')
                            file.write(
                                f'чат с контактом {some_user.first_name} {some_user.last_name}  (@{some_user.username})\n')
                        else:
                            counter_private_ne_cont += 1
                            print(f'чат с не контактом {some_user.first_name} {some_user.last_name}  (@{some_user.username})\n')
                            file.write(f'чат с не контактом {some_user.first_name} {some_user.last_name}  (@{some_user.username})\n')

            print(f'было найдено\n'
                  f'{counter_private_ne_cont + counter_private_cont} личных чатов, из которых '
                  f'{counter_private_ne_cont} не твои контакты, {counter_private_cont} твои контакты\n'
                  f'{counter_bots} ботов\t {counter_channels} каналов\n'
                  f'{counter_groups} обычных беседок и {counter_super} больших беседок')


async def get_number_from_noncontact(database):
    count = 0
    with open('телефонные номера не контактов.txt', 'w+', encoding='UTF-8') as file:
        async with app:
            async for dialog in app.get_dialogs():
                if dialog.chat.type.name == 'PRIVATE':
                    bro_as_object = await app.get_users(dialog.chat.id)
                    if bro_as_object.id == app.me.id:
                        continue

                    if not bro_as_object.is_contact:
                        if bro_as_object.phone_number:
                            bro_username = None
                            try:
                                bro_username = bro_as_object.username
                            except Exception:
                                pass
                            if bro_username:
                                file.write(f'@{bro_as_object.username}: +{bro_as_object.phone_number}\n')
                            else:
                                file.write(f'{bro_as_object.first_name}: +{bro_as_object.phone_number}\n')
                            count += 1
        print(f'успешно найдено {count} номера')


def main_menu():
    abs_path_database = os.path.abspath(os.path.join('данные json', 'yr_database.json'))
    abs_path_all_chats = os.path.abspath(os.path.join('все чаты и каналы'))
    print(f'{"ГЛАВНОЕ МЕНЮ":^20}')
    for r, name in enumerate(['Обновить все данные о чатах',

                              'Получить списки с именами'
                              'чатов из числа стандартных Telegram типов чатов (Контакты/Не контакты/Группы/Каналы/Боты)',

                              'Получить список всех официальных Telegram-каналов и ботов пользователя',

                              'Получить номера пользователей, которым ты писал, но они не являются твоими контактами',

                              'Получить список всех чатов, где хоть раз писал']):
        print(f'{r + 1}: {name}')
    dict_funk = {1: update_data,
                 2: get_all_chats,
                 3: official_bots_channels,
                 4: get_number_from_noncontact,
                 5: once_wrote}
    choise = int(input('что запустим? '))
    database_dict = read_from_json(abs_path_database)
    if not database_dict:
        if choise != 1:
            print('у нас нет информации о чатах. чтобы ее получить, пожалуйста, выберите 1-й пункт')
            app.run(main_menu())

    match choise:
        case 1:
            start = time.time()
            app.run(dict_funk[1](abs_path_database))
            print('данные обновлены')
        case 2:
            start = time.time()
            app.run(dict_funk[2]())
            print('вся информация собрана с файле файле "все диалоги.txt"')
        case 3:
            start = time.time()
            app.run(dict_funk[3]())
            print('вся информация собрана в фале "верифицированные каналы и боты.txt"')
        case 4:
            start = time.time()
            app.run(dict_funk[4](database_dict))
            print('вся информация собрана в фале "телефонные номера не контактов.txt"')
        case 5:
            start = time.time()
            app.run(dict_funk[5]())
            print('вся информация собрана в файлах:\t "телефонные "личные диалоги.txt" и "боты, супергруппы, группы.txt"')

    print(f'время выполнения задачи:  {round(time.time() - start, 1)} сек\n')
    app.run(main_menu())


app.run(main_menu())

