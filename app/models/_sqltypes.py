from enum import StrEnum

from sqlalchemy import Enum as SAEnum


def pg_enum(enum_cls: type[StrEnum], name: str) -> SAEnum:
    """Map to an existing PostgreSQL enum type (managed by Supabase migrations)."""
    return SAEnum(
        enum_cls,
        name=name,
        native_enum=True,
        create_type=False,
        values_callable=lambda obj: [m.value for m in obj],
    )
