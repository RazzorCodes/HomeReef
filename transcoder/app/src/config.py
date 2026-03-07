from misc.logger import logger
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    media_path: str = "/media"

    db_path: str = "/storage/spacesaver-transcode/main.db"

    model_config = SettingsConfigDict(env_file="../.env")


config = AppConfig()

for field_name in config.model_fields.keys():
    logger.debug(f"- {field_name} was set to: {getattr(config, field_name)}")
