import configparser
import json
import time

from pyrogram import Client

config = configparser.ConfigParser()
config.read('config.ini')
api_id = config['Telegram']['api_id']
api_hash = config['Telegram']['api_hash']
app = Client('me_session', api_id, api_hash)


def write_in_json(path: str, dictionary: dict) -> None:
    """Функция, записывающая словарь в .json файл"""
    with open(path, 'w', encoding='UTF-8') as file:
        json.dump(dictionary, file, ensure_ascii=False, indent=4)


def read_from_json(name_and_path: str) -> dict:
    """Функция, считывающая данные из .json формата

    Name: read_from_json

    :return dictionary: dict - данные из файла
    """
    file = open(name_and_path, 'r', encoding='UTF-8')
    dictionary = json.load(file)
    file.close()
    return dictionary


async def collect_data() -> None:
    """
    Функция, собирающая все id чата телеграмма по категориям

    Name: collect_data

    Work:
        Итерация по всем диалогам пользователя и в зависимости от типа (см. конструкцию match-case),
         происходит запись по ключам id диалога.
        Для чата 'PRIVATE' было решено поделить на типы личного диалога:
         с контактом, с не-контактом и с удаленным аккаунтом.
        Запись происходит в файл 'yr_database.json'

    Temps:
        database_dict:
            dict[str]: list[int]
            dict[str][str]: list[int]

        some_user: dict - объект который мы используем, чтобы получить данные о пользователя,
         общаясь к системе через id этого пользователя

    """
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
                    # если это диалог со служебным чатом телеграм
                    # (куда приходят уведомления), либо же твой личный чат
                    # (Избранные сообщения or Saved Messages)
                    if dialog.chat.id == 777000 or dialog.top_message.from_user.is_self:
                        continue

                    some_user = await app.get_users(dialog.chat.id)
                    if some_user.is_deleted:
                        database_dict['PRIVATE']['DELETED'].append(some_user.id)
                    elif some_user.is_contact:
                        database_dict['PRIVATE']['CONTACT'].append(some_user.id)
                    else:
                        database_dict['PRIVATE']['NOT CONTACT'].append(some_user.id)
    write_in_json('yr_database.json', database_dict)


async def official_bots_channels() -> None:
    """
    Функция для нахождения официальных ботов и каналов, на которые подписан пользователь

    Name: official_bots_channels

    Work:
        Итерируемся по всем диалогам пользователя, и сразу же проверяем,
        официальный он ли (is_verified).
        Далее, проверяем, канал ли это, или бот, и записываем в файл
     """
    with open('верифицированные каналы и боты.txt', 'w+', encoding='utf-8') as file:
        async with app:
            async for dialog in app.get_dialogs():
                if dialog.chat.is_verified:
                    if dialog.chat.type.name == 'BOT':
                        file.write(f'бот {dialog.chat.first_name}, @{dialog.chat.username}\n')
                    elif dialog.chat.type.name == 'CHANNEL':
                        file.write(f'канал {dialog.chat.title} (@{dialog.chat.username})\n')


