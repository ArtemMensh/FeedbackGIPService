import base64
import os
import shutil
import traceback
import paramiko
import pymysql
import requests
import logging
from pathlib import Path
from flask import Flask, request, jsonify
from DropboxManager import DropboxManager
from config import Config
from yougile import create_you_gile_task


logging.basicConfig(
    filename='app.log',  # Имя файла для логов
    filemode='a',        # Режим записи: 'a' для добавления, 'w' для перезаписи
    format='%(asctime)s - %(levelname)s - %(message)s',  # Формат сообщения
    level=logging.ERROR   # Уровень логирования
)
config = Config()
dropbox_manager = DropboxManager(config)
app = Flask(__name__)


def get_files_from_server(folder_name, save_path="./download"):
    """
    Функция получения файлов с удаленного файлового хранилища и сохранения их локально
    :param save_path: путь до локальной папки для сохранения
    :param folder_name:  имя папки на удаленном файловом хранилище
    :return: путь до локальной папки с файлами
    """
    sftp_host = config.get('sftp', 'SFTP_HOST')
    sftp_path_folder_feedback = config.get('sftp', 'SFTP_PATH_FOLDER_FEEDBACK')
    sftp_port = config.getint('sftp', 'SFTP_PORT')
    sftp_username = config.get('sftp', 'SFTP_USERNAME')
    sftp_password = config.get('sftp', 'SFTP_PASSWORD')

    if not os.path.exists(save_path):
        os.makedirs(save_path)

    full_path = sftp_path_folder_feedback + folder_name

    with paramiko.Transport((sftp_host, sftp_port)) as transport:
        transport.connect(username=sftp_username, password=sftp_password)
        with paramiko.SFTPClient.from_transport(transport) as sftp:
            local_path = Path(save_path) / Path(folder_name).name
            os.makedirs(local_path, exist_ok=True)

            for filename in sftp.listdir(full_path):
                remote_file_path = full_path + "/" + filename
                local_file_path = local_path / filename
                sftp.get(remote_file_path, str(local_file_path))

            sftp.close()
        transport.close()

    return local_path


# Функция для загрузки файлов на файлообменник и получения URL
def upload_files(local_path, delete_local_files=True):
    file_sharing_url = config.get('file.io', 'FILE_SHARING_URL')
    urls = []
    for filename in os.listdir(local_path):
        file_path = local_path / filename
        with open(file_path, 'rb') as f:
            response = requests.post(file_sharing_url, files={'file': f})
            if response.status_code == 200:
                url = response.json().get('link')
                urls.append(
                    filename + ": " + '<a target="_blank" rel="noopener noreferrer" href="' + url + '">' + url + '</a>')

    if delete_local_files:
        shutil.rmtree(local_path)

    return urls


# Функция для преобразования JSON данных в строку "key: value <br>"
def json_to_html_string(data):
    """
    Функция для преобразования JSON данных в строку "key: value <br>"
    :param data: JSON
    :return: строки "key: value <br>"
    """
    html_string = ""
    for key, value in data.items():
        html_string += str(key) + ": " + str(value) + " <br>"
    return html_string


def load_torrent_and_script_files(local_path, game_id):
    """
    Функция для загрузки торрент-файла и скрипта из базы данных
    :param local_path: Путь для сохранения
    :param game_id: ID игры на сервере по которому загружаются скрипт и торрент
    :return: None
    """
    connection = pymysql.connect(
        host='195.201.111.53',
        user='dataworker',
        password='VyFITpKnLQDIj77hOxk4',
        database='uGames',
        port=3306
    )

    cursor = connection.cursor()
    cursor.execute("SELECT torrent_file, torrent_file_name, scriptAuto FROM versoin WHERE item_id = " + game_id)
    rows = cursor.fetchall()
    for row in rows:
        torrent_file_encoded = row[0]
        torrent_file_name = row[1]
        script_auto = row[2]
        # Раскодирование торрент-файла из Base64
        decoded_file = base64.b64decode(torrent_file_encoded)
        # Путь для сохранения торрент-файла
        torrent_file_path = f"{local_path}/{torrent_file_name}"
        script_path = f"{local_path}/script.js"
        # Запись торрент-файла на диск
        with open(torrent_file_path, 'wb') as torrent_file:
            torrent_file.write(decoded_file)

        # Запись скрипта на диск
        if script_auto is not None and script_auto != '' and len(script_auto) > 0:
            with open(script_path, 'w') as script_file:
                script_file.write(script_auto)

    cursor.close()
    connection.close()


def process_folder_and_send(folder_name, data):
    """
    Функция публикации файлов на DropBox и создания задачи в YouGile
    :param folder_name: название папки на сервере
    :param data: тело запроса
    :return: None
    """
    local_path = get_files_from_server(folder_name)
    if str(data['gameId']) != '-1' and str(data['gameId']) != '0':
        load_torrent_and_script_files(local_path, str(data['gameId']))

    file_urls_io = upload_files(local_path, False)
    file_urls_dropbox = dropbox_manager.upload_file(local_path)
    text = json_to_html_string(data)
    full_message = text + "<br> <h1>Ссылки на файлы на DropBox:</h1>" + " <br> ".join(
        file_urls_dropbox) + "<br> <h1>Ссылки на файлы на file.io:</h1>" + " <br> ".join(file_urls_io)
    create_you_gile_task(data.get('topic') + " - " + data.get('gameName'), full_message)


def is_ignored_ticket(data):
    """
    Проверка на исключения запросов по тексту запроса и по параметру userFile
    :param data: тело запроса
    :return: Если запрос прошел проверку, то возвращается True, иначе False
    """
    if 'userFile' in data and data['userFile'] == "Да":
        return True

    ignored_text = ['Недостаточно места на диске',
                    'Система обнаружила недопустимый указатель адреса при попытке использовать в вызове аргумент '
                    'указателя',
                    'Отказано в доступе',
                    'Процесс не может получить доступ к файлу, так как этот файл занят другим процессом',
                    'Не удается найти указанный файл',
                    'Системе не удается найти указанный путь']

    for text in ignored_text:
        if text in data.get('text'):
            return True

    return False


# Маршрут для приема POST-запросов
@app.route('/feedbackGIP/', methods=['POST'])
def upload():
    """
    Маршрут для приема POST-запросов для создания задачи в YouGile
    :return: None
    """
    try:
        data = request.json
        folder_name = str(data.get('feedbackId'))

        if not folder_name:
            return jsonify({"error": "Feedback ID is required"}), 400

        if is_ignored_ticket(data):
            return jsonify({"status": "Ignored task"}), 200

        process_folder_and_send(folder_name, data)

        return jsonify({"status": "Success"}), 200

    except Exception as e:
        logging.error(str(e) + " \n " + traceback.format_exc())
        return jsonify({"error": str(e) + " \n " + traceback.format_exc()}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5678)
