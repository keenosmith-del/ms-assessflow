from functools import lru_cache
import os
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    assessflow_mode: str = "demo"
    assessflow_env: str = "development"
    database_url: str = "sqlite:///./assessflow.db"
    cors_origins: str = "http://localhost:5173"
    entra_tenant_id: str = ""
    entra_client_id: str = ""
    entra_copilot_client_id: str = ""
    entra_audience: str = ""
    foundry_project_endpoint: str = ""
    azure_openai_deployment: str = ""
    azure_language_endpoint: str = ""
    azure_search_endpoint: str = ""
    azure_search_index: str = "assessflow-policies"
    workflow_callback_secret: str = ""
    workflow_start_url: str = ""
    pii_categories: str = "Email,PhoneNumber,USSocialSecurityNumber"

    @model_validator(mode="after")
    def validate_mode(self):
        if self.assessflow_mode not in {"demo", "azure"}:
            raise ValueError("ASSESSFLOW_MODE must be demo or azure")
        if self.assessflow_env == "production":
            if self.assessflow_mode != "azure" or not self.database_url.startswith("postgresql"):
                raise ValueError("Production requires azure mode and PostgreSQL")
            if not all(x.startswith("https://") for x in self.cors_origins.split(",")):
                raise ValueError("Production requires HTTPS origins")
        if self.assessflow_mode == "azure":
            required = [
                self.entra_tenant_id,
                self.entra_client_id,
                self.entra_audience,
                self.foundry_project_endpoint,
                self.azure_openai_deployment,
                self.azure_language_endpoint,
                self.azure_search_endpoint,
            ]
            if not all(required):
                raise ValueError(
                    "Azure mode requires Entra, Foundry, Language and Search configuration"
                )
            for endpoint in [
                self.foundry_project_endpoint,
                self.azure_language_endpoint,
                self.azure_search_endpoint,
            ]:
                if not endpoint.startswith("https://"):
                    raise ValueError("Azure provider endpoints require HTTPS")
        return self


@lru_cache
def settings():
    return Settings(_env_file=os.getenv("ASSESSFLOW_ENV_FILE", ".env"))
