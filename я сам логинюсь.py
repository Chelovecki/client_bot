import time, json, configparser, datetime
from datetime import timedelta

from pyrogram import Client

config = configparser.ConfigParser()
config.read('config.ini')
api_id = config['Telegram']['api_id']
api_hash = config['Telegram']['api_hash']
app = Client('me_session', api_id, api_hash)

a = time.time()


def write_in_json(path, dictionary):
    with open(path, 'w', encoding='UTF-8') as file:
        json.dump(dictionary, file, ensure_ascii=False, indent=4)


def read_from_json(name_and_path):
    file = open(name_and_path, 'r', encoding='UTF-8')
    dictionary = json.load(file)
    file.close()
    return dictionary


async def collect_data():
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
    write_in_json('yr_database.json', database_dict)


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
    search_limit = datetime.datetime.now() - timedelta(days=30)  # возьмем дефолтный 30-дневный месяц
    logging = dict()
    if int(input(
            'по умолчанию будет осуществлен поиск по сообщениям за последний месяц. вы хотите указать свою дату, вплоть до которой будет осуществлен поиск?(1-да, 0-нет):  ')):
        y, m, d = map(int, input('введи дату в формате yyyy-mm-dd:  ').split('-'))
        # я подумал, что проще будет сделать проверку на корректность ввода так,
        # чем делать проверку диапазоном для каждого из 3-х инстансов
        search_limit = datetime.date(y, m, d)
    with open('чаты, где ты хоть раз писал.txt', 'w+', encoding='UTF-8') as file:
        async with app:
            counter_chats = 0
            async for dialog in app.get_dialogs():
                async for message in app.search_messages(dialog.chat.id, from_user="me"):
                    if message.date >= search_limit:
                        if not message.service:
                            match dialog.chat.type.name:
                                case 'BOT':
                                    file.write(
                                        f'бот {dialog.chat.first_name} (@{dialog.chat.username})\t'
                                        f'сообщение: {message.text}; в {message.date}\n')
                                case 'GROUP':
                                    file.write(
                                        f'группа {dialog.chat.first_name} (@{dialog.chat.username})\t'
                                        f'сообщение: {message.text}; в {message.date}\n')
                                case 'SUPERGROUP':
                                    file.write(
                                        f'супергруппа {dialog.chat.title} (@{dialog.chat.username})\t'
                                        f'сообщение: {message.text}; в {message.date}\n')
                                case 'CHANNEL':
                                    if dialog.chat.is_creator:
                                        file.write(
                                            f'канал {dialog.chat.title} (@{dialog.chat.username})\t'
                                            f'сообщение: {message.text}; в {message.date}\n')
                                case 'PRIVATE':
                                    file.write(
                                        f'чат {dialog.chat.first_name} {dialog.chat.last_name}  (@{dialog.chat.username})\t'
                                        f'сообщение: {message.text}; в {message.date}\n')
                                    counter_chats += 1
                            logging[dialog.chat.id] = message.id
                            break
                    else:
                        break
    write_in_json('чаты, где ты хоть раз писал.json', logging)

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
                            print(
                                f'чат с не контактом {some_user.first_name} {some_user.last_name}  (@{some_user.username})\n')
                            file.write(
                                f'чат с контактом {some_user.first_name} {some_user.last_name}  (@{some_user.username})\n')
                        else:
                            counter_private_ne_cont += 1
                            print(
                                f'чат с не контактом {some_user.first_name} {some_user.last_name}  (@{some_user.username})\n')
                            file.write(
                                f'чат с не контактом {some_user.first_name} {some_user.last_name}  (@{some_user.username})\n')

            print(f'было найдено\n'
                  f'{counter_private_ne_cont + counter_private_cont} личных чатов, из которых '
                  f'{counter_private_ne_cont} не твои контакты, {counter_private_cont} твои контакты\n'
                  f'{counter_bots} ботов\t {counter_channels} каналов\n'
                  f'{counter_groups} обычных беседок и {counter_super} больших беседок')


async def get_number_from_noncontact():
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
    print(f'{"ГЛАВНОЕ МЕНЮ":^20}')
    for r, name in enumerate([
        'Получить все данные об чатах (их id). результат работы по сути нигде не используется. Но ради интереса (для себя) можно и собрать.',
        'Получить списки с именами'
        'чатов из числа стандартных Telegram типов чатов (Контакты/Не контакты/Группы/Каналы/Боты)',
        'Получить список всех официальных Telegram-каналов и ботов пользователя',
        'Получить номера пользователей, которым ты писал, но они не являются твоими контактами',
        'Получить список всех чатов, где хоть раз писал']):
        print(f'{r + 1}: {name}')
    dict_funk = {1: collect_data,
                 2: get_all_chats,
                 3: official_bots_channels,
                 4: get_number_from_noncontact,
                 5: once_wrote}
    chose = int(input('что запустим? '))

    start = time.time()
    match chose:
        case 1:
            app.run(dict_funk[1]())
            print('данные собраны и находсят в файле "yr_database.json"')
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
                'вся информация собрана в файлах:\t "чаты, где ты хоть раз писал.txt"')

    print(f'время выполнения задачи:  {round(time.time() - start, 1)} сек\n')
    app.run(main_menu())


app.run(once_wrote())
print(f'время = {time.time() - a}')
