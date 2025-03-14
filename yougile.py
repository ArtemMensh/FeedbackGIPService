import logging

import requests
from config import Config

config = Config()


def create_you_gile_task(task_title, task_description):
    logging.basicConfig(
        filename='app.log',  # Имя файла для логов
        filemode='a',  # Режим записи: 'a' для добавления, 'w' для перезаписи
        format='%(asctime)s - %(levelname)s - %(message)s',  # Формат сообщения
        level=logging.ERROR  # Уровень логирования
    )

    yougile_api_token = config.get('yougile', 'YOUGILE_API_TOKEN')
    yougile_api_url = config.get('yougile', 'YOUGILE_API_URL')
    column_id = config.get('yougile', 'COLUMN_ID')

    """
    Функция для создания задачи в youGile
    :param task_title: Заголовок задачи
    :param task_description: Описание задачи
    :return: None
    """
    headers = {
        "Authorization": "Bearer {}".format(yougile_api_token),
        "Content-Type": "application/json"
    }
    data = {
        "title": task_title,
        "description": task_description,
        "columnId": column_id
    }
    response = requests.post(yougile_api_url, json=data, headers=headers)

    if response.status_code == 201:
        print("Задача успешно создана в youGile.")
        logging.getLogger().setLevel(logging.INFO)
        logging.info("Задача успешно создана в youGile.")
        logging.getLogger().setLevel(logging.ERROR)
    else:
        logging.error("Ошибка при создании задачи: " + response.status_code + " - " + response.text)
        print("Ошибка при создании задачи: " + response.status_code + " - " + response.text)


def get_tasks_from_column(column_id):
    logging.basicConfig(
        filename='app.log',  # Имя файла для логов
        filemode='a',  # Режим записи: 'a' для добавления, 'w' для перезаписи
        format='%(asctime)s - %(levelname)s - %(message)s',  # Формат сообщения
        level=logging.ERROR  # Уровень логирования
    )

    yougile_api_token = config.get('yougile', 'YOUGILE_API_TOKEN')
    yougile_api_url = config.get('yougile', 'YOUGILE_API_URL')

    """
    Функция для получения выполненных задач в youGile
    :return: Список выполненных задач
    """
    headers = {
        "Authorization": "Bearer {}".format(yougile_api_token),
        "Content-Type": "application/json"
    }
    response = {
        "content": [],
        "paging": {
            "next": True,
            "count": 0
        }
    }
    complite_tasks = []
    offset = 0
    while response["paging"]["next"]:
        offset = offset + response["paging"]["count"]
        params = {
            "columnId": column_id,
            "includeDeleted": True,
            "offset": offset,
            "limit": 1000
        }
        response_raw = requests.get(yougile_api_url, params=params, headers=headers)
        response = response_raw.json()

        if response_raw.status_code == 200:
            tasks = response["content"]
            for task in tasks:
                complite_tasks.append(task)
        else:
            logging.error(
                "Ошибка при получении выполненных задач: " + response_raw.status_code + " - " + response_raw.text)
            print("Ошибка при получении выполненных задач: " + response_raw.status_code + " - " + response_raw.text)

    return complite_tasks
def get_completed_tasks():
    complite_column_id = config.get('yougile', 'COMPLITE_COLUMN_ID')
    return get_tasks_from_column(complite_column_id)

def get_trash_tasks():
    trash_column_id = config.get('yougile', 'TRASH_COLUMN_ID')
    return get_tasks_from_column(trash_column_id)