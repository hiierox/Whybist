import logging
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from pydantic import BaseModel

from app.api.schemas import (
    MovieGetByIdResponse,
    MovieSearchByKeywordResponse,
    PersonGetByIdResponse,
    PersonSearchByNameResponse,
)
from app.config.config import settings
from app.external_services.kinopoisk import KinopoiskService
from app.external_services.redis import RedisService

TModel = TypeVar('TModel', bound=BaseModel)
logger = logging.getLogger(__name__)


class MovieService:
    def __init__(
        self, kinopoisk_service: KinopoiskService, redis_service: RedisService
    ) -> None:
        self.kinopoisk_service = kinopoisk_service
        self.redis_service = redis_service

    async def _get_cached_data(
        self, key: str, refreshed_ttl: int
    ) -> dict[str, Any] | None:
        """Gets cached payload and refreshes TTL"""
        return await self.redis_service.get(key, refreshed_ttl)

    async def _set_cache_data(self, key: str, value: dict[str, Any], ttl: int) -> None:
        """Sets payload in Redis with TTL"""
        await self.redis_service.set_value(key, value, ttl)

    @staticmethod
    def _cache_key(prefix: str, *parts: object) -> str:
        """Builds a key for Redis"""

        key = [prefix.lower().strip()]
        for part in parts:
            if isinstance(part, str):
                key.append(part.strip().lower())
            else:
                key.append(str(part).strip().lower())
        return ':'.join(key)

    async def _fetch_from_kinopoiskapi_or_cache(
            self,
            key: str,
            ttl: int,
            model: type[TModel],
            fetcher: Callable[[], Awaitable[dict[str, Any]]]
    ) -> TModel:
        cached = await self._get_cached_data(key, ttl)
        if cached is not None:
            return model.model_validate(cached)

        raw = await fetcher()
        validated = model.model_validate(raw)
        payload = validated.model_dump(by_alias=True, mode='json')
        await self._set_cache_data(key, payload, ttl)
        return validated

    async def search_movie_by_keyword(
        self, keyword: str, page: int = 1
    ) -> MovieSearchByKeywordResponse:
        """Gets a list of movies by keyword."""
        key = self._cache_key('search', keyword, page)
        return await self._fetch_from_kinopoiskapi_or_cache(
            key=key,
            ttl=settings.SEARCH_BY_KEYWORD_TTL,
            model=MovieSearchByKeywordResponse,
            fetcher=lambda: self.kinopoisk_service.search_movie_by_keyword(
                params={'keyword': keyword, 'page': page}
            )
        )

    async def get_movie_by_id(self, movie_id: int) -> MovieGetByIdResponse:
        """Gets a movie by id"""
        key = self._cache_key('movie', movie_id)
        return await self._fetch_from_kinopoiskapi_or_cache(
            key=key,
            ttl=settings.GET_BY_ID_TTL,
            model=MovieGetByIdResponse,
            fetcher=lambda: self.kinopoisk_service.get_movie_by_id(movie_id=movie_id)
        )

    async def search_person_by_name(
        self, name: str, page: int
    ) -> PersonSearchByNameResponse:
        key = self._cache_key('search_person', name, page)
        return await self._fetch_from_kinopoiskapi_or_cache(
            key=key,
            ttl=settings.SEARCH_BY_KEYWORD_TTL,
            model=PersonSearchByNameResponse,
            fetcher=lambda: self.kinopoisk_service.search_person_by_name(
                params={'name': name, 'page': page}
            )
        )

    async def get_person_by_id(self, person_id: int) -> PersonGetByIdResponse:
        key = self._cache_key('person', person_id)
        return await self._fetch_from_kinopoiskapi_or_cache(
            key=key,
            ttl=settings.GET_BY_ID_TTL,
            model=PersonGetByIdResponse,
            fetcher=lambda: self.kinopoisk_service.get_person_by_id(person_id)
        )
