from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    secret_key: str
    debug: bool = False
    google_client_id: str
    google_client_secret: str
    google_redirect_uri: str
    tile_version: str = "v02"
    # Workstation tooling only (scripts/unsplash_fetch.py). Declared here
    # because Settings forbids extra inputs, so an undeclared key in .env
    # fails every import of this module — including uvicorn's.
    unsplash_access_key: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
