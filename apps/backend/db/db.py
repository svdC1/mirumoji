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
from db.Tables import (profiles,
                       gpt_templates,
                       profile_files,
                       profile_transcripts,
                       clips
                       )
from typing import Any, Dict
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


class DbManager:
    """
    Implements async CRUD operations for the mirumoji database.

    Attributes:
      TABLES (dict): Dictionary mapping string table names to their
                     `SQAlchemy Table` object
    """

    TABLES = {
        "profiles": profiles,
        "gpt_templates": gpt_templates,
        "profile_transcripts": profile_transcripts,
        "profile_files": profile_files,
        "clips": clips
    }

    def __init__(self):
        self.table_names = __class__.TABLES.keys()

    def _map_table(self, table_name: str) -> Any:
        """
        Maps a `table_name` string to it's `SQLAlchemy Table` object

        Args:
          table_name (str): String of table's name

        Returns:
          Table: `SQLAlchemy Table` object

        Raises:
          ValueError: If `table_name` doesn't exist in database

        """
        try:
            return self.TABLES[table_name]
        except KeyError:
            raise ValueError("Table doesn't exist in database")

    async def _column_value_filter(self,
                                   table_name: str,
                                   filter_dict: Dict[str, Any],
                                   extend_query: bool = False,
                                   raw_q: Any = None
                                   ) -> Any:
        """
        Return table records in which columns `filter_dict.keys` have value of
        `filter_dict.value`

        Args:
          table_name (str): String of table's name
          filter_dict (Dict[str, Any]): Dictionary of `column` - `values`
                                        to filter
          extend_query (bool, optional): If True, extend query `q` with
                                         filters, otherwhise return execution
                                         result. Defaults to `False`
          raw_q (Any, optional): Query to extend if `extend_query` is `True`.
                                 Defaults to `None`

        Returns:
          Any: Result of `databases.fetch_all` on filter query
        """
        tbl = self._map_table(table_name)
        q = (tbl
             .select()
             )
        for col, val in filter_dict.items():
            q = (q
                 .where(tbl.c[col] == val)
                 )
        if extend_query:
            ext_q = raw_q
            for col, val in filter_dict.items():
                ext_q = (ext_q
                         .where(tbl.c[col] == val)
                         )
            return ext_q

        db = await get_db()
        return await db.fetch_all(q)

    async def update(self,
                     table_name: str,
                     filter_dict: Dict[str, Any],
                     values: dict
                     ) -> Any:
        """
        Update row where columns `filter_dict.key` have value
        `filter_dict.value`, in table `table_name` with values `values`

        Args:
          table_name (str): Table name to update
          filter_dict (Dict[str, Any]): Dictionary of `column` - `values`
                                        to filter
          values (dict): New row values

        Returns:
          Any: Return result of `databases.execute`
        """
        tbl = self._map_table(table_name)
        q = (tbl
             .update()
             )
        q = await self._column_value_filter(table_name,
                                            filter_dict,
                                            extend_query=True,
                                            raw_q=q
                                            )
        q = q.values(**values)
        db = await get_db()
        return await db.execute(q)

    async def create(self,
                     table_name: str,
                     values: dict
                     ) -> Any:
        """
        Create row with values `values` in table `table_name`

        Args:
          table_name (str): Table in which to create row
          values (dict): Row values

        Returns:
          Any: Return result of `databases.execute`
        """
        tbl = self._map_table(table_name)
        q = (tbl
             .insert()
             .values(**values)
             )
        db = await get_db()
        return await db.execute(q)

    async def delete(self,
                     table_name: str,
                     filter_dict: Dict[str, Any]
                     ) -> Any:
        """
        Delete row where column `filter_dict.key` has value
        `filter_dict.value`, in table `table_name`

        Args:
          table_name (str): Table name to update
          filter_dict (Dict[str, Any]): Dictionary of `column` - `values`
                                        to filter

        Returns:
          Any: Return result of `databases.execute`
        """
        tbl = self._map_table(table_name)
        q = (tbl
             .delete()
             )
        q = await self._column_value_filter(table_name,
                                            filter_dict,
                                            extend_query=True,
                                            raw_q=q
                                            )
        db = await get_db()
        return await db.execute(q)

    async def read(self,
                   table_name: str,
                   filter_dict: Dict[str, Any],
                   fetch_one: bool = False
                   ) -> Any:
        """
        Select all rows where column `filter_dict.key` has value
        `filter_dict.value`, in table `table_name`

        Args:
          table_name (str): Table name to update
          filter_dict (Dict[str, Any]): Dictionary of `column` - `values`
                                        to filter
          fetch_one (bool, optional): If True, fetch only one result
                                      otherwise fetch all. Defaults to False

        Returns:
          Any: Result of `databases.fetch_all` on filter query
        """
        if fetch_one:
            tbl = self._map_table(table_name)
            q = (tbl
                 .select()
                 )
            q = await self._column_value_filter(table_name,
                                                filter_dict,
                                                extend_query=True,
                                                raw_q=q
                                                )
            db = await get_db()
            return await db.fetch_one(q)

        return await self._column_value_filter(table_name, filter_dict)
