import telebot
import webbrowser
from telebot import types
import pickle
import pandas as pd
import numpy as np
import sklearn
from sklearn import tree
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import FunctionTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline

import warnings
warnings.filterwarnings("ignore")

bot = telebot.TeleBot('5996145958:AAHsnIT9iDGWDudDAecF0HNgZpD6RjN3-1g')

total_sq = 0.0
kitchen_sq = 0.0
admin_okrug = ''
subway = ''
rooms = 0
year = 0
wc_count = 1
floor = 0
class_real = ''
floor_max = 0

# sample_test = {
#     'total_meters':[58.2, 60.0],
#     'kitchen_meters':[21.0, 12.0],
#     'dist_to_subway, min':[15.0, 25.0],
#     'admin_okrug':['СВАО', 'СВАО'],
#     'subway':['Ботанический сад', 'ВДНХ'],
#     'is_skyscraper': ['False', 'False'],
#     'class_real':['комфорт', ''],
#     'way_to_subway':['пешком', 'пешком'],
#     'wc_type':['совмещенный', 'раздельный'],
#     'house_type':['Монолитный', 'кирпичный'],
#     'flat_type':['Новостройка', 'Вторичка'],
#     'rooms': [2, 2],
#     'year_of_construction':[2021, 1995],
#     'wc_count':[2, 1],
#     'district':['р-н Останкинский', 'р-н Алексеевский'],
#     'floor_type':['usual', 'usual']
# }

admin_okrugs = ['СЗАО', 'ЦАО', 'САО', 'СВАО', 'ВАО', 'ЮВАО', 'ЮАО', 'ЮЗАО', 'ЗАО', 'НАО (Новомосковский)']
house_classes = ['премиум', 'бизнес', 'комфорт', 'эконом', 'элитный']

def reset(message):
    reset_global_values()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_predict = types.KeyboardButton('Новая квартира')
    btn_website = types.KeyboardButton('Перейти на cian.ru')
    btn_help = types.KeyboardButton('О боте')
    markup.row(btn_predict, btn_website, btn_help)
    bot.send_message(message.chat.id, f'Можете начать заново или перейти на сайт с квартирами', parse_mode='html', reply_markup=markup)
    bot.register_next_step_handler(message, on_start)


def make_prediction():
    global total_sq, kitchen_sq, admin_okrug, subway, floor, floor_max, class_real, wc_count, rooms, year
    global model
    global column_transformer

    sample_test = {
        'total_meters': [total_sq],
        'kitchen_meters': [kitchen_sq],
        'dist_to_subway, min': [15.0],
        'admin_okrug': [admin_okrug if admin_okrug!= '' else 'СВАО'],
        'subway': [subway],
        'is_skyscraper': ['False' if floor_max < 60 else 'True'],
        'class_real': ['комфорт' if class_real == '' else class_real],
        'way_to_subway': ['пешком'],
        'wc_type': ['совмещенный'],
        'house_type': ['Монолитный'],
        'flat_type': ['Вторичка'],
        'rooms': [rooms if rooms != 0 else 2],
        'year_of_construction': [2021],
        'wc_count': [1 if wc_count == 0 else wc_count],
        'district': ['р-н Останкинский'],
        'floor_type': ['usual' if floor > 3 else 'ground']
    }

    sample_df = pd.DataFrame.from_dict(sample_test)
    sample_df_transformed = column_transformer.transform(sample_df)
    prediction = model.predict(sample_df_transformed)[0] * total_sq
    return (prediction + 5000000)

    #bot.reply_to(message, f'Ваша предсказанная стоимость квартиры: {round(prediction+5000000, 0)} рублей')
    #bot.register_next_step_handler(message, reset)
    #reset(message)

def log_transform(x):
    return np.log(x + 1)
with open("rf_reg.pkl", "rb") as f:
    model = pickle.load(f)
with open("column_transf.pkl", "rb") as f:
    column_transformer = pickle.load(f)

@bot.message_handler(commands=['start'])
def main(message):
    reset_global_values()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_predict = types.KeyboardButton('Новая квартира')
    btn_website = types.KeyboardButton('Перейти на cian.ru')
    btn_help = types.KeyboardButton('О боте')
    markup.row(btn_predict, btn_website, btn_help)
    bot.reply_to(message, f'<b>Привет, {message.from_user.first_name}!</b> Этот бот позволяет '
                          f'вам сделать предсказание стоимости квартиры в Москве на основе ваших параметров.',
                 parse_mode='html',
                 reply_markup=markup)

    bot.register_next_step_handler(message, on_start)