async def once_wrote() -> None:
    """
    Функция для нахождения и логирования всех чатов, где ты писал хоть раз что-либо

    Name: once_wrote

    Work:
        Итерируемся по всем доступным диалогам. В зависимости от типа чата мы выбираем объект файла,
         в который мы будем логировать информацию.
        Далее, идем по всем сообщениям от пользователя (тот, кт запускает скрипт) - from_user="me".
        После первого найденного сообщения выходим из цикла поиска сообщений пользователя в данном чате
         - 'break', и дальше итерируемся по чатам

    Problems:
        Во время поиска последнего сообщения, легко поймать time.sleep() от телеграмма на 6-30 сек
        ```[me_session] Waiting for 21 seconds before continuing (required by "messages.Search")```


    Temp: counter_calls: int - показывает в сколько чатов ты писал
    """

    with (open('боты, супер-группа, группы.txt', 'w+', encoding='UTF-8') as except_private_file,
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
                        print(f'это супер-группа {dialog.chat.title}')
                        except_private_file.write(f'супер-группа {dialog.chat.title}  (@{dialog.chat.username})\n')
                    case 'CHANNEL':
                        if dialog.chat.is_creator:
                            print(f'это канал {dialog.chat.title}')
                            except_private_file.write(f'канал {dialog.chat.title}  (@{dialog.chat.username})\n')
                    case 'PRIVATE':
                        async for message in app.search_messages(dialog.chat.id, from_user='me'):
                            print(f'сообщение: {message.text}, время: {message.date}')
                            private_file.write(
                                f'чат {dialog.chat.first_name} {dialog.chat.last_name}  (@{dialog.chat.username})\n'
                                f'текст: {message.text}, дата: {message.date}\n\n')
                            counter_chats += 1
                            break


async def get_all_chats() -> None:
    """
    Функция для получения и обработки всех чатов и каналов, которые имеет пользователь

    Name: get_all_chats

    Work:
        Библиотека итерируется по всем диалогам пользователя и в зависимости от типа (см. конструкцию match-case)
        Потом, в зависимости от типа, записывается по ключам id диалога.
        Для чата 'PRIVATE' было решено поделить на типы личного диалога:
         с контактом, с не-контактом и с удаленным аккаунтом.
        Запись всей информации в файл 'все диалоги.txt'

    Temps:
        counter_private_cont: int - счетчик чатов с контактами
        counter_private_ne_cont: int - счетчик чатов с не контактами
        counter_bots: int - счетчик ботов
        counter_super: int - счетчик супер-групп
        counter_groups: int - счетчик групп
        counter_channels: int - счетчик каналов
    """
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
                        print(f'супер-группа: {dialog.chat.first_name} (@{dialog.chat.username}')
                        file.write(f'супер-группа: {dialog.chat.first_name} (@{dialog.chat.username})\n')
                    case 'PRIVATE':
                        # если это диалог со служебным чатом телеграм
                        # (куда приходят уведомления), либо же твой личный чат
                        # (Избранные сообщения or Saved Messages)
                        if dialog.chat.id == 777000 or dialog.top_message.from_user.is_self:
                            continue

                        some_user = await app.get_users(dialog.chat.id)
                        if some_user.is_contact:
                            counter_private_cont += 1
                            print(
                                f'чат с не контактом {some_user.first_name} {some_user.last_name}  '
                                f'(@{some_user.username})\n')
                            file.write(
                                f'чат с контактом {some_user.first_name} {some_user.last_name}  '
                                f'(@{some_user.username})\n')
                        else:
                            counter_private_ne_cont += 1
                            print(
                                f'чат с не контактом {some_user.first_name} {some_user.last_name}  '
                                f'(@{some_user.username})\n')
                            file.write(
                                f'чат с не контактом {some_user.first_name} {some_user.last_name}  '
                                f'(@{some_user.username})\n')

            print(f'было найдено\n'
                  f'{counter_private_ne_cont + counter_private_cont} личных чатов, из которых '
                  f'{counter_private_ne_cont} не твои контакты, {counter_private_cont} твои контакты\n'
                  f'{counter_bots} ботов\t {counter_channels} каналов\n'
                  f'{counter_groups} обычных беседок и {counter_super} больших беседок')


async def get_number_from_not_contact() -> None:
    """
    Функция для получения номера телефона тех чатов, с которыми общался пользователь, но не добавил в контакты

    Name: get_number_from_not_contact

    Work:
        Итерируемся по диалогам. Сначала ищем приватные чаты ('PRIVATE'), далее обращаемся к пользователю,
         как к объекту, чтобы узнать, является ли он контактом пользователя, или нет.
        Если нет - берем его username, номер телефона, и записываем
         в файл 'телефонные номера не контакты.txt'

    Temp: count: int - счетчик собранных номеров

    :exception BaseException:
        Не у всех доступен username. Чтобы не обращаться к ключу, которого нет, было решено
         применить конструкцию try-except для предотвращения ошибки
    """
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
                            except BaseException:
                                pass
                            if bro_username:
                                file.write(f'@{bro_as_object.username}: +{bro_as_object.phone_number}\n')
                            else:
                                file.write(f'{bro_as_object.first_name}: +{bro_as_object.phone_number}\n')
                            count += 1
        print(f'успешно найдено {count} номера')


def main_menu() -> None:
    """
    Функция для выбора действий в программе

    Name: main_menu

    Temp:
        dict_funk: dict[int]: Iterable - содержит ссылки на функции для вызова при обращении по ключу
        start: time - нужна для вычисления времени выполнения определенной функции

    """
    print(f'{"ГЛАВНОЕ МЕНЮ":^20}')
    for r, name in enumerate([
        'Получить все данные об чатах (их id). '
        'Результат работы по сути нигде не используется. '
        'Но ради интереса (для себя) можно и собрать.',

        'Получить списки с именами'
        'чатов из числа стандартных Telegram типов чатов '
        '(Контакты/Не контакты/Группы/Каналы/Боты)',

        'Получить список всех официальных Telegram-каналов и ботов пользователя',

        'Получить номера пользователей, которым ты писал, но они не являются твоими контактами',

        'Получить список всех чатов, где хоть раз писал'
    ]):
        print(f'{r + 1}: {name}')
    dict_funk = {1: collect_data,
                 2: get_all_chats,
                 3: official_bots_channels,
                 4: get_number_from_not_contact,
                 5: once_wrote}
    chose = int(input('что запустим? '))

    start = time.time()
    match chose:
        case 1:
            app.run(dict_funk[1]())
            print('данные собраны и находятся в файле "yr_database.json"')
        case 2:
            app.run(dict_funk[2]())
            print('вся информация собрана с файле файле "все диалоги.txt"')
        case 3:
            app.run(dict_funk[3]())
            print('вся информация собрана в фале "верифицированные каналы и боты.txt"')
        case 4:
            app.run(dict_funk[4]())
            print('вся информация собрана в фале "телефонные номера не контактов.txt"')
        case 5:
            start = time.time()
            app.run(dict_funk[5]())
            print(
                'вся информация собрана в файлах:\t "телефонные "личные диалоги.txt" и "боты, супергруппы, группы.txt"')

    print(f'время выполнения задачи:  {round(time.time() - start, 1)} сек\n')
    app.run(main_menu())


app.run(main_menu())
