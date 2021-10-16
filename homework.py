import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
headers = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


RETRY_TIME = 300
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена, в ней нашлись ошибки.'
}


def send_message(bot, message):
    bot.send_message(chat_id=CHAT_ID, text=message)


def get_api_answer(url, current_timestamp):
    payload = {'from_date': current_timestamp}
    response = requests.get(
        ENDPOINT, headers=headers, params=payload)
    if response.status_code != 200:
        logging.error(
            f'<The answer is not 200>: {response.status_code}')
        raise requests.HTTPError('<The answer is not 200>')
    response = response.json()
    return response


def parse_status(homework):
    verdict = homework[0]['status']
    verdict = HOMEWORK_STATUSES[verdict]
    homework_name = homework.get('homework_name')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_response(response):
    homeworks = response.get('homeworks')
    parse_status(homeworks)


def main():
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    current_timestamp = current_timestamp - 2592000
    while True:
        try:
            response = get_api_answer(ENDPOINT, current_timestamp)
            check_response(response)
            time.sleep(RETRY_TIME)
            send_message(bot, message)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            time.sleep(RETRY_TIME)
            continue


if __name__ == '__main__':
    main()
