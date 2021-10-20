"""Телеграм бот-ассистент. Итоговый проект."""

import logging
import sys
import os
import time

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s',
                    handlers=[logging.StreamHandler(sys.stdout), ])
logger = logging.getLogger(__name__)

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
    logger.info('Бот отправил сообщение')


def get_api_answer(url, current_timestamp):
    """Метод отправки запроса к API."""
    payload = {'from_date': current_timestamp}
    response = requests.get(
        ENDPOINT, headers=headers, params=payload)
    if response.status_code != 200:
        logger.error(
            'Сбой в работе программы: Эндпоинт'
            ' https://practicum.yandex.ru/api/user_api/homework_statuses/111'
            f' недоступен. Код ответа API: {response.status_code}')
        # вызов исключения для отправки ботом сообщения в телеграм
        raise Exception('Код состояния HTTP не равен 200')
    response = response.json()
    return response


def parse_status(homework):
    """Метод анализа статуса и подготовки сообщения."""
    status = homework.get('status')
    verdict = HOMEWORK_STATUSES[status]
    if not homework.get('homework_name'):
        logger.error('Нет названия домашней работы')
        # вызов исключения для отправки ботом сообщения в телеграм
        raise Exception('Нет названия домашней работы')
    homework_name = homework.get('homework_name')
    message = f'Изменился статус проверки работы "{homework_name}". {verdict}'
    logger.info(message)
    return message


def check_response(response):
    """Метод проверки полученного ответа на корректность и проверка статуса."""
    logger.debug(response)
    if not response['homeworks']:
        logger.error('Нет данных')
        # вызов исключения для отправки ботом сообщения в телеграм
        raise Exception('Нет данных')
    status = response['homeworks'][0].get('status')
    if status not in HOMEWORK_STATUSES:
        logger.error('Неизвестный статус')
        # вызов исключения для отправки ботом сообщения в телеграм
        raise Exception('Неизвестный статус')
    if counter[0] == 0:
        old_status[0] = status
        counter[0] = 1
        return old_status[0]
    if counter[0] == 1:
        if status == old_status[0]:
            return False
        else:
            return status


def main():
    """Метод выполнения основного кода."""
    if (PRACTICUM_TOKEN == '') or (TELEGRAM_TOKEN == '') or (CHAT_ID == 0):
        message = 'Отсутствуют обязательные переменные окружения'
        logger.critical(message)
        # вызов исключения для отправки ботом сообщения в телеграм
        raise Exception(message)
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    current_timestamp = current_timestamp - 86400
    while True:
        try:
            response = get_api_answer(ENDPOINT, current_timestamp)
            if check_response(response):
                homework = response['homeworks'][0]
                message = parse_status(homework)
                send_message(bot, message)
            time.sleep(RETRY_TIME)
            current_timestamp = int(time.time())
            current_timestamp = current_timestamp - 86400
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(
                f'Сбой в работе программы: {error}')
            send_message(bot, message)
            time.sleep(RETRY_TIME)
            current_timestamp = int(time.time())
            current_timestamp = current_timestamp - 86400
            continue


if __name__ == '__main__':
    main()
