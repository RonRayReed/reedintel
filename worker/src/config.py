import os
from dataclasses import dataclass


@dataclass
class Settings:
    database_host: str = os.getenv("DATABASE_HOST", "localhost")
    database_port: int = int(os.getenv("DATABASE_PORT", "5432"))
    database_name: str = os.getenv("DATABASE_NAME", "reedintel")
    database_user: str = os.getenv("DATABASE_USER", "reedadmin")
    database_password: str = os.getenv("DATABASE_PASSWORD", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    opendatabot_api_key: str = os.getenv("OPENDATABOT_API_KEY", "")
    deepl_api_key: str = os.getenv("DEEPL_API_KEY", "")
    run_mode: str = os.getenv("RUN_MODE", "once")

    @property
    def db_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.database_user}:{self.database_password}"
            f"@{self.database_host}:{self.database_port}/{self.database_name}"
        )


settings = Settings()
