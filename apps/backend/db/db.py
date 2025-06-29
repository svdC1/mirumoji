"""
This module defines helper functions to create / connect with the Mirumoji
database.

Attributes:
  DATABASE_URL (str): `SQLite` database URL.
  METADATA (MetaData): `sqlachemy` `MetaData` object for database.
  database (Database): `Database` object.
  engine (Engine): `SQLAlchemy` `Engine` object for database
"""

import os
from databases import Database
from sqlalchemy import create_engine
from db.Tables import METADATA
from db.Tables import (gpt_templates)
from pathlib import Path

# Check if Data Folder exists
project_root = Path(__file__).resolve().parent.parent
path_data = project_root / "data"
path_data.mkdir(parents=True, exist_ok=True)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/mirumoji.db")
database = Database(DATABASE_URL)
METADATA = METADATA
engine = create_engine(DATABASE_URL)
METADATA.create_all(engine)


async def get_db() -> Database:
    """
    Get the Database object.

    Returns:
      Database: `Database` object
    """
    return database


async def connect_db() -> None:
    """
    Wrapper for `Database.connect`
    """
    await database.connect()


async def disconnect_db() -> None:
    """
    Wrapper for `Database.disconnect`
    """
    await database.disconnect()


async def get_gpt_template_db(profile_id: str):
    """
    Query the database to find the GPT template of a specific profile.

    Args:
      profile_id (str): The profile to get the GPT Template for.

    Returns:
      Record: The database record.
    """
    q = gpt_templates.select().where(gpt_templates.c.profile_id == profile_id)
    return await database.fetch_one(q)
