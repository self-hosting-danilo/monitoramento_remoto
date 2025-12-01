import telebot
from dotenv import load_dotenv
import os

load_dotenv()

API_TOKEN = os.getenv('API_TOKEN', '')

bot = telebot.TeleBot(API_TOKEN)

def send_message(chat_id, text):
    bot.send_message(chat_id, text)


