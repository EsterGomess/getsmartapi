""" Services package initialization file."""
from app.services.auth import authenticate_api_client, authenticate_user
from app.services.user import (
    register_user,
    login_user,
    change_user_email,
    request_password_reset,
    reset_user_password
)
from app.services.note import (
    create_note_for_user,
    get_note_for_user,
    get_notes_paginated_by_user,
    list_notes_by_user,
    update_note_for_user,
    delete_note_for_user,
    get_note_graph
)
from app.services.notes_ai import suggest_connections

__all__ = [
    "authenticate_api_client",
    "authenticate_user",
    "register_user",
    "login_user",
    "reset_user_password",
    "create_note_for_user",
    "get_note_for_user",
    "get_notes_paginated_by_user",
    "list_notes_by_user",
    "update_note_for_user",
    "delete_note_for_user",
    "get_note_graph",
    "suggest_connections",
    "request_password_reset",
    "change_user_email"
]
