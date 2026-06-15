"""
memory/student_memory.py

Tracks and persists student performance across sessions.
Uses SQLite for storage. Records completed cases, scores,
weak topics, and tailors future case selection.

In v1, this module provides an in-memory store as a stub
that will be backed by SQLite once the schema is finalised.
"""

import json
import os
import sqlite3
from datetime import datetime
from typing import Optional


DB_PATH = os.path.join(os.path.dirname(__file__), "..", "student_data.db")


class StudentMemory:
    """
    Persistent store for student learning history.

    Usage:
        memory = StudentMemory("student_123")
        memory.save_case(...)
        profile = memory.get_profile()
    """

    def __init__(self, student_id: str = "default"):
        self.student_id = student_id
        self._init_db()

    # ------------------------------------------------------------------
    #  Internal helpers
    # ------------------------------------------------------------------
    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Create tables if they do not exist."""
        with self._get_connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS cases (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id  TEXT NOT NULL,
                    specialty   TEXT,
                    difficulty  TEXT,
                    score       INTEGER,
                    diagnosis   TEXT,
                    feedback    TEXT,
                    completed_at TEXT
                );

                CREATE TABLE IF NOT EXISTS weak_topics (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id  TEXT NOT NULL,
                    topic       TEXT NOT NULL,
                    count       INTEGER DEFAULT 1,
                    UNIQUE(student_id, topic)
                );
                """
            )

    # ------------------------------------------------------------------
    #  Public API
    # ------------------------------------------------------------------
    def save_case(
        self,
        specialty: str,
        difficulty: str,
        score: int,
        diagnosis: str,
        feedback: dict,
    ) -> None:
        """
        Record a completed case in the database.
        """
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO cases (student_id, specialty, difficulty, score, diagnosis, feedback, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    self.student_id,
                    specialty,
                    difficulty,
                    score,
                    diagnosis,
                    json.dumps(feedback),
                    datetime.utcnow().isoformat(),
                ),
            )

            missed = feedback.get("missed_items", [])
            for topic in missed:
                conn.execute(
                    """
                    INSERT INTO weak_topics (student_id, topic, count)
                    VALUES (?, ?, 1)
                    ON CONFLICT(student_id, topic) DO UPDATE SET count = count + 1
                    """,
                    (self.student_id, topic.lower()),
                )

    def get_profile(self) -> dict:
        """
        Return a summary of the student's performance.
        """
        with self._get_connection() as conn:
            row = conn.execute(
                """
                SELECT
                    COUNT(*)                                     AS total_cases,
                    ROUND(AVG(score), 1)                         AS avg_score,
                    COALESCE(MIN(score), 0)                      AS min_score,
                    COALESCE(MAX(score), 0)                      AS max_score
                FROM cases
                WHERE student_id = ?
                """,
                (self.student_id,),
            ).fetchone()

            weak = conn.execute(
                """
                SELECT topic, count
                FROM weak_topics
                WHERE student_id = ?
                ORDER BY count DESC
                LIMIT 5
                """,
                (self.student_id,),
            ).fetchall()

        return {
            "total_cases": row["total_cases"],
            "average_score": row["avg_score"],
            "min_score": row["min_score"],
            "max_score": row["max_score"],
            "weak_topics": [{"topic": r["topic"], "count": r["count"]} for r in weak],
        }

    def get_weak_topics(self) -> list[str]:
        """Return topic names the student struggles with most."""
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT topic FROM weak_topics
                WHERE student_id = ?
                ORDER BY count DESC
                """,
                (self.student_id,),
            ).fetchall()
        return [r["topic"] for r in rows]
