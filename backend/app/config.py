"""
Application settings, loaded from environment variables (see .env.example).
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/condo_argo"
    jwt_secret_key: str = "change-this-to-a-long-random-value-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 240
    # Comma-separated list of allowed frontend origins, e.g.
    # "https://condo-argo-frontend.vercel.app,http://localhost:5173"
    # Defaults to "*" so local dev keeps working without extra config.
    cors_origins: str = "*"

    @property
    def cors_origin_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    class Config:
        env_file = ".env"


settings = Settings()