@bot.message_handler(commands=['site'])
def site(message):
    bot.send_message(message.chat.id,
                     'Переходим на сайт...',
                     parse_mode='html')
    webbrowser.open('https://cian.ru')
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_predict = types.KeyboardButton('Новая квартира')
    btn_website = types.KeyboardButton('Перейти на cian.ru')
    btn_help = types.KeyboardButton('О боте')
    markup.row(btn_predict, btn_website, btn_help)
    bot.register_next_step_handler(message, on_start)

@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(message.chat.id, 'Бот разработан в рамках учебного проекта на программе MLDS в Высшей школе экономики', parse_mode='html')
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_predict = types.KeyboardButton('Новая квартира')
    btn_website = types.KeyboardButton('Перейти на cian.ru')
    btn_help = types.KeyboardButton('О боте')
    markup.row(btn_predict, btn_website, btn_help)
    bot.register_next_step_handler(message, on_start)

def on_start(message):
    if message.text == 'Новая квартира':
        reset_global_values()
        request_additional_info(message)
    if message.text == 'Перейти на cian.ru':
        site(message)
    if message.text == 'О боте':
        help(message)

def reset_global_values():
    global total_sq, kitchen_sq, admin_okrug, subway, floor, floor_max, class_real, wc_count, rooms, year
    global is_started
    total_sq = 0.0
    kitchen_sq = 0.0
    admin_okrug = ''
    subway = ''
    rooms = 0
    year = 0
    wc_count = 1
    floor = 0
    class_real = ''
    floor_max = 0
    is_started = 0


def print_flat_info():
    print(total_sq, kitchen_sq, admin_okrug, subway, rooms, year, wc_count, floor, class_real, floor_max)


is_started = 0
def request_additional_info(message):
    global kitchen_sq, total_sq, admin_okrug, subway, rooms, year, wc_count, floor, floor_max, class_real
    global is_started

    buttons = []

    if (total_sq != 0.0) & (kitchen_sq != 0.0) & (admin_okrug != '') & (rooms != 0) & (subway != ''):
        buttons.append(types.KeyboardButton('Рассчитать'))
        is_started = 2
    if total_sq == 0.0:
        buttons.append(types.KeyboardButton('Общая площадь'))
    if kitchen_sq == 0.0:
        buttons.append(types.KeyboardButton('Площадь кухни'))
    if admin_okrug == '':
        buttons.append(types.KeyboardButton('Округ'))
    if rooms == 0:
        buttons.append(types.KeyboardButton('Комнат'))
    if subway == '':
        buttons.append(types.KeyboardButton('Метро'))
    if floor == 0:
        buttons.append(types.KeyboardButton('Этаж'))
    if floor_max == 0:
        buttons.append(types.KeyboardButton('Этажей в доме'))
    if wc_count == 1:
        buttons.append(types.KeyboardButton('Санузлов'))
    if class_real == '':
        buttons.append(types.KeyboardButton('Класс дома'))
    buttons.append(types.KeyboardButton('Начать сначала'))
    buttons.append(types.KeyboardButton(''))
    buttons.append(types.KeyboardButton(''))

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, input_field_placeholder='')
    markup.row(buttons[0], buttons[1], buttons[2])

    if not is_started:
        bot.send_message(message.chat.id, 'Задайте параметры квартиры', parse_mode='html', reply_markup=markup)
        is_started = 1
    elif is_started != 2:
        bot.send_message(message.chat.id, 'Продолжайте вводить параметры квартиры', parse_mode='html', reply_markup=markup)
    else:
        bot.send_message(message.chat.id, 'Продолжайте вводить параметры или получите расчет уже сейчас', parse_mode='html', reply_markup=markup)

    bot.register_next_step_handler(message, on_requesting)


