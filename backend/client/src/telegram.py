import telebot
from dotenv import load_dotenv
import os


class Telegram:
    load_dotenv()
    API_TOKEN = os.getenv('API_TOKEN', '')
    bot = telebot.TeleBot(API_TOKEN)

    @classmethod
    def send_message(cls, chat_id, text):
        cls.bot.send_message(chat_id, text)

if __name__ == '__main__':
    Telegram.send_message(-5043458545, 'teste')