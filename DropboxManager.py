import dropbox

from config import Config
import os
import requests
from dotenv import load_dotenv, set_key
from dropbox.exceptions import AuthError
import shutil


def check_token_validity(token: str) -> bool:
    url = "https://api.dropboxapi.com/2/users/get_current_account"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(url, headers=headers)
    return response.status_code == 200


class DropboxManager:
    def __init__(self, config: Config):
        load_dotenv()
        self.app_key = config.get("dropbox", "DROPBOX_APP_KEY")
        self.app_secret = config.get("dropbox", "DROPBOX_APP_SECRET")
        self.refresh_token = os.getenv("DROPBOX_REFRESH_TOKEN")
        if not self.refresh_token:
            print("DROPBOX_REFRESH_TOKEN is not set in .env file")
            exit(1)
        self.access_token = os.getenv("DROPBOX_API_TOKEN")
        if not self.access_token:
            self.access_token = self.refresh_access_token()

    def check_and_refresh_token(self) -> str:
        if not check_token_validity(self.access_token):
            self.access_token = self.refresh_access_token()
        return self.access_token

    def refresh_access_token(self) -> str:
        """
            Функция для обновления токена Dropbox
            :return: новый токен
        """
        url = "https://api.dropbox.com/oauth2/token"
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.app_key,
            "client_secret": self.app_secret,
        }
        response = requests.post(url, data=data)
        response.raise_for_status()
        new_token = response.json()["access_token"]
        set_key(".env", "DROPBOX_API_TOKEN", new_token)
        return new_token

    def upload_file(self, local_path) -> list:
        """
        Функция для загрузки файла на Dropbox
        :param local_path: путь к файлу
        :return: None
        """
        dbx = dropbox.Dropbox(self.access_token)
        urls = []
        name_folder = local_path.name
        try:
            dbx.files_get_metadata('/' + name_folder)
        except AuthError as e:
            self.refresh_access_token()
            return self.upload_file(local_path)
        except Exception as e:
            dbx.files_create_folder_v2("/" + name_folder)

        for filename in os.listdir(local_path):
            file_path = local_path / filename
            with open(file_path, 'rb') as f:
                dbx.files_upload(f.read(), '/' + name_folder + "/" + filename,
                                 mode=dropbox.files.WriteMode('overwrite'))

            try:
                link = dbx.sharing_create_shared_link_with_settings('/' + name_folder + "/" + filename).url
                urls.append(
                    filename + ": " + '<a target="_blank" rel="noopener noreferrer" href="' + link + '">' + link + '</a>'
                )
            except Exception as e:
                links = dbx.sharing_list_shared_links('/' + name_folder + "/" + filename).links
                for link in links:
                    urls.append(
                        filename + ": " + '<a target="_blank" rel="noopener noreferrer" href="' + link.url + '">' + link.url + '</a>'
                    )

        shutil.rmtree(local_path)
        return urls
