"""
Database operations test suite.
Run: python tests/db/test.py

Zero external dependencies - uses only stdlib unittest + sqlite3.
"""
import __future__

import base64
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

# --- Ditto-compatible schema ---
SCHEMA_MAIN = (
    "CREATE TABLE Main("
    "lID INTEGER PRIMARY KEY AUTOINCREMENT, "
    "lDate INTEGER, mText TEXT, lShortCut INTEGER, "
    "lDontAutoDelete INTEGER, CRC INTEGER, bIsGroup INTEGER, "
    "lParentID INTEGER, QuickPasteText TEXT, clipOrder REAL, "
    "clipGroupOrder REAL, globalShortCut INTEGER, lastPasteDate INTEGER, "
    "stickyClipOrder REAL, stickyClipGroupOrder REAL, "
    "MoveToGroupShortCut INTEGER, GlobalMoveToGroupShortCut INTEGER)"
)
SCHEMA_DATA = (
    "CREATE TABLE Data("
    "lID INTEGER PRIMARY KEY AUTOINCREMENT, "
    "lParentID INTEGER, strClipBoardFormat TEXT, ooData BLOB)"
)
SCHEMA_DELETES = "CREATE TABLE MainDeletes(clipID INTEGER, modifiedDate)"

INDEXES = [
    "CREATE UNIQUE INDEX Main_ID on Main(lID ASC)",
    "CREATE UNIQUE INDEX Data_ID on Data(lID ASC)",
    "CREATE INDEX Main_ParentId on Main(lParentID DESC)",
    "CREATE INDEX Main_IsGroup on Main(bIsGroup DESC)",
    "CREATE INDEX Main_CRC on Main(CRC ASC)",
]


def create_test_db() -> sqlite3.Connection:
    """Create an in-memory Ditto-compatible DB."""
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(SCHEMA_MAIN)
    conn.execute(SCHEMA_DATA)
    conn.execute(SCHEMA_DELETES)
    for idx in INDEXES:
        conn.execute(idx)
    conn.commit()
    return conn


def insert_test_clip(conn, mtext, lDate, bIsGroup=0, lParentID=-1, CRC=None):
    """Helper: insert a clip row directly into Main."""
    conn.execute(
        "INSERT INTO Main (lDate, mText, bIsGroup, lParentID, CRC) VALUES (?, ?, ?, ?, ?)",
        (lDate, mtext, bIsGroup, lParentID, CRC),
    )
    return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def insert_test_data(conn, lParentID, fmt, data):
    """Helper: insert a data row."""
    conn.execute(
        "INSERT INTO Data (lParentID, strClipBoardFormat, ooData) VALUES (?, ?, ?)",
        (lParentID, fmt, data),
    )


# --- Import target ---
from vditto.db import (
    open_db,
    save_clip,
    update_clip_date,
    find_by_crc,
    load_recent,
    load_clip_data,
    search_clips,
    create_group,
    delete_group,
    move_to_group,
)


