import os
import paramiko
import requests
from pathlib import Path
from flask import Flask, request, jsonify
import shutil
import pymysql
import base64
import traceback

# Конфигурация
YOUGILE_API_URL = "https://ru.yougile.com/api-v2/tasks"
YOUGILE_API_TOKEN = "xIXVgC5WIud+skl95Ku3GOhBlCnM+k+Vrt5eGELPEvC-SyiKex9Htltggr7Vn5-a"
COLUMN_ID = "ff44d75f-ebe4-40de-b950-23916287164e"
SFTP_HOST = '195.201.111.53'
SFTP_PATH_FOLDER_FEEDBACK = "/mnt/nas/home/fundora/fundora-lite-api/storage/feedback/"
SFTP_PORT = 22
SFTP_USERNAME = 'root'
SFTP_PASSWORD = '7GnNeYD352stJa'
FILE_SHARING_URL = 'https://file.io'

# Flask приложение
app = Flask(__name__)


# Функция для создания задачи в youGile
def create_youGile_task(task_title, task_description):
    headers = {
        "Authorization": "Bearer {}".format(YOUGILE_API_TOKEN),
        "Content-Type": "application/json"
    }
    data = {
        "title": task_title,
        "description": task_description,
        "columnId": COLUMN_ID
    }
    response = requests.post(YOUGILE_API_URL, json=data, headers=headers)

    if response.status_code == 201:
        print("Задача успешно создана в youGile.")
    else:
        print("Ошибка при создании задачи: " + response.status_code + " - " + response.text)


# Функция для подключения к серверу и поиска папки
def get_files_from_server(remote_path):
    full_path = SFTP_PATH_FOLDER_FEEDBACK + remote_path
    transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))
    transport.connect(username=SFTP_USERNAME, password=SFTP_PASSWORD)
    sftp = paramiko.SFTPClient.from_transport(transport)

    local_path = Path("./download") / Path(remote_path).name
    os.makedirs(local_path, exist_ok=True)

    for filename in sftp.listdir(full_path):
        remote_file_path = full_path + "/" + filename
        local_file_path = local_path / filename  # Проверяем, существует ли файл локально
        sftp.get(remote_file_path, str(local_file_path))

    sftp.close()
    transport.close()

    return local_path


# Функция для загрузки файлов на файлообменник и получения URL
def upload_files(local_path):
    urls = []
    for filename in os.listdir(local_path):
        file_path = local_path / filename
        with open(file_path, 'rb') as f:
            response = requests.post(FILE_SHARING_URL, files={'file': f})
            if response.status_code == 200:
                url = response.json().get('link')
                urls.append(
                    filename + ": " + '<a target="_blank" rel="noopener noreferrer" href="' + url + '">' + url + '</a>')

    shutil.rmtree(local_path)

    return urls


# Функция для преобразования JSON данных в строку "key: value <br>"
def json_to_html_string(data):
    html_string = ""
    for key, value in data.items():
        html_string += str(key) + ":" + str(value) + " <br>"
    return html_string


# Основная функция для выполнения всех шагов
def load_torrent_and_script_files(local_path, game_id):
    connection = pymysql.connect(
        host='195.201.111.53',
        user='dataworker',
        password='VyFITpKnLQDIj77hOxk4',
        database='uGames',
        port=3306  # Убедитесь, что используется правильный порт
    )
    cursor = connection.cursor()
    cursor.execute(
        "SELECT torrent_file, torrent_file_name, date_add_torrent_file, scriptAuto FROM versoin WHERE item_id = "
        + game_id)
    rows = cursor.fetchall()
    for row in rows:
        torrent_file_encoded = row[0]
        torrent_file_name = row[1]
        date_add_torrent_file = row[2]
        script_auto = row[3]
        # Раскодирование торрент-файла из Base64
        decoded_file = base64.b64decode(torrent_file_encoded)
        # Путь для сохранения торрент-файла
        torrent_file_path = f"{local_path}/{torrent_file_name}"
        script_path = f"{local_path}/script.js"
        # Запись торрент-файла на диск
        with open(torrent_file_path, 'wb') as torrent_file:
            torrent_file.write(decoded_file)

        if script_auto is not None and script_auto != '' and len(script_auto) > 0:
            with open(script_path, 'w') as script_file:
                script_file.write(script_auto)

    cursor.close()
    connection.close()


def process_folder_and_send(remote_path, data):
    local_path = get_files_from_server(remote_path)
    load_torrent_and_script_files(local_path, str(data['gameId']))

    file_urls = upload_files(local_path)
    text = json_to_html_string(data)
    full_message = text + "<br>".join(file_urls)
    create_youGile_task(data.get('topic'), full_message)


# Маршрут для приема POST-запросов
@app.route('/feedbackGIP/', methods=['POST'])
def upload():
    try:
        data = request.json
        folder_name = str(data.get('feedbackId'))

        if not folder_name:
            return jsonify({"error": "Invalid input"}), 400

        # Запускаем асинхронную обработку
        process_folder_and_send(folder_name, data)

        return jsonify({"status": "Success"}), 200

    except Exception as e:
        return jsonify({"error": str(e) + " " + traceback.format_exc()}), 500


# Пример использования
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5678)
