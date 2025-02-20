import redis.asyncio as aioredis
from redis.asyncio import Redis, ConnectionPool
from settings import get_settings

cfg = get_settings()


class RedisClient:
    def __init__(
            self,
            host: str,
            port: int,
            db: int = 0,
    ):
        self.host = host
        self.port = port
        self.db = db
        self.pool = None
        self.redis = None

    async def connect(self):
        self.pool = aioredis.ConnectionPool.from_url(
            f'redis://{self.host}:{self.port}/{self.db}',
            decode_responses=True
        )
        # self.redis = aioredis.Redis.from_url(
        #     f'redis://{self.host}:{self.port}/{self.db}',
        #     decode_responses=True
        # )

    async def get_pool(self) -> ConnectionPool:
        return self.pool

    async def get_redis(self) -> Redis:
        ses = await aioredis.Redis.from_pool(self.pool)
        yield ses
        await ses.aclose()

    async def set(self, key, value):
        await self.redis.set(key, value)

    async def get(self, key):
        value = await self.redis.get(key)
        return value

    async def incrby(self, key, amount):
        await self.redis.incrby(key, amount)

    async def delete(self, key):
        await self.redis.delete(key)

    async def close(self):
        # await self.redis.aclose()
        await self.pool.disconnect()



redis_client = RedisClient(host=cfg.server_host, port=6379, db=0)

# if __name__ == '__main__':
#     async def main():
#         await redis_client.connect()
#         await redis_client.set('key', 'ytuhdu')
#         value = await redis_client.get('key')
#         print(value)
#         await redis_client.close()
#
#     import asyncio
#
#     asyncio.run(main())
