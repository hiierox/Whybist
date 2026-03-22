import json
import logging
from typing import Any

from redis.asyncio import Redis, RedisError

logger = logging.getLogger(__name__)


class RedisService:
    def __init__(self, redis_client: Redis):
        self.redis_client = redis_client

    async def get(self, key: str, refreshed_ttl: int) -> dict[str, Any] | None:
        try:
            cached = await self.redis_client.getex(key, ex=refreshed_ttl)
            logger.info(f'{'Redis HIT' if cached else 'Redis MISS'}')
            return json.loads(cached) if cached else None
        except RedisError as e:
            logger.exception(f'Redis GET Error, key: {key}, error: {e}')
        except json.JSONDecodeError as e:
            logger.exception(f'Redis GET Error, key: {key}, error: {e}')
            try:
                await self.redis_client.delete(key)
            except RedisError as delete_error:
                logger.warning(
                    f"""Redis DELETE Error after bad JSON, key: {key},
                    error: {delete_error}"""
                )
        return None

    async def set_value(self, key: str, value: dict[str, Any], ttl: int) -> None:
        value_dump = json.dumps(value)
        try:
            await self.redis_client.set(key, value_dump, ex=ttl)
            logger.info(f'Redis SET key: {key}, SUCCESS')
        except RedisError as e:
            logger.exception(f'Redis SET Error: {e}')
