"""Tests for the authentication service functions."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.core.security import get_password_hash
from app.models import APIClient, User
from app.services import auth


@pytest.mark.parametrize(
    ("function_name", "crud_name"),
    [
        ("authenticate_api_client", "get_api_client_by_username"),
        ("authenticate_user", "get_user_by_username"),
    ],
)
class TestAuthenticate:
    @pytest.mark.asyncio
    async def test_returns_entity_for_valid_password(self, function_name, crud_name):
        stored = SimpleNamespace(hashed_password="stored hash")
        db = object()

        with (
            patch.object(auth, crud_name, new=AsyncMock(return_value=stored)) as lookup,
            patch.object(auth, "verify_password", return_value=True) as verify,
        ):
            result = await getattr(auth, function_name)(db, "alice", "correct")

        assert result is stored
        lookup.assert_awaited_once_with(db=db, username="alice")
        verify.assert_called_once_with("correct", "stored hash")

    @pytest.mark.asyncio
    async def test_returns_none_when_entity_does_not_exist(self, function_name, crud_name):
        with (
            patch.object(auth, crud_name, new=AsyncMock(return_value=None)) as lookup,
            patch.object(auth, "verify_password") as verify,
        ):
            result = await getattr(auth, function_name)(object(), "missing", "pw")

        assert result is None
        lookup.assert_awaited_once()
        verify.assert_not_called()

    @pytest.mark.asyncio
    async def test_returns_none_for_invalid_password(self, function_name, crud_name):
        stored = SimpleNamespace(hashed_password="stored hash")

        with (
            patch.object(auth, crud_name, new=AsyncMock(return_value=stored)),
            patch.object(auth, "verify_password", return_value=False) as verify,
        ):
            result = await getattr(auth, function_name)(object(), "alice", "wrong")

        assert result is None
        verify.assert_called_once_with("wrong", "stored hash")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("function", "model"),
    [
        (auth.authenticate_api_client, APIClient),
        (auth.authenticate_user, User),
    ],
)
async def test_authenticates_with_a_real_password_hash(db, function, model):
    password = "correct horse battery staple"
    entity = model(
        username="alice",
        email="alice@example.com",
        hashed_password=get_password_hash(password),
    )
    db.add(entity)
    await db.commit()

    result = await function(db, "alice", password)

    assert result is not None
    assert result.username == "alice"
