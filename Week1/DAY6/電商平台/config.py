import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")

    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "shop")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")

    @staticmethod
    def dsn():
        return (
            f"host={Config.DB_HOST} port={Config.DB_PORT} "
            f"dbname={Config.DB_NAME} user={Config.DB_USER} "
            f"password={Config.DB_PASSWORD}"
        )
