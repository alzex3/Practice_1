from app.services import VKDownloader, OKDownloader, INSTDownloader, YaUploader, GglUploader

from settings import VK_API_V


def get_source():
    print("""\nВыберите источник фоторгафий:
        vk - ВКонтакте 
        ok - Одноклассники 
        in - Instagram
        exit - выход""")

    while True:
        source = input('\nВведите команду: ').lower()
        if source == 'vk':
            vk_token = input('Введите токен ВКонтакте:\n')
            vk_user_id = input('Введите id пользователя, фотографии которого необходимо сохранить:\n')
            mode = input('Выберите режим | "user" - сохранить фоторгафии профиля, "all" - все фотографии:\n')
            vk_downloader = VKDownloader(vk_token, vk_user_id, mode, VK_API_V)
            return vk_downloader

        elif source == 'ok':
            ok_access_token = input('Введите токен Одноклассники:\n')
            application_key = input('Введите "application key":\n')
            secret_key = input('Введите токен "secret key":\n')
            ok_user_id = input('Введите id пользователя, фотографии которого необходимо сохранить:\n')
            mode = input('Выберите режим | "user" - сохранить фоторгафии профиля, "all" - все фотографии:\n')
            ok_downloader = OKDownloader(application_key, ok_access_token, secret_key, ok_user_id, mode)
            return ok_downloader

        elif source == 'in':
            inst_access_token = input('Введите токен Instagram:\n')
            inst_downloader = INSTDownloader(inst_access_token)
            return inst_downloader

        elif source == 'exit':
            print('Программа завершена!')
            break

        else:
            print('Комманда введена неверно, повторите ввод!')


def get_target():
    print("""Выберите хранилище для сохранения:
        gl - Google Drive
        ya - Яндекс Диск
        exit - выход""")

    while True:
        target = input('\nВведите команду: ').lower()
        if target == 'ya':
            ya_token = input('Введите токен Яндекс Диск:\n')
            ya_uploader = YaUploader(ya_token)
            return ya_uploader

        elif target == 'gl':
            credentials_file = input('При первом запуске будет открыт браузер для аутентификации.'
                                     '\nВведите название файла .json с правами доступа Google Api (Credentials):\n')
            gl_uploader = GglUploader(credentials_file)
            return gl_uploader

        elif target == 'exit':
            print('Программа завершена!')
            break

        else:
            print('Комманда введена неверно, повторите ввод!')


def handler():
    print('Программа "Social Backup" запущена!\n')
    try:
        get_target().upload(get_source().download())
    except AttributeError:
        pass
    except Exception:
        print('\nДанные авторизации указаны неверно!')
