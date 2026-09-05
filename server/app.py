import json
import os
import sqlite3
import subprocess
from datetime import date
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
DB_PATH = os.path.join(BASE_DIR, "dictionary.db")
DATA_JSON_PATH = os.path.join(PROJECT_DIR, "webpage", "data.json")
ADMIN_DIR = os.path.join(PROJECT_DIR, "admin")

app = FastAPI(title="Tulu Dictionary Admin")


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS words (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            kannada     TEXT NOT NULL,
            tulu        TEXT NOT NULL,
            english     TEXT NOT NULL,
            date_added  TEXT NOT NULL,
            tags        TEXT NOT NULL DEFAULT '[]',
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()

    # Seed from webpage/data.json if the table is empty
    count = conn.execute("SELECT COUNT(*) FROM words").fetchone()[0]
    if count == 0 and os.path.exists(DATA_JSON_PATH):
        with open(DATA_JSON_PATH, "r", encoding="utf-8") as f:
            words = json.load(f)
        for w in words:
            tulu = json.dumps(w["tulu"], ensure_ascii=False)
            tags = json.dumps(w.get("tags", []), ensure_ascii=False)
            conn.execute(
                "INSERT INTO words (kannada, tulu, english, date_added, tags) VALUES (?, ?, ?, ?, ?)",
                (w["kannada"], tulu, w["english"], w["date_added"], tags),
            )
        conn.commit()
        print(f"Seeded {len(words)} words from data.json")

    conn.close()


def row_to_dict(r):
    return {
        "id":         r["id"],
        "kannada":    r["kannada"],
        "tulu":       json.loads(r["tulu"]),
        "english":    r["english"],
        "date_added": r["date_added"],
        "tags":       json.loads(r["tags"]),
        "created_at": r["created_at"],
        "updated_at": r["updated_at"],
    }


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class WordIn(BaseModel):
    kannada:    str
    tulu:       list[str]
    english:    str
    date_added: str | None = None
    tags:       list[str] = []


# ---------------------------------------------------------------------------
# Serve admin UI
# ---------------------------------------------------------------------------

@app.get("/", include_in_schema=False)
@app.get("/admin", include_in_schema=False)
def admin_ui():
    return FileResponse(os.path.join(ADMIN_DIR, "index.html"))

app.mount("/admin/static", StaticFiles(directory=ADMIN_DIR), name="admin_static")


# ---------------------------------------------------------------------------
# API — words
# ---------------------------------------------------------------------------

@app.get("/api/words")
def get_words():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM words ORDER BY date_added DESC, id DESC"
    ).fetchall()
    conn.close()
    return [row_to_dict(r) for r in rows]


@app.post("/api/words", status_code=201)
def add_word(word: WordIn):
    kannada    = word.kannada.strip()
    tulu       = json.dumps([t.strip() for t in word.tulu], ensure_ascii=False)
    english    = word.english.strip()
    date_added = word.date_added or date.today().isoformat()
    tags       = json.dumps([t.strip() for t in word.tags], ensure_ascii=False)

    conn = get_db()
    cur = conn.execute(
        "INSERT INTO words (kannada, tulu, english, date_added, tags) VALUES (?, ?, ?, ?, ?)",
        (kannada, tulu, english, date_added, tags),
    )
    word_id = cur.lastrowid
    conn.commit()
    created = conn.execute("SELECT * FROM words WHERE id = ?", (word_id,)).fetchone()
    conn.close()
    export_json()
    return row_to_dict(created)


@app.put("/api/words/{word_id}")
def update_word(word_id: int, word: WordIn):
    conn = get_db()
    old = conn.execute("SELECT * FROM words WHERE id = ?", (word_id,)).fetchone()
    if not old:
        conn.close()
        raise HTTPException(status_code=404, detail="Word not found")

    kannada    = word.kannada.strip() if word.kannada else old["kannada"]
    tulu       = json.dumps([t.strip() for t in word.tulu], ensure_ascii=False)
    english    = word.english.strip() if word.english else old["english"]
    date_added = word.date_added or old["date_added"]
    tags       = json.dumps([t.strip() for t in word.tags], ensure_ascii=False)

    conn.execute(
        "UPDATE words SET kannada=?, tulu=?, english=?, date_added=?, tags=?, "
        "updated_at=CURRENT_TIMESTAMP WHERE id=?",
        (kannada, tulu, english, date_added, tags, word_id),
    )
    conn.commit()
    updated = conn.execute("SELECT * FROM words WHERE id = ?", (word_id,)).fetchone()
    conn.close()
    export_json()
    return row_to_dict(updated)


@app.delete("/api/words/{word_id}")
def delete_word(word_id: int):
    conn = get_db()
    word = conn.execute("SELECT * FROM words WHERE id = ?", (word_id,)).fetchone()
    if not word:
        conn.close()
        raise HTTPException(status_code=404, detail="Word not found")

    conn.execute("DELETE FROM words WHERE id = ?", (word_id,))
    conn.commit()
    conn.close()
    export_json()
    return {"success": True}


# ---------------------------------------------------------------------------
# Export / publish
# ---------------------------------------------------------------------------

@app.post("/api/export")
def export_json():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM words ORDER BY date_added ASC, id ASC"
    ).fetchall()
    conn.close()

    words = [{
        "kannada":    r["kannada"],
        "tulu":       json.loads(r["tulu"]),
        "english":    r["english"],
        "date_added": r["date_added"],
        "tags":       json.loads(r["tags"]),
    } for r in rows]

    with open(DATA_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(words, f, ensure_ascii=False, indent=4)

    return {"success": True, "count": len(words)}


@app.post("/api/publish")
def publish():
    export_json()

    def run(cmd):
        return subprocess.run(
            cmd, capture_output=True, text=True, cwd=PROJECT_DIR
        )

    steps = [
        ["git", "add", "webpage/data.json"],
        ["git", "add", "server/dictionary.db"],
        ["git", "commit", "-m", "feat(data): more words"],
        ["git", "push", "origin", "main"],
    ]

    output_lines = []
    for cmd in steps:
        result = run(cmd)
        output_lines.append((result.stdout + result.stderr).strip())
        if result.returncode != 0:
            return {
                "success": False,
                "output":  "\n".join(output_lines).strip(),
            }

    return {
        "success": True,
        "output":  "\n".join(output_lines).strip(),
    }


# ---------------------------------------------------------------------------

init_db()
