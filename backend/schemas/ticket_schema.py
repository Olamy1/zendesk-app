# =================================================================================================
# File: backend/models/ticket_schema.py
# Description:
#   Ticket schema definitions for API requests and responses in the OAPS Zendesk App (v2.1+)
#
# Purpose:
#   Defines the structure of Zendesk ticket data exchanged between backend and frontend.
#   Used for listing, updating, and exporting tickets in real time.
#
# Notes:
#   - Mirrors core Zendesk Ticket fields used by OAPS dashboards and exports.
#   - Adds optional business fields used for analytics (meeting window, follow-up status).
#
# Author: Olivier Lamy
# Version: 2.1.0 | October 2025
# =================================================================================================

from typing import Optional
from pydantic import BaseModel, Field


class Ticket(BaseModel):
    """
    Represents a Zendesk ticket record exposed through API endpoints.

    Attributes:
        id (int): Unique Zendesk ticket identifier.
        subject (str): Ticket subject line.
        status (str): Current Zendesk ticket status (e.g., open, pending, solved).
        priority (Optional[str]): Priority level (e.g., high, urgent).
        assignee_id (Optional[int]): ID of the user assigned to the ticket.
        group_id (Optional[int]): Zendesk group ID responsible for the ticket.
        updated_at (Optional[str]): Timestamp of the most recent ticket update (ISO 8601).
        resolved_at (Optional[str]): Time when ticket was marked solved/closed.
        follow_up_status (Optional[str]): Derived field for compliance reporting.
        meeting_window (Optional[str]): Current reporting or meeting window bucket.
    """

    id: int = Field(..., description="Unique Zendesk ticket ID")
    subject: str = Field(..., description="Ticket subject line")
    status: str = Field(..., description="Current status of the ticket")
    priority: Optional[str] = Field(None, description="Priority level (low, normal, high, urgent)")
    assignee_id: Optional[int] = Field(None, description="Assigned user ID")
    group_id: Optional[int] = Field(None, description="Associated group ID")
    updated_at: Optional[str] = Field(None, description="Last updated timestamp (ISO 8601 format)")
    resolved_at: Optional[str] = Field(None, description="Timestamp when ticket was solved/closed")
    follow_up_status: Optional[str] = Field(None, description="Derived follow-up or compliance flag")
    meeting_window: Optional[str] = Field(None, description="Associated reporting window label")
