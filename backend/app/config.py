from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    quants_api_v2_api_key: str = ""
    cache_dir: str = "data"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
