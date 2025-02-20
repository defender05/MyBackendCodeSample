from typing import Any
from fastapi import HTTPException, status
from loguru import logger as log


def exception_or_log(is_backend: bool, exception_type, message: str):
    """
    LEGACY
    Функция для логирования и исключений
    - Если сервис вызывается в роутерах fastapi,то указываем is_backend=True
      и выбрасываем исключения
    - Если сервис вызывается в обработчиках aiogram,то указываем is_backend=False и
      оставляем только логи

    P.S: Выбрасывание исключений при вызове сервиса из обработчиков aiogram ломает uvicorn,
    который начинает бесконечно отправлять запросы к базе и к вебхуку и получает POST /webhook 404 Not Found
    """
    if is_backend:
        raise HTTPException(
            status_code=exception_type, detail=message)
    else:
        log.warning(message)



def exception_and_log(debug: bool, exception_type, message: str):
    """
    LEGACY
    Выбрасывает исключение и логгирует, если debug=True
    """
    if debug:
        log.warning(message)

    raise HTTPException(
        status_code=exception_type, detail=message)

