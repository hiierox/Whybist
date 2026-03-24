from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class Country(BaseModel):
    country: str


class Genre(BaseModel):
    genre: str


class MovieSearchByKeywordModel(BaseModel):
    film_id: int = Field(alias='filmId')
    name_ru: str | None = Field(default=None, alias='nameRu')
    name_en: str | None = Field(default=None, alias='nameEn')
    type: str | None = None
    year: str | None = None
    film_length: str | None = Field(default=None, alias='filmLength')
    countries: list[Country] | None = None
    genres: list[Genre] | None = None
    rating: str | None = None
    rating_vote_count: int | None = Field(default=None, alias='ratingVoteCount')
    poster_url_preview: HttpUrl | None = Field(default=None, alias='posterUrlPreview')


class MovieSearchByKeywordResponse(BaseModel):
    keyword: str
    page_count: int = Field(alias='pagesCount')
    films: list[MovieSearchByKeywordModel]


class MovieGetByIdResponse(BaseModel):
    id: int = Field(alias='kinopoiskId')
    name_ru: str | None = Field(default=None, alias='nameRu')
    name_en: str | None = Field(default=None, alias='nameEn')
    name_original: str | None = Field(default=None, alias='nameOriginal')
    poster_url: HttpUrl | None = Field(default=None, alias='posterUrl')
    rating_kinopoisk: float | None = Field(default=None, alias='ratingKinopoisk')
    rating_kinopoisk_vote_count: int | None = Field(
        default=None, alias='ratingKinopoiskVoteCount'
    )
    rating_imdb: float | None = Field(default=None, alias='ratingImdb')
    rating_imdb_vote_count: int | None = Field(
        default=None, alias='ratingImdbVoteCount'
    )
    web_url: HttpUrl | None = Field(default=None, alias='webUrl')
    year: int | None = None
    film_length: int | None = Field(default=None, alias='filmLength')
    description: str | None = None
    type: str | None = None
    rating_mpaa: str | None = Field(default=None, alias='ratingMpaa')
    countries: list[Country] | None = None
    genres: list[Genre] | None = None
    start_year: int | None = Field(default=None, alias='startYear')
    end_year: int | None = Field(default=None, alias='endYear')
    serial: bool | None = None
    short_film: bool | None = Field(default=None, alias='shortFilm')
    completed: bool | None = None


class PersonSearchByNameModel(BaseModel):
    kinopoisk_id: int = Field(alias='kinopoiskId')
    web_url: str = Field(alias='webUrl')
    name_ru: str | None = Field(default=None, alias='nameRu')
    name_en: str | None = Field(default=None, alias='nameEn')
    sex: Literal['MALE', 'FEMALE', 'UNKNOWN'] | None = None
    poster_url: HttpUrl | None = Field(default=None, alias='posterUrl')


class PersonSearchByNameResponse(BaseModel):
    total: int
    items: list[PersonSearchByNameModel]


class PersonSpouses(BaseModel):
    person_id: int = Field(alias='personId')
    name: str | None = None
    divorced: bool
    divorced_reason: str | None = Field(default=None, alias='divorcedReason')
    sex: Literal['MALE', 'FEMALE']
    children: int
    web_url: str = Field(alias='webUrl')
    relation: str


class PersonFilms(BaseModel):
    film_id: int = Field(alias='filmId')
    name_ru: str | None = Field(default=None, alias='nameRu')
    name_en: str | None = Field(default=None, alias='nameEn')
    rating: str | None = None
    general: bool
    description: str | None = None
    profession_key: str = Field(alias='professionKey')


class PersonGetByIdResponse(BaseModel):
    person_id: int = Field(alias='personId')
    web_url: str | None = Field(default=None, alias='webUrl')
    name_ru: str | None = Field(default=None, alias='nameRu')
    name_en: str | None = Field(default=None, alias='nameEn')
    sex: Literal['MALE', 'FEMALE'] | None = None
    poster_url: str = Field(alias='posterUrl')
    growth: str | None = None
    birthday: str | None = None
    death: str | None = None
    age: int | None = None
    birthplace: str | None = None
    deathplace: str | None = None
    has_awards: int | None = Field(default=None, alias='hasAwards')
    profession: str | None = None
    facts: list[str]
    spouses: list[PersonSpouses]
    films: list[PersonFilms]
