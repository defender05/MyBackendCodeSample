from typing import final
from faststream import FastStream
from faststream.redis import RedisBroker, RedisMessage, Redis

from src.settings import get_settings

cfg = get_settings()


@final
class Queue:
    def __init__(
            self,
            redis_broker_url: str,
            redis_url: str,

    ):
        self.broker = RedisBroker(redis_broker_url)
        self.stream = FastStream(self.broker)
        self.redis = Redis.from_url(redis_url)

    def get_stream(self) -> FastStream:
        return self.stream

    def get_redis(self) -> Redis:
        return self.redis

    def get_broker(self) -> RedisBroker:
        return self.broker


queue = Queue(redis_broker_url=cfg.redis_broker_url, redis_url=cfg.redis_url)
