"""Телеграм бот-ассистент. Итоговый проект."""

import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
headers = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена, в ней нашлись ошибки.'
}


def send_message(bot, message):
    """Метод отправки сообщении ботом."""
    bot.send_message(chat_id=CHAT_ID, text=message)
    logging.info('Сообщение отправлено')


def get_api_answer(url, current_timestamp):
    """Метод отправки запроса к API."""
    payload = {'from_date': current_timestamp}
    response = requests.get(
        ENDPOINT, headers=headers, params=payload)
    if response.status_code != 200:
        logging.error(
            f'Код состояния HTTP не равен 200: {response.status_code}')
        raise requests.HTTPError('Код состояния HTTP не равен 200')
    response = response.json()
    return response


def parse_status(homework):
    """Метод анализа статуса и подготовки сообщения."""
    verdict = homework[0].get('status')
    verdict = HOMEWORK_STATUSES[verdict]
    homework_name = homework[0].get('homework_name')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_response(response):
    """Метод проверки полученного ответа на корректность и проверка статуса."""
    print(response)
    homework = response['homeworks']
    return homework


def main():
    """Метод выполнения основного кода."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    current_timestamp = current_timestamp - 2592000
    while True:
        try:
            response = get_api_answer(ENDPOINT, current_timestamp)
            homework = check_response(response)
            message = parse_status(homework)
            time.sleep(RETRY_TIME)
            send_message(bot, message)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(
                f'Сбой в работе программы: {error}')
            send_message(bot, message)
            time.sleep(RETRY_TIME)
            continue


if __name__ == '__main__':
    main()
