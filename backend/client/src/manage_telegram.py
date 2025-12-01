import os
import sys
import django
from pathlib import Path

# Caminho absoluto da raiz do projeto
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "monitoramento.settings")
django.setup()

from dashboard.models import ChatTelegram, Hospital

def get_chat_id(nome):
    try:
        hospital = Hospital.objects.get(nome=nome)
    except Hospital.DoesNotExist:
        print(f'Hospital "{nome}" não encontrado.')
        return
    
    chats = ChatTelegram.objects.filter(hospital=hospital)

    if chats:
        for chat in chats:
            print(f"Chat Telegram: {chat.chat_id}")
    else:
        print("Nenhum registro encontrado para este hospital.")

if __name__ == '__main__':
    get_chat_id('Hospital da Crianca')