def on_requesting(message):
    if message.text == 'Рассчитать':
        bot.send_message(message.chat.id, 'Готов ваш расчет!', parse_mode='html')
        prediction = round(make_prediction(), 0)


        markup = types.ReplyKeyboardMarkup()
        btn_restart = types.KeyboardButton('Начать сначала')
        markup.row(btn_restart)
        bot.send_message(message.chat.id, f'Оценка стоимости вашей квартиры: {prediction}', parse_mode='html', reply_markup=markup)
        bot.register_next_step_handler(message, reset)


    if message.text == 'Начать сначала':
        bot.reply_to(message, 'Начинаем сначала')
        bot.register_next_step_handler(message, reset)
        reset(message)
        #make_prediction(message)

    if message.text == 'Общая площадь':
        markup = types.ReplyKeyboardMarkup(input_field_placeholder='Общая площадь, в квм', resize_keyboard=True, one_time_keyboard=True)
        btn_back = types.KeyboardButton('Назад')
        markup.row(btn_back)
        bot.send_message(message.chat.id, 'Введите общую площадь квартиры', parse_mode='html', reply_markup=markup)
        bot.register_next_step_handler(message, set_total_sq)

    if message.text == 'Площадь кухни':
        markup = types.ReplyKeyboardMarkup(input_field_placeholder='Площадь кухни, в квм', resize_keyboard=True, one_time_keyboard=True)
        btn_back = types.KeyboardButton('Назад')
        markup.row(btn_back)
        bot.send_message(message.chat.id, 'Введите площадь кухни', parse_mode='html', reply_markup=markup)
        bot.register_next_step_handler(message, set_kitchen_sq)

    if message.text == 'Округ':
        global admin_okrugs
        markup = types.ReplyKeyboardMarkup(input_field_placeholder='', resize_keyboard=True, one_time_keyboard=True)
        btn_back = types.KeyboardButton('Назад')
        markup.row(btn_back, types.KeyboardButton(admin_okrugs[0]), types.KeyboardButton(admin_okrugs[1]),
                   types.KeyboardButton(admin_okrugs[2]), types.KeyboardButton(admin_okrugs[3]))
        markup.row(types.KeyboardButton(admin_okrugs[4]), types.KeyboardButton(admin_okrugs[5]),
                   types.KeyboardButton(admin_okrugs[6]),
                   types.KeyboardButton(admin_okrugs[7]), types.KeyboardButton(admin_okrugs[8]))
        markup.row(types.KeyboardButton(admin_okrugs[9]))
        bot.send_message(message.chat.id, 'Выберите адм. округ Москвы', parse_mode='html', reply_markup=markup)
        bot.register_next_step_handler(message, set_admin_okrug)

    if message.text == 'Метро':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        btn_back = types.KeyboardButton('Назад')
        markup.row(btn_back)
        bot.send_message(message.chat.id, 'Введите ближайшее метро / МЦК', parse_mode='html', reply_markup=markup)
        bot.register_next_step_handler(message, set_subway)

    if message.text == 'Комнат':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        btn_back = types.KeyboardButton('Назад')
        markup.row(btn_back)
        bot.send_message(message.chat.id, 'Введите кол-во комнат (кроме кухни)', parse_mode='html', reply_markup=markup)
        bot.register_next_step_handler(message, set_rooms)

    if message.text == 'Этаж':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        btn_back = types.KeyboardButton('Назад')
        markup.row(btn_back)
        bot.send_message(message.chat.id, 'Введите этаж квартиры', parse_mode='html', reply_markup=markup)
        bot.register_next_step_handler(message, set_floor)

    if message.text == 'Этажей в доме':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        btn_back = types.KeyboardButton('Назад')
        markup.row(btn_back)
        bot.send_message(message.chat.id, 'Введите кол-во этажей в доме', parse_mode='html', reply_markup=markup)
        bot.register_next_step_handler(message, set_floor_max)

    if message.text == 'Санузлов':
        markup = types.ReplyKeyboardMarkup()
        btn_back = types.KeyboardButton('Назад')
        markup.row(btn_back)
        bot.send_message(message.chat.id, 'Введите кол-во санузлов', parse_mode='html', reply_markup=markup)
        bot.register_next_step_handler(message, set_wc)

    if message.text == 'Класс дома':
        global house_classes
        markup = types.ReplyKeyboardMarkup()
        buttons = []
        btn_back = types.KeyboardButton('Назад')
        markup.row()
        for okr in house_classes:
            markup.add(types.KeyboardButton(okr))
        markup.add(btn_back)
        bot.send_message(message.chat.id, 'Выберите класс дома', parse_mode='html', reply_markup=markup)
        bot.register_next_step_handler(message, set_class)


