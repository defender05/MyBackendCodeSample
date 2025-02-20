import json
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import final, Optional, Literal


@final
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',  # first search .dev.env, then .prod.env
        env_file_encoding='utf-8',
        case_sensitive=False,
    )

    run_type: str = 'local'
    debug: bool = True

    server_host: str = 'localhost'
    domain: str = 'localhost'

    # nats config
    # nats_url: str = 'nats://localhost:4222'
    # stream_name: str = 'telegram_updates'
    # stream_subject: str = 'update'
    # stream_retention: RetentionPolicy = RetentionPolicy.WORK_QUEUE

    # auth config
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 1
    SECRET_KEY: str = 'secret'
    ALGORITHM: str = 'HS256'

    # uvicorn config
    host: str = '0.0.0.0'
    port: int = 8000
    reload: bool = True
    workers: int | None = None

    # gunicorn config
    log_level: Literal['debug', 'info', 'warning', 'error', 'critical'] = 'info'
    log_format: str = "[%(asctime)s.%(msecs)03d] %(module)10s:%(lineno)-3d %(levelname)-7s - %(message)s"
    timeout : int = 900

    # redis config
    redis_host: str = 'redis'
    redis_port: int = 6379
    redis_url: str = f'redis://{redis_host}:{redis_port}/0'

    # cors
    cors_origins: list[str] = ['*']
    cors_credentials: bool = True
    cors_methods: list[str] = ['*']
    cors_headers: list[str] = ['*']

    # s3
    default_image_url: Optional[str] = None
    s3_backet_url: str = 'https://s3.timeweb.cloud/some-bucket-name/'

    # database config
    # db_url: str = f'postgresql+asyncpg://postgres:postgres@localhost:5432/postgres'
    async_db_url: str = ''
    sync_db_url: str = ''
    db_host: str = ''
    db_pass: str = ''
    db_user: str = ''
    db_name: str = ''
    db_echo: bool = False
    db_echo_pool: bool = False
    db_pool_size: int = 5
    db_pool_pre_ping: bool = True
    db_max_overflow: int = 10

    # telegram config
    bot_admins: list[int] = [] # telegram id list
    bot_token: str = ''
    test_bot_token: str = ''
    bot_username: str = ''
    webapp_username: Optional[str] = ''
    https_tunnel_url: str = f'https://{domain}'
    webhook_path: str = f'/webhook'
    webhook_url: str = f'https://{domain}/api/v1{webhook_path}'
    webapp_url: str = f'https://{domain}'
    # Дополнительный токен безопасности для webhook (можно придумать самому)
    tg_secret_token: str = '111'


@lru_cache()  # get it from memory
def get_settings() -> Settings:
    return Settings()
