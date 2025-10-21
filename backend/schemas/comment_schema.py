# =================================================================================================
# File: backend/models/comment_schema.py
# Description:
#   Comment schema definitions for API requests in the OAPS Zendesk App (v2.0+)
#
# Purpose:
#   Defines the structure of comments added to Zendesk tickets from within
#   the OAPS Zendesk App interface (public or internal notes).
#
# Notes:
#   - Ensures clean serialization when submitting new comments.
#   - Supports internal note handling and author attribution.
#
# Author: Olivier Lamy
# Version: 2.0.0 | October 2025
# =================================================================================================

from typing import Optional
from pydantic import BaseModel, Field


class Comment(BaseModel):
    """
    Represents a comment payload for Zendesk ticket updates.

    Attributes:
        author_id (Optional[int]): ID of the user adding the comment (None if system-generated).
        body (str): The content of the comment.
        is_public (bool): Visibility flag — True for requester-visible, False for internal notes.
    """

    author_id: Optional[int] = Field(None, description="Author ID (or None for system comments)")
    body: str = Field(..., description="Comment text body")
    is_public: bool = Field(..., description="True if comment is visible to requester, else internal")