def set_total_sq(message):
    global total_sq
    if message.text == 'Назад':
        bot.register_next_step_handler(message, request_additional_info)
        request_additional_info(message)
    else:
        try:
            total_sq = float(message.text.strip())
            bot.register_next_step_handler(message, request_additional_info)
            request_additional_info(message)
        except ValueError:
            bot.send_message(message.chat.id, 'Надо вводить число!')
            bot.register_next_step_handler(message, request_additional_info)
            request_additional_info(message)


def set_kitchen_sq(message):
    global kitchen_sq
    if message.text == 'Назад':
        bot.register_next_step_handler(message, request_additional_info)
        request_additional_info(message)
    else:
        try:
            kitchen_sq = float(message.text.strip())
            bot.register_next_step_handler(message, request_additional_info)
            request_additional_info(message)
        except ValueError:
            bot.send_message(message.chat.id, 'Надо вводить число!')
            bot.register_next_step_handler(message, request_additional_info)
            request_additional_info(message)


def set_admin_okrug(message):
    global admin_okrug
    global admin_okrugs
    if message.text == 'Назад':
        bot.register_next_step_handler(message, request_additional_info)
        request_additional_info(message)
    else:
        user_okrug = message.text
        if user_okrug in admin_okrugs:
            admin_okrug = user_okrug
            bot.register_next_step_handler(message, request_additional_info)
            request_additional_info(message)


def set_subway(message):
    global subway
    if message.text == 'Назад':
        bot.register_next_step_handler(message, request_additional_info)
        request_additional_info(message)
    else:
        subway = message.text
        bot.register_next_step_handler(message, request_additional_info)
        request_additional_info(message)


def set_rooms(message):
    global rooms
    if message.text == 'Назад':
        bot.register_next_step_handler(message, request_additional_info)
        request_additional_info(message)
    else:
        try:
            rooms = int(message.text.strip())
            bot.register_next_step_handler(message, request_additional_info)
            request_additional_info(message)
        except ValueError:
            bot.send_message(message.chat.id, 'Надо вводить число!')
            bot.register_next_step_handler(message, request_additional_info)
            request_additional_info(message)


def set_wc(message):
    global wc_count
    if message.text == 'Назад':
        bot.register_next_step_handler(message, request_additional_info)
        request_additional_info(message)
    else:
        try:
            wc_count = int(message.text.strip())
            bot.register_next_step_handler(message, request_additional_info)
            request_additional_info(message)
        except ValueError:
            bot.send_message(message.chat.id, 'Надо вводить число!')
            bot.register_next_step_handler(message, request_additional_info)
            request_additional_info(message)


def set_floor(message):
    global floor
    if message.text == 'Назад':
        bot.register_next_step_handler(message, request_additional_info)
        request_additional_info(message)
    else:
        try:
            floor = int(message.text.strip())
            bot.register_next_step_handler(message, request_additional_info)
            request_additional_info(message)
        except ValueError:
            bot.send_message(message.chat.id, 'Надо вводить число!')
            bot.register_next_step_handler(message, request_additional_info)
            request_additional_info(message)


def set_floor_max(message):
    global floor_max
    if message.text == 'Назад':
        bot.register_next_step_handler(message, request_additional_info)
        request_additional_info(message)
    else:
        try:
            floor_max = int(message.text.strip())
            bot.register_next_step_handler(message, request_additional_info)
            request_additional_info(message)
        except ValueError:
            bot.send_message(message.chat.id, 'Надо вводить число!')
            bot.register_next_step_handler(message, request_additional_info)
            request_additional_info(message)


def set_class(message):
    global house_classes
    global class_real
    if message.text == 'Назад':
        bot.register_next_step_handler(message, request_additional_info)
        request_additional_info(message)
    else:
        user_class = message.text
        if user_class in house_classes:
            class_real = user_class
            bot.register_next_step_handler(message, request_additional_info)
            request_additional_info(message)







@bot.message_handler()
def info(message):
    if message.text.lower() == 'привет':
        bot.send_message(message.chat.id, f'Hi, {message.from_user.first_name}!')
    else:
        bot.send_message(message.chat.id, f'Я вас не понимаю')




# with open("col_transf.pkl", "rb") as f:
#     column_transformer = pickle.load(f)

bot.polling(none_stop=True)
