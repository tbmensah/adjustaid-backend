#!/usr/bin/env python3
"""
Create a test Auth user via Supabase Admin API, then insert public.users.

Requires in .env:
  - SUPABASE_URL
  - SUPABASE_SERVICE_ROLE_KEY  (Dashboard → API → service_role; server-only)
  - DATABASE_URL

Run from repo root:
  PYTHONPATH=. python scripts/seed_dummy_user.py

Optional env:
  DUMMY_USER_EMAIL   default: dummy+<unix_ts>@example.invalid
  DUMMY_USER_PASSWORD  default: a random strong password printed once
"""

from __future__ import annotations

import os
import secrets
import sys
import uuid
from datetime import UTC, datetime

import httpx
from sqlalchemy.orm import Session, sessionmaker

from app.db.session import get_engine
from app.models import User


def _require(name: str) -> str:
    v = os.environ.get(name)
    if not v:
        print(f"Missing {name} in environment (.env).", file=sys.stderr)
        sys.exit(1)
    return v


def create_auth_user(supabase_url: str, service_role: str, email: str, password: str) -> uuid.UUID:
    base = supabase_url.rstrip("/")
    url = f"{base}/auth/v1/admin/users"
    with httpx.Client(timeout=30.0) as client:
        r = client.post(
            url,
            headers={
                "Authorization": f"Bearer {service_role}",
                "apikey": service_role,
                "Content-Type": "application/json",
            },
            json={
                "email": email,
                "password": password,
                "email_confirm": True,
            },
        )
    if r.status_code >= 400:
        print(r.text, file=sys.stderr)
        if r.status_code == 401:
            print(
                "Use the service_role key from Supabase Dashboard → Project Settings → API (not the anon key).",
                file=sys.stderr,
            )
        r.raise_for_status()
    data = r.json()
    uid = data.get("id")
    if not uid:
        print("Unexpected response from admin API:", data, file=sys.stderr)
        sys.exit(1)
    return uuid.UUID(uid)


def main() -> None:
    # Load .env via pydantic-settings (same as the app)
    from app.core.config import get_settings

    get_settings.cache_clear()
    s = get_settings()

    supabase_url = s.supabase_url or _require("SUPABASE_URL")
    service_role = s.supabase_service_role_key or _require("SUPABASE_SERVICE_ROLE_KEY")
    if not s.database_url:
        _require("DATABASE_URL")

    ts = int(datetime.now(UTC).timestamp())
    email = os.environ.get("DUMMY_USER_EMAIL", f"dummy+{ts}@example.invalid")
    password = os.environ.get("DUMMY_USER_PASSWORD") or secrets.token_urlsafe(16)

    print(f"Creating auth user: {email}")
    auth_id = create_auth_user(supabase_url, service_role, email, password)

    SessionLocal = sessionmaker(autoflush=False, autocommit=False, expire_on_commit=False, bind=get_engine())
    db: Session = SessionLocal()
    try:
        row = User(
            auth_id=auth_id,
            email=email,
            full_name="Dummy User",
            company="AdjustAid Test",
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        print("public.users row created.")
        print(f"  id (app user):     {row.id}")
        print(f"  auth_id (sub):    {row.auth_id}")
        print(f"  email:             {row.email}")
        print(f"  password (save):   {password}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
