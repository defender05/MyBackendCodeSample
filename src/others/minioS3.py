import asyncio
from datetime import timedelta

# from minio import Minio
# from minio.error import S3Error

from miniopy_async import Minio, S3Error
from settings import get_settings

cfg = get_settings()


# Инициализируйте клиент Minio
minio_client = Minio(
    f'{cfg.server_host}:9000',
    access_key=cfg.minio_access_key,
    secret_key=cfg.minio_secret_key,
    secure=False
)


# Загрузите файл в ваш бакет
async def upload_file_to_minio(filename, bucket_name):
    try:
        # Загружаем файл в бакет
        await minio_client.fput_object(bucket_name, filename, filename)
        # Получаем URL загруженного файла
        image_url = await minio_client.get_presigned_url(
            method='GET',
            bucket_name=bucket_name,
            object_name=filename,
            expires=timedelta(days=2000)
        )
        return image_url
    except S3Error as err:
        return f"File upload failed: {err}"


# Получите ссылку на файл в вашем бакете
async def get_file_url(filename, bucket_name, expires: timedelta = timedelta(days=2000)):
    try:
        # Получите предварительно подписанную ссылку на файл
        await minio_client.fget_object()
        url = await minio_client.presigned_get_object(
            bucket_name=bucket_name,
            object_name=filename,
            expires=expires
        )
        # await minio_client.get_object()
        return url
    except S3Error as err:
        return f"Failed to get file URL: {err}"


async def main():
    countries = [
        "countries_icons/russia.png",,
    ]

    for filename in countries:
        file_url = await get_file_url(
            filename=filename,
            bucket_name='country-balls',
            expires=timedelta(days=2000)
        )
        print(file_url)


if __name__ == '__main__':
    asyncio.run(main())

