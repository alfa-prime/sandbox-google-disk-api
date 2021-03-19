from modules.google_api import Create_Service
from googleapiclient.http import MediaFileUpload
import json
import urllib
from urllib.request import urlopen
import os

CLIENT_SECRET_FILE = './.tokens/client_secret.json'
API_NAME = 'drive'
API_VERSION = 'v3'
SCOPES = ['https://www.googleapis.com/auth/drive']

service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)

def load_photos():
    """ берем сведения о фотках """
    with open('./input/photos_a.json', encoding='utf-8') as f:
        result = json.load(f)
    return result

def local_dir_exists(path):
    if os.path.exists(path) is False:
        os.mkdir(path)

def item_exist(name, service_, parent):
    """ проверяем существует ли папка или файл """
    query = f"(name='{name}') and (trashed=false)"
    query = f"{query} and (parents='{parent}')" if parent else query

    response = service_.files().list(q=query, spaces='drive').execute()
    files = response.get('files')

    return files[0]['id'] if files else False

def make_dir(name, service_, parents_=None):
    """ создание папки """
    def make():
        metadata = {'name': name, 'mimeType': 'application/vnd.google-apps.folder'}
        metadata = {**metadata, 'parents': [parents_]} if parents_ else metadata
        print('make:', name)
        return service_.files().create(body=metadata, fields='id').execute().get('id')

    item_id = item_exist(name, service_, parents_)

    return item_id or make()


root_folder_name = 'Михаил Афанасьевич'
root_folder_id = make_dir(root_folder_name, service)
photos = load_photos()
# получаю уникальные названия альбомов
folders = set(photos[index]['album_title'] for index in photos)
folders_google_id = {}

# на gdisk создаю папки по именам альбомов
for folder in folders:
    folders_google_id[folder] = make_dir(folder, service, root_folder_id)

for values in photos.values():
    title = values['album_title']
    parents = folders_google_id[title]

    date = values['date']
    likes = values['likes']
    image_url = values['url']

    file_name = f"{likes:02}-{date}.jpg"

    local_dir_exists('img')
    file_path = './img/'
    # получаю файл по url и сохраняю во временную директорию
    # todo: прописать удаление временной папки по оконачнии скрипта
    urllib.request.urlretrieve(image_url, f"{file_path}{file_name}")

    print(file_name)

    # загружаю фото на gdisk
    if not item_exist(file_name, service, parents):
        file_metadata = {
            'name': file_name,
            'parents': [parents],
        }

        media = MediaFileUpload(f"{file_path}{file_name}", mimetype='image/jpeg', resumable=True)
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
