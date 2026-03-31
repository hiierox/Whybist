from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env')
    KINOPOISK_API_KEY: str = ''
    REDIS_HOST: str = 'redis'
    REDIS_PORT: int = 6379
    SEARCH_BY_KEYWORD_TTL: int = 3600
    GET_BY_ID_TTL: int = 7 * 24 * 3600
    COMMON_FILMS_TTL: int = 3600

COMMON_FILMS_PAGE_SIZE = 10

settings = Settings()
