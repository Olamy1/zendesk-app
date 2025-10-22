# =================================================================================================
# File: backend/models/user_schema.py
# Description:
#   User schema definitions for API responses in the OAPS Zendesk App (v2.1+)
#
# Purpose:
#   Defines a structured representation of Zendesk users or agents as used
#   by the frontend (dropdowns, ticket assignment views, and analytics).
#
# Notes:
#   - Mirrors a subset of the Zendesk User object, limiting to essential fields.
#   - Ensures data consistency when passing user data between frontend and backend.
#
# Author: Olivier Lamy
# Version: 2.1.0 | October 2025
# =================================================================================================

from typing import Optional
from pydantic import BaseModel, Field


class User(BaseModel):
    """
    Represents a Zendesk user or agent for internal API use.

    Attributes:
        id (int): Unique user identifier from Zendesk.
        name (str): Full display name of the user.
        email (Optional[str]): Primary email address.
        role (Optional[str]): Zendesk-defined role (e.g., agent, admin, end-user).
        group_id (Optional[int]): Associated Zendesk group ID (used for routing and assignments).
        active (Optional[bool]): Whether the user account is active.
    """

    id: int = Field(..., description="Unique Zendesk user ID")
    name: str = Field(..., description="User's full display name")
    email: Optional[str] = Field(None, description="User's email address")
    role: Optional[str] = Field(None, description="User's Zendesk role")
    group_id: Optional[int] = Field(None, description="Group ID associated with the user")
    active: Optional[bool] = Field(True, description="Whether this user is active in Zendesk")
