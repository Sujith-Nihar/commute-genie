import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "gemini-2.5-flash")
    LTA_ACCOUNT_KEY: str = os.getenv("LTA_ACCOUNT_KEY", "")
    DEFAULT_COUNTRY: str = os.getenv("DEFAULT_COUNTRY", "Singapore")
    OPENWEATHER_API_KEY: str = os.getenv("OPENWEATHER_API_KEY", "")


settings = Settings()