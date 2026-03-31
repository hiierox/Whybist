import logging
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from pydantic import BaseModel

from app.api.schemas import (
    CommonFilmsResponse,
    MovieGetByIdResponse,
    MovieSearchByKeywordResponse,
    PersonGetByIdResponse,
    PersonSearchByNameResponse,
    ProfessionKey,
    Sorting,
)
from app.config.config import COMMON_FILMS_PAGE_SIZE, settings
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
        fetcher: Callable[[], Awaitable[dict[str, Any]]],
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
            ),
        )

    async def get_movie_by_id(self, movie_id: int) -> MovieGetByIdResponse:
        """Gets a movie by id"""
        key = self._cache_key('movie', movie_id)
        return await self._fetch_from_kinopoiskapi_or_cache(
            key=key,
            ttl=settings.GET_BY_ID_TTL,
            model=MovieGetByIdResponse,
            fetcher=lambda: self.kinopoisk_service.get_movie_by_id(movie_id=movie_id),
        )

    async def search_person_by_name(
        self, name: str, page: int
    ) -> PersonSearchByNameResponse:
        """Gets a list of persons by name."""
        key = self._cache_key('search_person', name, page)
        return await self._fetch_from_kinopoiskapi_or_cache(
            key=key,
            ttl=settings.SEARCH_BY_KEYWORD_TTL,
            model=PersonSearchByNameResponse,
            fetcher=lambda: self.kinopoisk_service.search_person_by_name(
                params={'name': name, 'page': page}
            ),
        )

    async def get_person_by_id(self, person_id: int) -> PersonGetByIdResponse:
        """Gets a person by id."""
        key = self._cache_key('person', person_id)
        return await self._fetch_from_kinopoiskapi_or_cache(
            key=key,
            ttl=settings.GET_BY_ID_TTL,
            model=PersonGetByIdResponse,
            fetcher=lambda: self.kinopoisk_service.get_person_by_id(person_id),
        )

    async def _get_common_fimls_ids(
        self,
        person1_id: int,
        person2_id: int,
        person1_role: str,
        person2_role: str,
    ) -> list[int]:
        """Builds intersection of film IDs for two persons filtered by roles."""
        person_one = await self.get_person_by_id(person1_id)
        person_two = await self.get_person_by_id(person2_id)

        set_p1 = {
            film.film_id
            for film in person_one.films
            if film.profession_key == person1_role
        }
        set_p2 = {
            film.film_id
            for film in person_two.films
            if film.profession_key == person2_role
        }
        return list(set_p1 & set_p2)

    def _slice_common_films_ids(
        self, lst: list[int], page: int, sorting: Sorting
    ) -> list[int]:
        """Sorts common film IDs and returns one page slice."""
        reverse = sorting == Sorting.NEWEST
        sliced = sorted(lst, reverse=reverse)
        start = (page - 1) * COMMON_FILMS_PAGE_SIZE
        end = start + COMMON_FILMS_PAGE_SIZE
        return sliced[start:end]

    @staticmethod
    def _normalize_person_pair(
        person1_id: int,
        person2_id: int,
        person1_role: ProfessionKey,
        person2_role: ProfessionKey,
    ) -> tuple[int, int, ProfessionKey, ProfessionKey]:
        """Normalizes pair order to produce a stable cache key."""
        pair = sorted(
            [(person1_id, person1_role), (person2_id, person2_role)],
            key=lambda x: (x[0], x[1]),
        )
        return pair[0][0], pair[1][0], pair[0][1], pair[1][1]

    async def find_common_films_of_two_persons(
        self,
        person1_id: int,
        person2_id: int,
        person1_role: ProfessionKey,
        person2_role: ProfessionKey,
        page: int,
        sorting: Sorting,
    ) -> CommonFilmsResponse:
        """
        Returns one page of common film IDs using cached intersection when possible.
        """
        p1, p2, r1, r2 = self._normalize_person_pair(
            person1_id, person2_id, person1_role, person2_role
        )
        key = self._cache_key('common', p1, p2, r1, r2)
        cached = await self._get_cached_data(key, settings.COMMON_FILMS_TTL)
        if cached is not None:
            film_ids = cached.get('film_ids')
            if isinstance(film_ids, list):
                sliced = self._slice_common_films_ids(film_ids, page, sorting)
                return CommonFilmsResponse(film_ids=sliced)
            await self.redis_service.delete(key)

        intersection = await self._get_common_fimls_ids(
            person1_id, person2_id, person1_role, person2_role
        )
        await self._set_cache_data(
            key, {'film_ids': intersection}, settings.COMMON_FILMS_TTL
        )
        sliced = self._slice_common_films_ids(list(intersection), page, sorting)
        return CommonFilmsResponse(film_ids=sliced)
