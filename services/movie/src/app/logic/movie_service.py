import logging
from typing import Any

from app.api.schemas import (
    MovieGetByIdResponse,
    MovieSearchByKeywordResponse,
    PersonGetByIdResponse,
    PersonSearchByNameResponse,
)
from app.config.config import settings
from app.external_services.kinopoisk import KinopoiskService
from app.external_services.redis import RedisService

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

    async def search_movie_by_keyword(
        self, keyword: str, page: int = 1
    ) -> MovieSearchByKeywordResponse:
        """Gets a list of movies by keyword."""

        key = self._cache_key('search', keyword, page)
        cached_response = await self._get_cached_data(
            key, settings.SEARCH_BY_KEYWORD_TTL
        )
        if cached_response is not None:
            return MovieSearchByKeywordResponse.model_validate(cached_response)

        response = await self.kinopoisk_service.search_movie_by_keyword(
            params={'keyword': keyword, 'page': page}
        )
        validated_response = MovieSearchByKeywordResponse.model_validate(response)
        dict_response = validated_response.model_dump(by_alias=True, mode='json')
        await self._set_cache_data(key, dict_response, settings.SEARCH_BY_KEYWORD_TTL)

        return validated_response

    async def get_movie_by_id(self, movie_id: int) -> MovieGetByIdResponse:
        """Gets a movie by id"""

        key = self._cache_key('movie', movie_id)
        cached = await self._get_cached_data(key, settings.GET_BY_ID_TTL)
        if cached is not None:
            return MovieGetByIdResponse.model_validate(cached)

        response = await self.kinopoisk_service.get_movie_by_id(movie_id=movie_id)
        validated_response = MovieGetByIdResponse.model_validate(response)
        dict_response = validated_response.model_dump(by_alias=True, mode='json')
        await self._set_cache_data(key, dict_response, settings.GET_BY_ID_TTL)

        return validated_response

    async def search_person_by_name(
        self, name: str, page: int
    ) -> PersonSearchByNameResponse:
        key = self._cache_key('search_person', name, page)
        cached = await self._get_cached_data(key, settings.SEARCH_BY_KEYWORD_TTL)
        if cached is not None:
            return PersonSearchByNameResponse.model_validate(cached)

        response = await self.kinopoisk_service.search_person_by_name(
            params={'name': name, 'page': page}
        )
        validated_response = PersonSearchByNameResponse.model_validate(response)
        dict_response = validated_response.model_dump(by_alias=True, mode='json')
        await self._set_cache_data(key, dict_response, settings.SEARCH_BY_KEYWORD_TTL)
        return validated_response

    async def get_person_by_id(self, person_id: int) -> PersonGetByIdResponse:
        key = self._cache_key('person', person_id)
        cached = await self._get_cached_data(key, settings.GET_BY_ID_TTL)
        if cached is not None:
            return PersonGetByIdResponse.model_validate(cached)

        response = await self.kinopoisk_service.get_person_by_id(person_id)
        validated_response = PersonGetByIdResponse.model_validate(response)
        dict_response = validated_response.model_dump(by_alias=True, mode='json')
        await self._set_cache_data(key, dict_response, settings.GET_BY_ID_TTL)

        return validated_response
