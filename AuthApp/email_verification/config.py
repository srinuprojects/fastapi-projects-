from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    MAIL_USERNAME:  str
    MAIL_PASSWORD:  str
    MAIL_FROM:      str
    MAIL_FROM_NAME: str
    MAIL_SERVER:    str
    MAIL_PORT:      int
    SECRET_KEY:     str
    BASE_URL:       str

    class Config:
        env_file = ".env"


settings = Settings()
