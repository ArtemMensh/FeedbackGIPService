import os
import shutil
from pathlib import Path
from dotenv import load_dotenv
import yadisk


class YandexDiskManager:
    def __init__(self, config):
        load_dotenv()
        token = os.getenv("YANDEX_DISK_API_TOKEN")
        if not token:
            print("YANDEX_DISK_API_TOKEN не задан в .env файле")
            exit(1)
        # Инициализация клиента yadisk
        self.yadisk = yadisk.YaDisk(token=token)
        # Корневая папка на Яндекс.Диске, например "disk:/apps/your_app/"
        self.folder = config.get("yandex", "YANDEX_DISK_FOLDER_NAME")
        # Если корневая папка не существует, создаём её
        if not self.yadisk.exists(self.folder):
            self.yadisk.mkdir(self.folder)

    def upload_file(self, local_path: Path) -> list:
        """
        Загружает файлы из локальной папки на Яндекс.Диск и возвращает список ссылок для общего доступа.
        :param local_path: объект Path, указывающий на локальную папку с файлами.
        :return: список строк с названием файла и HTML-ссылкой.
        """
        file_urls = []
        folder_name = local_path.name
        remote_folder = self.folder + folder_name
        # Создаем удалённую папку, если её ещё нет
        if not self.yadisk.exists(remote_folder):
            self.yadisk.mkdir(remote_folder)

        self.yadisk.publish(remote_folder)
        meta = self.yadisk.get_meta(remote_folder)
        public_link = meta["public_url"]

        file_urls.append(
            f'{folder_name}: <a target="_blank" rel="noopener noreferrer" href="{public_link}">Ссылка на папку</a>'
        )

        # Обходим файлы в локальной папке
        for filename in os.listdir(local_path):
            file_path = local_path / filename
            remote_file_path = remote_folder + "/" + filename
            # Загружаем файл с перезаписью, если он существует
            self.yadisk.upload(str(file_path), remote_file_path, overwrite=True)
            # Публикуем файл для получения общедоступной ссылки
            self.yadisk.publish(remote_file_path)
            meta = self.yadisk.get_meta(remote_file_path)
            public_link = meta["public_url"]

            file_urls.append(
                f'{filename}: <a target="_blank" rel="noopener noreferrer" href="{public_link}">{filename}</a>'
            )
        # Удаляем локальную папку после загрузки
        shutil.rmtree(local_path)
        return file_urls

    def delete_files(self, name_folders: list):
        """
        Удаляет указанные папки с Яндекс.Диска.
        :param name_folders: список имён папок (внутри self.folder)
        """
        for folder in name_folders:
            remote_folder = self.folder + folder
            if self.yadisk.exists(remote_folder):
                self.yadisk.remove(remote_folder, permanently=True)
                print(f"Папка {remote_folder} удалена")
            else:
                print(f"Папка {remote_folder} не существует")
