"""
Base Pydantic schema configuration.

All application schemas inherit from ``BaseSchema`` to ensure a consistent
serialisation behaviour, most notably ``from_attributes=True`` which enables
ORM-model-to-schema conversion (previously ``orm_mode`` in Pydantic v1).
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """
    Base schema for all Pydantic models in this application.

    Configuration:
    - ``from_attributes``: Enables initialisation from ORM model attributes.
    - ``populate_by_name``: Allows field population via field name or alias.
    - ``use_enum_values``: Serialises enum members as their values.
    """

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True,
        str_strip_whitespace=True,
    )


class TimestampSchema(BaseSchema):
    """
    Mixin schema that includes audit timestamp fields.

    Extend this instead of ``BaseSchema`` when the corresponding ORM model
    inherits from ``TimestampMixin``.
    """

    created_at: datetime
    updated_at: datetime
