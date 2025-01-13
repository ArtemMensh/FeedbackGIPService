import requests
from config import Config

config = Config()

def create_you_gile_task(task_title, task_description):
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
    else:
        print("Ошибка при создании задачи: " + response.status_code + " - " + response.text)