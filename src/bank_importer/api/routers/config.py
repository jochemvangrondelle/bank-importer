# Copyright (C) 2025 Jochem van Grondelle <jochem@vangrondelle.net>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the PolyForm Noncommercial License 1.0.0.
# You may not use this program except in compliance with the License.
# A copy of the License is available at https://polyformproject.org/licenses/noncommercial/1.0.0/
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# PolyForm Noncommercial License 1.0.0 for more details.

"""Configuration endpoints."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status

from bank_importer.api.dependencies import get_config_manager
from bank_importer.api.schemas.config import (
    AccountConfigResponse,
    AppSettings,
    ConfigResponse,
    ConfigUpdate,
    DatabaseSettings,
    OutputSettings,
    SettingsResponse,
    SettingsUpdate,
    TargetConfigResponse,
    TranslationSettings,
)
from bank_importer.api.security import require_auth
from bank_importer.config import ConfigManager
from bank_importer.models.config_models import AccountConfig, TargetConfig

router = APIRouter()


@router.get("", tags=["Configuration"])
async def get_config(
    config: Annotated[ConfigManager, Depends(get_config_manager)],
    _: Annotated[dict, Depends(require_auth)],
) -> ConfigResponse:
    """Get full configuration."""
    raw_config = config.config

    # Build response
    app_settings = AppSettings(**raw_config.get("app", {"timezone": "Asia/Bangkok"}))
    db_settings = DatabaseSettings(url=config.get_database_url())
    output_settings = OutputSettings(
        output_dir=config.get_output_dir(),
    )

    translation_config = raw_config.get("translation", {})
    translation_settings = TranslationSettings(
        enable_translation=translation_config.get("enable_translation", True),
        default_source_language=translation_config.get("default_source_language", "TH"),
        default_target_language=translation_config.get("default_target_language", "en"),
        translation_cache_file=translation_config.get(
            "translation_cache_file",
            "translation_cache.json",
        ),
        term_mappings=translation_config.get("term_mappings"),
    )

    accounts = [
        AccountConfigResponse.from_dict(acc) for acc in config.get_all_accounts()
    ]
    targets = [
        TargetConfigResponse.from_dict(tgt) for tgt in config.get_enabled_targets()
    ]

    return ConfigResponse(
        app=app_settings,
        database=db_settings,
        output=output_settings,
        translation=translation_settings,
        accounts=accounts,
        targets=targets,
    )


@router.put("", tags=["Configuration"])
async def update_config(
    config_update: ConfigUpdate,
    config: Annotated[ConfigManager, Depends(get_config_manager)],
    _: Annotated[dict, Depends(require_auth)],
) -> ConfigResponse:
    """Update full configuration."""
    # TODO: Implement full config update
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Full configuration update not yet implemented",
    )


@router.get("/settings", tags=["Configuration"])
async def get_settings(
    config: Annotated[ConfigManager, Depends(get_config_manager)],
    _: Annotated[dict, Depends(require_auth)],
) -> SettingsResponse:
    """Get application settings."""
    raw_config = config.config

    app_settings = AppSettings(**raw_config.get("app", {"timezone": "Asia/Bangkok"}))
    db_settings = DatabaseSettings(url=config.get_database_url())
    output_settings = OutputSettings(output_dir=config.get_output_dir())

    translation_config = raw_config.get("translation", {})
    translation_settings = TranslationSettings(
        enable_translation=translation_config.get("enable_translation", True),
        default_source_language=translation_config.get("default_source_language", "TH"),
        default_target_language=translation_config.get("default_target_language", "en"),
        translation_cache_file=translation_config.get(
            "translation_cache_file",
            "translation_cache.json",
        ),
        term_mappings=translation_config.get("term_mappings"),
    )

    return SettingsResponse(
        app=app_settings,
        database=db_settings,
        output=output_settings,
        translation=translation_settings,
    )


@router.patch("/settings", tags=["Configuration"])
async def update_settings(
    settings_update: SettingsUpdate,
    config: Annotated[ConfigManager, Depends(get_config_manager)],
    _: Annotated[dict, Depends(require_auth)],
) -> SettingsResponse:
    """Update application settings."""
    # TODO: Implement settings update
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Settings update not yet implemented",
    )


@router.get("/accounts", tags=["Configuration"])
async def list_accounts(
    config: Annotated[ConfigManager, Depends(get_config_manager)],
    _: Annotated[dict, Depends(require_auth)],
) -> dict[str, Any]:
    """List all accounts."""
    accounts = [
        AccountConfigResponse.from_dict(acc) for acc in config.get_all_accounts()
    ]
    return {"accounts": accounts}


@router.post(
    "/accounts",
    status_code=status.HTTP_201_CREATED,
    tags=["Configuration"],
)
async def create_account(
    account: AccountConfig,
    config: Annotated[ConfigManager, Depends(get_config_manager)],
    _: Annotated[dict, Depends(require_auth)],
) -> AccountConfigResponse:
    """Create new account."""
    # Check if account already exists
    existing = config.get_account_config(account.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Account '{account.name}' already exists",
        )

    # Add account to config
    accounts = config.config.get("accounts", [])
    accounts.append(account.model_dump_dict())
    config.config["accounts"] = accounts
    config.save_config()

    return AccountConfigResponse.from_account_config(account)


@router.get(
    "/accounts/{account_name}",
    tags=["Configuration"],
)
async def get_account(
    account_name: str,
    config: Annotated[ConfigManager, Depends(get_config_manager)],
    _: Annotated[dict, Depends(require_auth)],
) -> AccountConfigResponse:
    """Get account by name."""
    account = config.get_account_config(account_name)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account '{account_name}' not found",
        )
    return AccountConfigResponse.from_dict(account)


@router.put(
    "/accounts/{account_name}",
    tags=["Configuration"],
)
async def update_account(
    account_name: str,
    account: AccountConfig,
    config: Annotated[ConfigManager, Depends(get_config_manager)],
    _: Annotated[dict, Depends(require_auth)],
) -> AccountConfigResponse:
    """Update account."""
    existing = config.get_account_config(account_name)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account '{account_name}' not found",
        )

    # Update account in config
    accounts = config.config.get("accounts", [])
    for i, acc in enumerate(accounts):
        if acc.get("name") == account_name:
            accounts[i] = account.model_dump_dict()
            break
    config.config["accounts"] = accounts
    config.save_config()

    return AccountConfigResponse.from_account_config(account)


@router.delete(
    "/accounts/{account_name}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Configuration"],
)
async def delete_account(
    account_name: str,
    config: Annotated[ConfigManager, Depends(get_config_manager)],
    _: Annotated[dict, Depends(require_auth)],
) -> None:
    """Delete account."""
    existing = config.get_account_config(account_name)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account '{account_name}' not found",
        )

    # Remove account from config
    accounts = config.config.get("accounts", [])
    accounts = [acc for acc in accounts if acc.get("name") != account_name]
    config.config["accounts"] = accounts
    config.save_config()


@router.get("/targets", tags=["Configuration"])
async def list_targets(
    config: Annotated[ConfigManager, Depends(get_config_manager)],
    _: Annotated[dict, Depends(require_auth)],
) -> dict[str, Any]:
    """List all targets."""
    targets = [
        TargetConfigResponse.from_dict(tgt) for tgt in config.get_enabled_targets()
    ]
    return {"targets": targets}


@router.post(
    "/targets",
    status_code=status.HTTP_201_CREATED,
    tags=["Configuration"],
)
async def create_target(
    target: TargetConfig,
    config: Annotated[ConfigManager, Depends(get_config_manager)],
    _: Annotated[dict, Depends(require_auth)],
) -> TargetConfigResponse:
    """Create new target."""
    # Check if target already exists
    targets = config.config.get("targets", [])
    for tgt in targets:
        if tgt.get("name") == target.name:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Target '{target.name}' already exists",
            )

    # Add target to config
    targets.append(target.model_dump_dict())
    config.config["targets"] = targets
    config.save_config()

    return TargetConfigResponse.from_target_config(target)


@router.get(
    "/targets/{target_name}",
    tags=["Configuration"],
)
async def get_target(
    target_name: str,
    config: Annotated[ConfigManager, Depends(get_config_manager)],
    _: Annotated[dict, Depends(require_auth)],
) -> TargetConfigResponse:
    """Get target by name."""
    targets = config.config.get("targets", [])
    for tgt in targets:
        if tgt.get("name") == target_name:
            return TargetConfigResponse.from_dict(tgt)

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Target '{target_name}' not found",
    )


@router.put(
    "/targets/{target_name}",
    tags=["Configuration"],
)
async def update_target(
    target_name: str,
    target: TargetConfig,
    config: Annotated[ConfigManager, Depends(get_config_manager)],
    _: Annotated[dict, Depends(require_auth)],
) -> TargetConfigResponse:
    """Update target."""
    targets = config.config.get("targets", [])
    found = False
    for i, tgt in enumerate(targets):
        if tgt.get("name") == target_name:
            targets[i] = target.model_dump_dict()
            found = True
            break

    if not found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target '{target_name}' not found",
        )

    config.config["targets"] = targets
    config.save_config()

    return TargetConfigResponse.from_target_config(target)


@router.delete(
    "/targets/{target_name}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Configuration"],
)
async def delete_target(
    target_name: str,
    config: Annotated[ConfigManager, Depends(get_config_manager)],
    _: Annotated[dict, Depends(require_auth)],
) -> None:
    """Delete target."""
    targets = config.config.get("targets", [])
    original_count = len(targets)
    targets = [tgt for tgt in targets if tgt.get("name") != target_name]

    if len(targets) == original_count:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target '{target_name}' not found",
        )

    config.config["targets"] = targets
    config.save_config()
