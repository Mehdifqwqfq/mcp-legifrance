"""Settings — PISTE creds + Legifrance API base.

Auth via OAuth2 client_credentials on PISTE — secrets sourced from process env
(typically ``source ~/.etikpharma-secrets`` before launching the MCP).
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration.

    Two PISTE credentials are required (``PISTE_CLIENT_ID`` /
    ``PISTE_CLIENT_SECRET``). Everything else has a sane default.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # PISTE OAuth2 client_credentials — Confidential app on oauth.piste.gouv.fr
    piste_client_id: str = Field(
        ...,
        validation_alias="PISTE_CLIENT_ID",
        description="UUID client ID of the PISTE Confidential app.",
    )
    piste_client_secret: str = Field(
        ...,
        validation_alias="PISTE_CLIENT_SECRET",
        description="UUID client secret (yes, the PISTE secret is a UUID).",
    )

    # PISTE endpoints — PROD (sandbox-oauth/sandbox-api ne sert pas la v2.4.2 stable)
    piste_token_url: str = Field(default="https://oauth.piste.gouv.fr/api/oauth/token")
    piste_token_scope: str = Field(default="openid")
    legifrance_base_url: str = Field(
        default="https://api.piste.gouv.fr/dila/legifrance/lf-engine-app"
    )

    user_agent: str = Field(
        default="Etik Pharma MCP / Mehdi Gharbi (fqwqfq@gmail.com)",
    )
    request_timeout: float = Field(default=30.0)
    log_level: str = Field(default="INFO", validation_alias="LEGIFRANCE_LOG_LEVEL")