class TestDB(unittest.TestCase):
    """Test database operations against in-memory Ditto-compatible DB."""

    def setUp(self):
        self.conn = create_test_db()

    def tearDown(self):
        self.conn.close()

    # ---- save_clip ----

    def test_save_clip_text_normal(self):
        data = b"Hello World"
        lid = save_clip(self.conn, "Hello World", "text", data)
        self.assertIsNotNone(lid)

        row = self.conn.execute("SELECT mText, bIsGroup FROM Main WHERE lID=?", (lid,)).fetchone()
        self.assertEqual(row[0], "Hello World")
        self.assertEqual(row[1], 0)

        drow = self.conn.execute(
            "SELECT strClipBoardFormat FROM Data WHERE lParentID=?", (lid,)
        ).fetchone()
        self.assertEqual(drow[0], "CF_UNICODETEXT")

    def test_save_clip_image_normal(self):
        lid = save_clip(self.conn, "[image]", "image", b"\x00\x00\x00\x00")
        row = self.conn.execute("SELECT mText FROM Main WHERE lID=?", (lid,)).fetchone()
        self.assertEqual(row[0], "[image]")

        drow = self.conn.execute(
            "SELECT strClipBoardFormat FROM Data WHERE lParentID=?", (lid,)
        ).fetchone()
        self.assertEqual(drow[0], "CF_DIB")

    def test_save_clip_duplicate_crc(self):
        data = b"duplicate text"
        lid1 = save_clip(self.conn, "duplicate text", "text", data)
        lid2 = save_clip(self.conn, "duplicate text", "text", data)
        self.assertEqual(lid1, lid2, "Duplicate should return same lID, not create new")

        count = self.conn.execute("SELECT COUNT(*) FROM Main WHERE bIsGroup=0").fetchone()[0]
        self.assertEqual(count, 1)

    def test_save_clip_empty_text(self):
        lid = save_clip(self.conn, "", "text", b"")
        self.assertIsNotNone(lid)
        count = self.conn.execute("SELECT COUNT(*) FROM Main").fetchone()[0]
        self.assertEqual(count, 1)

    # ---- load_recent ----

    def test_load_recent_normal(self):
        insert_test_clip(self.conn, "first", 100)
        insert_test_clip(self.conn, "second", 200)
        insert_test_clip(self.conn, "third", 300)

        results = load_recent(self.conn, 10)
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]["mText"], "third")
        self.assertEqual(results[1]["mText"], "second")
        self.assertEqual(results[2]["mText"], "first")

    def test_load_recent_excludes_groups(self):
        insert_test_clip(self.conn, "clip1", 100, bIsGroup=0)
        insert_test_clip(self.conn, "group1", 0, bIsGroup=1)

        results = load_recent(self.conn, 10)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["mText"], "clip1")

    def test_load_recent_limit(self):
        insert_test_clip(self.conn, "a", 100)
        insert_test_clip(self.conn, "b", 200)
        insert_test_clip(self.conn, "c", 300)

        results = load_recent(self.conn, 2)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["mText"], "c")
        self.assertEqual(results[1]["mText"], "b")

    # ---- load_clip_data ----

    def test_load_clip_data_normal(self):
        lid = insert_test_clip(self.conn, "multi-format", 100)
        insert_test_data(self.conn, lid, "CF_UNICODETEXT", b"text data")
        insert_test_data(self.conn, lid, "CF_TEXT", b"text data")

        results = load_clip_data(self.conn, lid)
        self.assertEqual(len(results), 2)
        formats = [r["strClipBoardFormat"] for r in results]
        self.assertIn("CF_UNICODETEXT", formats)
        self.assertIn("CF_TEXT", formats)

    def test_load_clip_data_not_found(self):
        results = load_clip_data(self.conn, 99999)
        self.assertEqual(len(results), 0)

    # ---- search_clips ----

    def test_search_like_match(self):
        insert_test_clip(self.conn, "hello world", 100)
        insert_test_clip(self.conn, "goodbye world", 200)

        results = search_clips(self.conn, "hello", "like")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["mText"], "hello world")

    def test_search_like_no_match(self):
        insert_test_clip(self.conn, "hello", 100)
        results = search_clips(self.conn, "xyz", "like")
        self.assertEqual(len(results), 0)

    def test_search_regex_match(self):
        insert_test_clip(self.conn, "test123", 100)
        insert_test_clip(self.conn, "no digits", 200)

        results = search_clips(self.conn, r"\d+", "regex")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["mText"], "test123")

    def test_search_empty_keyword(self):
        insert_test_clip(self.conn, "hello", 100)
        results = search_clips(self.conn, "", "like")
        self.assertEqual(len(results), 1)

    # ---- create_group ----

    def test_create_group_root(self):
        gid = create_group(self.conn, "My Group", -1)
        row = self.conn.execute(
            "SELECT bIsGroup, mText, lParentID FROM Main WHERE lID=?", (gid,)
        ).fetchone()
        self.assertEqual(row[0], 1)
        self.assertEqual(row[1], "My Group")
        self.assertEqual(row[2], -1)

    def test_create_group_subgroup(self):
        parent_id = create_group(self.conn, "Parent Group", -1)
        child_id = create_group(self.conn, "Child Group", parent_id)

        row = self.conn.execute(
            "SELECT bIsGroup, mText, lParentID FROM Main WHERE lID=?", (child_id,)
        ).fetchone()
        self.assertEqual(row[0], 1)
        self.assertEqual(row[1], "Child Group")
        self.assertEqual(row[2], parent_id)

    # ---- delete_group ----

    def test_delete_group_empty(self):
        gid = create_group(self.conn, "ToDelete", -1)
        delete_group(self.conn, gid)

        count = self.conn.execute("SELECT COUNT(*) FROM Main WHERE lID=?", (gid,)).fetchone()[0]
        self.assertEqual(count, 0)

    def test_delete_group_non_empty(self):
        gid = create_group(self.conn, "HasClips", -1)
        insert_test_clip(self.conn, "clip in group", 100, lParentID=gid)

        with self.assertRaises(Exception):
            delete_group(self.conn, gid)

    # ---- move_to_group ----

    def test_move_to_group_normal(self):
        clip_id = insert_test_clip(self.conn, "move me", 100)
        gid = create_group(self.conn, "Target Group", -1)

        move_to_group(self.conn, clip_id, gid)
        row = self.conn.execute(
            "SELECT lParentID FROM Main WHERE lID=?", (clip_id,)
        ).fetchone()
        self.assertEqual(row[0], gid)

    def test_move_to_group_root(self):
        gid = create_group(self.conn, "TempGroup", -1)
        clip_id = insert_test_clip(self.conn, "unroot me", 100, lParentID=gid)

        move_to_group(self.conn, clip_id, -1)
        row = self.conn.execute(
            "SELECT lParentID FROM Main WHERE lID=?", (clip_id,)
        ).fetchone()
        self.assertEqual(row[0], -1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
