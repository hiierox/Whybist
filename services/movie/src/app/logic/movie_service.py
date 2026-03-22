import logging
from typing import Any

from app.api.schemas import MovieSearchByIdResponse, MovieSearchByKeywordResponse
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

    async def get_movie_by_keyword(
        self, keyword: str, page: int = 1
    ) -> MovieSearchByKeywordResponse:
        """Gets a list of movies by keyword."""

        key = self._cache_key('search', keyword, page)
        cached_response = await self._get_cached_data(
            key, settings.SEARCH_BY_KEYWORD_TTL
        )
        if cached_response is not None:
            return MovieSearchByKeywordResponse.model_validate(cached_response)

        response = await self.kinopoisk_service.get_movie_by_keyword(
            params={'keyword': keyword, 'page': page}
        )
        validated_response = MovieSearchByKeywordResponse.model_validate(response)
        dict_response = validated_response.model_dump(by_alias=True, mode='json')
        await self._set_cache_data(key, dict_response, settings.SEARCH_BY_KEYWORD_TTL)

        return validated_response

    async def get_movie_by_id(self, movie_id: int) -> MovieSearchByIdResponse:
        """Gets a movie by id"""

        key = self._cache_key('movie', movie_id)
        cached = await self._get_cached_data(key, settings.MOVIE_ID_TTL)
        if cached is not None:
            return MovieSearchByIdResponse.model_validate(cached)

        response = await self.kinopoisk_service.get_movie_by_id(movie_id=movie_id)
        validated_response = MovieSearchByIdResponse.model_validate(response)
        dict_response = validated_response.model_dump(by_alias=True, mode='json')
        await self._set_cache_data(key, dict_response, settings.MOVIE_ID_TTL)

        return validated_response
