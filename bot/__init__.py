# -*- coding: utf-8 -*-

import os
import telebot
from telebot import types
from .data import districts as districts_data
import json
import datetime
import logging

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

log = logging.getLogger(__name__)

bot = telebot.TeleBot(os.environ.get('TELEGRAM_API_KEY'))
checking_dict = {}
schedule_dict = {}

schedule = json.loads(open(os.path.join(PROJECT_DIR, "..", "output", "all.json"), "r").read())


def get_district_and_place_by_id(pid):
    for d in districts_data:
        for p in d['places']:
            if p['id'] == pid:
                return p['name'], d['district']
    return None, None


def get_id_by_place_name(name):
    for d in districts_data:
        for p in d['places']:
            if p['name'] == name:
                return p['id']
    return None


def load_schedule_to_dict():
    for s in schedule:
        date = s["date"]
        pid = s["id"]
        place, district = get_district_and_place_by_id(pid)
        if place is None:
            continue
        schedule_dict.setdefault(date, {
            'district': set(),
            'places': set(),
            'schedule': {}
        })
        schedule_dict[date]['district'].add(district)
        schedule_dict[date]['places'].add(place)
        schedule_dict[date]['schedule'][pid] = s['schedule']

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, """Support commands:
    /check - Start checking
    """)

@bot.message_handler(commands=['check'])
def start_checking(message):
    chat_id = message.chat.id
    checking_dict[chat_id] = {}

    # if tmr is not in schedule_dict, load data
    date = datetime.date.today() + datetime.timedelta(days=1)
    date_str = date.strftime('%Y-%m-%d')
    if date_str not in schedule_dict:
        load_schedule_to_dict()

    today = datetime.date.today().strftime('%Y-%m-%d')
    districts_set = schedule_dict[today]['district']

    districts = [d['district'] for d in districts_data if d['district'] in districts_set]
    if not len(districts):
        log.info('Cannot found districts')
        bot.reply_to(message, "沒有數據")
        return

    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add(*districts)
    msg = bot.reply_to(message, '選擇地區', reply_markup=markup)
    bot.register_next_step_handler(msg, process_district)


def process_district(message):
    district = message.text
    print(district)
    # ask areas
    places_dict = next((d['places'] for d in districts_data if d['district'] == district), None)
    if places_dict is None:
        raise Exception()

    today = datetime.date.today().strftime('%Y-%m-%d')
    places_set = schedule_dict[today]['places']

    places = [p['name'] for p in places_dict if p['name'] in places_set]

    # handle no places
    if not len(places):
        log.error('Cannot found places')
        bot.reply_to(message, "沒有數據")
        return

    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    # print(places)
    markup.add(*places)
    msg = bot.reply_to(message, '選擇運動場', reply_markup=markup)
    bot.register_next_step_handler(msg, process_area)

def process_area(message):
    # save place
    place = message.text

    chat_id = message.chat.id
    checking_dict[chat_id]['place'] = place

    today = datetime.date.today().strftime('%Y-%m-%d')
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add(*["今日", "明天"])
    msg = bot.reply_to(message, '選擇時間', reply_markup=markup)
    bot.register_next_step_handler(msg, process_query)


def process_query(message):
    chat_id = message.chat.id
    place = checking_dict[chat_id]['place']
    pid = get_id_by_place_name(place)

    if pid is None:
        log.error('Cannot found place id')
        bot.reply_to(message, "沒有數據")
        return

    date_option = message.text
    # default is today
    date_str = datetime.date.today().strftime('%Y-%m-%d')

    if date_option == '明天':
        date = datetime.date.today() + datetime.timedelta(days=1)
        date_str = date.strftime('%Y-%m-%d')

    print(date_str)
    schedule = schedule_dict.get(date_str, {'schedule':{}})['schedule'].get(pid)

    if schedule is None:
        log.error('Cannot found schedule')
        bot.reply_to(message, "沒有數據")
        bot.register_next_step_handler(message, process_query)
        return

    result_text = ""
    for s in schedule:
        result_text += s['time'] + ' ' + s['status'] + '\n'

    bot.reply_to(message, result_text)
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add(*["今日", "明天", ""])
    bot.register_next_step_handler(message, process_query)
