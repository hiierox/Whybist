from fastapi import APIRouter, Depends, Path, Query

from app.api.schemas import (
    CommonFilmsResponse,
    MovieGetByIdResponse,
    MovieSearchByKeywordResponse,
    PersonGetByIdResponse,
    PersonSearchByNameResponse,
    ProfessionKey,
    Sorting,
)
from app.dependencies import get_movie_service
from app.logic.movie_service import MovieService

router = APIRouter()


@router.get(
    '/film',
    response_model=MovieSearchByKeywordResponse,
    responses={
        401: {'description': 'Unauthorized (invalid API key)'},
        402: {'description': 'Daily request limit exceeded'},
        404: {'description': 'Movie not found'},
        429: {'description': 'Rate limit exceeded'},
        503: {'description': 'Upstream unavailable'},
    },
)
async def search_by_keyword(
    keyword: str = Query(..., pattern=r'.*\S.*'),
    page: int = Query(1, ge=1),
    movie_service: MovieService = Depends(get_movie_service),
) -> MovieSearchByKeywordResponse:
    return await movie_service.search_movie_by_keyword(keyword=keyword, page=page)


@router.get(
    '/film/{movie_id}',
    response_model=MovieGetByIdResponse,
    responses={
        401: {'description': 'Unauthorized (invalid API key)'},
        402: {'description': 'Daily request limit exceeded'},
        404: {'description': 'Movie not found'},
        429: {'description': 'Rate limit exceeded'},
        503: {'description': 'Upstream unavailable'},
    },
)
async def get_movie_by_id(
    movie_id: int = Path(..., ge=1, le=9999999),
    movie_service: MovieService = Depends(get_movie_service),
) -> MovieGetByIdResponse:
    return await movie_service.get_movie_by_id(movie_id=movie_id)


@router.get(
    '/person',
    response_model=PersonSearchByNameResponse,
    responses={
        401: {'description': 'Unauthorized (invalid API key)'},
        402: {'description': 'Daily request limit exceeded'},
        404: {'description': 'Person not found'},
        429: {'description': 'Rate limit exceeded'},
        503: {'description': 'Upstream unavailable'},
    },
)
async def search_person_by_name(
    name: str = Query(..., pattern=r'.*\S.*'),
    page: int = Query(1, ge=1),
    movie_service: MovieService = Depends(get_movie_service),
) -> PersonSearchByNameResponse:
    return await movie_service.search_person_by_name(name=name, page=page)


@router.get(
    '/person/{person_id}',
    response_model=PersonGetByIdResponse,
    responses={
        401: {'description': 'Unauthorized (invalid API key)'},
        402: {'description': 'Daily request limit exceeded'},
        404: {'description': 'Person not found'},
        429: {'description': 'Rate limit exceeded'},
        503: {'description': 'Upstream unavailable'},
    },
)
async def get_person_by_id(
    person_id: int = Path(..., ge=1, le=9999999),
    movie_service: MovieService = Depends(get_movie_service),
) -> PersonGetByIdResponse:
    return await movie_service.get_person_by_id(person_id=person_id)


@router.get(
    '/common-films',
    response_model=CommonFilmsResponse,
    responses={
        401: {'description': 'Unauthorized (invalid API key)'},
        402: {'description': 'Daily request limit exceeded'},
        404: {'description': 'Person not found'},
        429: {'description': 'Rate limit exceeded'},
        503: {'description': 'Upstream unavailable'},
    },
)
async def find_common_films_of_two_persons(
    person1_id: int = Query(..., ge=1),
    person2_id: int = Query(..., ge=1),
    person1_role: ProfessionKey = Query(ProfessionKey.ACTOR),
    person2_role: ProfessionKey = Query(ProfessionKey.ACTOR),
    page: int = Query(1, ge=1),
    sorting: Sorting = Query(Sorting.NEWEST),
    movie_service: MovieService = Depends(get_movie_service),
) -> CommonFilmsResponse:
    return await movie_service.find_common_films_of_two_persons(
        person1_id=person1_id,
        person2_id=person2_id,
        person1_role=person1_role,
        person2_role=person2_role,
        page=page,
        sorting=sorting,
    )
