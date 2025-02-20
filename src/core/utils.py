import gettext
import os
from fastapi import Request


# Функция для получения переводов на основе языка
def _get_translation_text(domain: str, lang):
    # Получаем путь к директории, где находится данный файл
    current_dir = os.path.dirname(__file__)
    # Путь к папке locales, находящейся в корне проекта
    localedir = os.path.abspath(os.path.join(current_dir, '../../locales'))
    # log.debug(f'localedir: {localedir}')
    translation = gettext.translation(domain, localedir, languages=[lang], fallback=True)
    return translation.gettext


def get_translation(request: Request, domain: str):
    lang_header = request.headers.get('Accept-Language')
    lang = lang_header.split(',')[0] if lang_header else 'en'
    return _get_translation_text(domain, lang)


# if __name__ == "__main__":
#     lang_func = get_translations('en')
#     trans = lang_func("Ресторан")
#     print(trans)

