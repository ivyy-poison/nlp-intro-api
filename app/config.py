from pydantic import BaseSettings

class Settings(BaseSettings):
    db_password: str = "123Password"
    db_user: str = "postgres"
    db_name: str = "CsitProject"
    db_host: str = "localhost"
    db_port: int

    class Config:
        env_file = ".env"

settings = Settings()