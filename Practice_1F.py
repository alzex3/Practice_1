import json
import hashlib
import requests
from tqdm import tqdm
from time import sleep
from datetime import datetime
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaInMemoryUpload


def path():
    return f'Backup {datetime.now().strftime("%d.%m.%Y, %H.%M.%S")}'


class VKDownloader:
    def __init__(self, token):
        self.token = token

    def download(self, user_id, mode):
        if mode == 'user':
            method = 'photos.get'
            params = {'user_id': f'{user_id}', 'album_id': 'profile', 'extended': '1',
                      'access_token': f'{self.token}', 'v': '5.52'}

        elif mode == 'all':
            method = 'photos.getAll'
            params = {'owner_id': f'{user_id}', 'count': '200', 'extended': '1',
                      'access_token': f'{self.token}', 'v': '5.52'}

        url = f'https://api.vk.com/method/{method}'
        resp = requests.get(url, params).json()

        pics = {}
        for pic in resp['response']['items']:

            pic_sizes = {}
            for key, value in pic.items():
                if 'photo_' in key:
                    pic_size = int(key.split('_')[1])
                    pic_sizes[pic_size] = value
            max_pic = max(pic_sizes.items())
            pic_size = max_pic[0]
            pic_url = max_pic[1]

            pic_likes = pic['likes']['count']
            pic_date = datetime.fromtimestamp(pic['date']).strftime('%d.%m.%Y, %H.%M.%S')

            if f'pic_{pic_likes}.jpg' not in pics.keys():
                pics[f'pic_{pic_likes}.jpg'] = {'url': pic_url, 'size': pic_size}
            else:
                pics[f'pic_{pic_likes}_{pic_date}.jpg'] = {'url': pic_url, 'size': pic_size}

        return pics


class OKDownloader:
    def __init__(self, app_key, token, sec_key):
        self.url = 'https://api.ok.ru/fb.do?'
        self.app_key = app_key
        self.token = token
        self.sec_key = sec_key

    def get_albums_ids(self, fid):
        hash_str = f'application_key={self.app_key}count=100fid={fid}method=photos.getAlbums{self.sec_key}'
        sig = hashlib.md5(hash_str.encode()).hexdigest()

        request = f'{self.url}application_key={self.app_key}&fid={fid}&method=photos.getAlbums&count=100' \
                  f'&sig={sig}&access_token={self.token}'

        albums_ids = []
        for album in requests.get(request).json()['albums']:
            albums_ids.append(album['aid'])

        return albums_ids

    def get_album_pics(self, aid):
        hash_str = f'aid={aid}application_key={self.app_key}count=100' \
                   f'fields=photo.PIC_MAX,photo.LIKE_COUNT,photo.CREATED_MSmethod=photos.getPhotos{self.sec_key}'
        sig = hashlib.md5(hash_str.encode()).hexdigest()

        request = f'{self.url}aid={aid}&application_key={self.app_key}&method=photos.getPhotos&count=100' \
                  f'&fields=photo.PIC_MAX%2Cphoto.LIKE_COUNT%2Cphoto.CREATED_MS' \
                  f'&sig={sig}&access_token={self.token}'

        return requests.get(request).json()

    def get_user_pics(self):
        hash_str = f'application_key={self.app_key}count=100' \
                   f'fields=photo.PIC_MAX,photo.LIKE_COUNT,photo.CREATED_MSmethod=photos.getPhotos{self.sec_key}'
        sig = hashlib.md5(hash_str.encode()).hexdigest()

        request = f'{self.url}application_key={self.app_key}&method=photos.getPhotos&count=100' \
                  f'&fields=photo.PIC_MAX%2Cphoto.LIKE_COUNT%2Cphoto.CREATED_MS' \
                  f'&sig={sig}&access_token={self.token}'

        return requests.get(request).json()

    def download(self, user_id, mode):

        def user_pics():
            pics = {}
            for user_pic in self.get_user_pics()['photos']:
                pic_likes = user_pic['like_count']
                pic_date = datetime.fromtimestamp(int(str(user_pic['created_ms'])[0:10])).strftime('%d.%m.%Y, %H.%M.%S')

                if f'pic_{pic_likes}.jpg' not in pics.keys():
                    pics[f'pic_{pic_likes}.jpg'] = {'url': user_pic['pic_max'], 'size': 'max'}
                else:
                    pics[f'pic_{pic_likes}_{pic_date}.jpg'] = {'url': user_pic['pic_max'], 'size': 'max'}

            return pics

        def all_pics():
            pics = user_pics()
            for album in self.get_albums_ids(user_id):
                for pic in self.get_album_pics(album)['photos']:

                    pic_likes = pic['like_count']
                    pic_date = datetime.fromtimestamp(int(str(pic['created_ms'])[0:10])).strftime('%d.%m.%Y, %H.%M.%S')

                    if f'pic_{pic_likes}.jpg' not in pics.keys():
                        pics[f'pic_{pic_likes}.jpg'] = {'url': pic['pic_max'], 'size': 'max'}
                    else:
                        pics[f'pic_{pic_likes}_{pic_date}.jpg'] = {'url': pic['pic_max'], 'size': 'max'}

            return pics

        if mode == 'user':
            return user_pics()
        elif mode == 'all':
            return all_pics()


