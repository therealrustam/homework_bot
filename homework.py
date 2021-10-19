"""Телеграм бот-ассистент. Итоговый проект."""

import logging
import sys
import os
import time

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s',
                    handlers=[logging.StreamHandler(sys.stdout), ])

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
headers = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
counter = {0: 0}
old_status = {0: ''}
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
    logging.info('Бот отправил сообщение')


def get_api_answer(url, current_timestamp):
    """Метод отправки запроса к API."""
    payload = {'from_date': current_timestamp}
    response = requests.get(
        ENDPOINT, headers=headers, params=payload)
    if response.status_code != 200:
        logging.error(
            'Сбой в работе программы: Эндпоинт'
            ' https://practicum.yandex.ru/api/user_api/homework_statuses/111'
            f' недоступен. Код ответа API: {response.status_code}')
        raise requests.HTTPError('Код состояния HTTP не равен 200')
    response = response.json()
    return response


def parse_status(homework):
    """Метод анализа статуса и подготовки сообщения."""
    verdict = homework.get('status')
    verdict = HOMEWORK_STATUSES[verdict]
    homework_name = homework.get('homework_name')
    logging.info(
        f'Изменился статус проверки работы "{homework_name}". {verdict}')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_response(response):
    """Метод проверки полученного ответа на корректность и проверка статуса."""
    if response['homeworks'] == []:
        logging.error('Нет данных')
        raise Exception('Нет данных')
    if response['homeworks'][0].get('status') not in ['approved',
                                                      'reviewing',
                                                      'rejected', ]:
        logging.error('Неизвестный статус')
        raise Exception('Неизвестный статус')
    print(response)
    if counter[0] == 0:
        old_status[0] = response['homeworks'][0].get('status')
        counter[0] = 1
        return old_status[0]
    if counter[0] == 1:
        status = response['homeworks'][0].get('status')
        if status == old_status[0]:
            return False
        else:
            return status


def main():
    """Метод выполнения основного кода."""
    if (PRACTICUM_TOKEN == '') or (TELEGRAM_TOKEN == '') or (CHAT_ID == 0):
        logging.critical('Отсутствуют обязательные переменные окружения')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    current_timestamp = current_timestamp - RETRY_TIME
    while True:
        try:
            response = get_api_answer(ENDPOINT, current_timestamp)
            if check_response(response):
                homework = response['homeworks'][0]
                message = parse_status(homework)
                send_message(bot, message)
            time.sleep(RETRY_TIME)
            current_timestamp = int(time.time())
            current_timestamp = current_timestamp - RETRY_TIME
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(
                f'Сбой в работе программы: {error}')
            send_message(bot, message)
            time.sleep(RETRY_TIME)
            current_timestamp = int(time.time())
            current_timestamp = current_timestamp - RETRY_TIME
            continue


if __name__ == '__main__':
    main()
