import os
from dataclasses import dataclass


@dataclass
class Settings:
    database_host: str = os.getenv("DATABASE_HOST", "localhost")
    database_port: int = int(os.getenv("DATABASE_PORT", "5432"))
    database_name: str = os.getenv("DATABASE_NAME", "reedintel")
    database_user: str = os.getenv("DATABASE_USER", "reedadmin")
    database_password: str = os.getenv("DATABASE_PASSWORD", "")
    database_sslmode: str = os.getenv("DATABASE_SSLMODE", "disable")

    @property
    def db_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.database_user}:{self.database_password}"
            f"@{self.database_host}:{self.database_port}/{self.database_name}"
            f"?sslmode={self.database_sslmode}"
        )


settings = Settings()
