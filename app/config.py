"""
Configuration settings for the FastAPI application.
This module defines the configuration variables and their default values.
"""
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import computed_field
from sqlalchemy.engine import URL, make_url

IS_PRODUCTION = os.getenv("ENV") == "production"

class Settings(BaseSettings):
    """Configuration settings for the FastAPI application."""
    POSTGRES_USER: str | None = None
    POSTGRES_PASSWORD: str | None = None
    POSTGRES_DB: str | None = None
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str | None = None
    DATABASE_URL_SYNC: str | None = None

    APP_NAME: str = "Ideiateca API"
    DEBUG: bool = False
    ENV: str = "development"
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 43_200
    API_CLIENT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 43_200
    ALGORITHM: str = "HS256"
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 1
    DB_MAX_OVERFLOW: int = 0
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800
    SHOW_DOCS: bool = True
    CORS_ALLOWED_ORIGINS: str = "http://localhost:3000"
    FRONTEND_URL: str = "http://localhost:3000"

    # SMTP
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 15
    SMTP_HOST: str = "smtp-relay.brevo.com"
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM: str = "no-reply@ideateca.com"
    SMTP_USE_TLS: bool = True
    SMTP_USE_SSL: bool = False

    # dev
    EMAIL_DRY_RUN: bool = False

    model_config = SettingsConfigDict(
        env_file=".env.developement" if not IS_PRODUCTION else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @computed_field
    @property
    def database_url(self) -> str:
        """
        Return an async SQLAlchemy URL from a provider URL or POSTGRES_* values.
        """
        if self.DATABASE_URL:
            url = make_url(self.DATABASE_URL).set(drivername="postgresql+asyncpg")
            query = dict(url.query)
            if "sslmode" in query and "ssl" not in query:
                query["ssl"] = query.pop("sslmode")
            # This libpq option is not accepted by asyncpg.
            query.pop("channel_binding", None)
            url = url.set(query=query)
            return url.render_as_string(hide_password=False)
        return self._build_postgres_url("postgresql+asyncpg")

    @computed_field
    @property
    def database_url_sync(self) -> str:
        """
        Return a sync SQLAlchemy URL for Alembic.
        """
        if self.DATABASE_URL_SYNC:
            return make_url(self.DATABASE_URL_SYNC).set(
                drivername="postgresql+psycopg2"
            ).render_as_string(hide_password=False)
        if self.DATABASE_URL:
            return make_url(self.DATABASE_URL).set(
                drivername="postgresql+psycopg2"
            ).render_as_string(hide_password=False)
        return self._build_postgres_url("postgresql+psycopg2")

    def _build_postgres_url(self, drivername: str) -> str:
        if not all((self.POSTGRES_USER, self.POSTGRES_PASSWORD, self.POSTGRES_DB)):
            raise ValueError(
                "Set DATABASE_URL or provide POSTGRES_USER, POSTGRES_PASSWORD, "
                "and POSTGRES_DB."
            )
        return URL.create(
            drivername=drivername,
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            database=self.POSTGRES_DB,
        ).render_as_string(hide_password=False)

    @property
    def cors_allowed_origins(self) -> list[str]:
        """Return the comma-separated browser origins allowed by CORS."""
        return [
            origin.strip()
            for origin in self.CORS_ALLOWED_ORIGINS.split(",")
            if origin.strip()
        ]

settings = Settings()