class INSTDownloader:
    def __init__(self, token):
        self.token = token

    def download(self):
        url = 'https://graph.instagram.com/me/media?'
        fields = 'id, media_type, media_url, timestamp'
        params = {'fields': f'{fields}', 'access_token': f'{self.token}'}
        resp = requests.get(url, params).json()

        pics = {}
        for pic in resp['data']:
            pic_date = pic['timestamp'][0:19].replace(':', '.')
            pics[f'pic_{pic_date}.jpg'] = {'url': pic['media_url'], 'size': 'max'}

        while 'next' in resp['paging']:
            resp = requests.get(resp['paging']['next']).json()
            for pic in resp['data']:
                pic_date = pic['timestamp'][0:19].replace(':', '.')
                pics[f'pic_{pic_date}.jpg'] = {'url': pic['media_url'], 'size': 'max'}

        return pics


class YaUploader:
    def __init__(self, token):
        self.token = token

    def upload(self, items):
        path_name = path()
        path_put_url = f'https://cloud-api.yandex.net/v1/disk/resources?path={path_name}'
        requests.put(path_put_url, headers={'Authorization': self.token})

        result_list = []
        with tqdm(desc='Копирование', total=len(items)) as pbar:
            for name, item in items.items():
                item_get_url = f'https://cloud-api.yandex.net/v1/disk/resources/upload?path={path_name}%2F{name}'
                item_put_url = requests.get(item_get_url, headers={'Authorization': self.token}).json()['href']
                requests.put(item_put_url, data=requests.get(item['url']))
                result_list.append({'file_name': name, 'size': str(item['size'])})
                sleep(0.1)
                pbar.update(1)

        json_get_url = f'https://cloud-api.yandex.net/v1/disk/resources/upload?path={path_name}%2F{path_name}.json'
        json_put_url = requests.get(json_get_url, headers={'Authorization': self.token}).json()['href']
        requests.put(json_put_url, json.dumps(result_list))
        print('Копирование завершено успешно!')


class GglUploader:
    def __init__(self, cred_file):
        self.cred_file = cred_file

    def upload(self, items):
        path_name = path()
        scopes = ['https://www.googleapis.com/auth/drive']
        credentials = Credentials.from_authorized_user_file(self.cred_file, scopes)
        service = build('drive', 'v3', credentials=credentials)

        folder_metadata = {
            'name': path_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = service.files().create(body=folder_metadata, fields='id').execute()
        folder_id = folder.get('id')

        result_list = []
        with tqdm(desc='Копирование', total=len(items)) as pbar:
            for name, item in items.items():
                name = name
                data = requests.get(item['url']).content
                file_metadata = {
                    'name': name,
                    'parents': [folder_id]
                }
                media = MediaInMemoryUpload(data, resumable=True)
                service.files().create(body=file_metadata, media_body=media, fields='id').execute()

                result_list.append({'file_name': name, 'size': str(item['size'])})
                sleep(0.1)
                pbar.update(1)

        name = f'{path_name}.json'
        data = json.dumps(result_list).encode()
        file_metadata = {
                    'name': name,
                    'parents': [folder_id]
                }
        media = MediaInMemoryUpload(data, resumable=True)
        service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        print('Копирование завершено успешно!')


# VK Data
vk_token = ''
vk_user_id = ''

# OK Data
application_key = ''
ok_access_token = ''
secret_key = ''
ok_user_id = ''

# INST Data
inst_access_token = ''

# Ya Data
ya_token = ''

# Gg Data
credentials_file = ''


vk_downloader = VKDownloader(vk_token)
ok_downloader = OKDownloader(application_key, ok_access_token, secret_key)
inst_downloader = INSTDownloader(inst_access_token)

ya_uploader = YaUploader(ya_token)
gl_uploader = GglUploader(credentials_file)


gl_uploader.upload(vk_downloader.download(vk_user_id, 'user'))
gl_uploader.upload(ok_downloader.download(ok_user_id, 'user'))
gl_uploader.upload(inst_downloader.download())

ya_uploader.upload(vk_downloader.download(vk_user_id, 'user'))
ya_uploader.upload(ok_downloader.download(ok_user_id, 'user'))
ya_uploader.upload(inst_downloader.download())
