# sqlite_memory.py
import sqlite3
from datetime import datetime
import hashlib
from typing import List, Dict, Tuple, Optional

class SQLiteAutoSummaryMemory:
    def __init__(self, db_path: str, summarizer_fn, max_turns: int = 6):
        self.db_path = db_path
        self.summarizer_fn = summarizer_fn
        self.max_turns = max_turns
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self._connect()
        c = conn.cursor()

        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                summary TEXT DEFAULT '',
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER,
                role TEXT,
                content TEXT,
                created_at TEXT,
                FOREIGN KEY(conversation_id) REFERENCES conversations(id)
            )
        """)
        conn.commit()
        conn.close()
        
    def register_user(self, username: str, password: str) -> bool:
        try:
            conn = self._connect()
            c = conn.cursor()
            hashed_pw = hashlib.sha256(password.encode()).hexdigest()
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_pw))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False

    def authenticate_user(self, username: str, password: str) -> Optional[int]:
        conn = self._connect()
        c = conn.cursor()
        hashed_pw = hashlib.sha256(password.encode()).hexdigest()
        c.execute("SELECT id FROM users WHERE username=? AND password=?", (username, hashed_pw))
        row = c.fetchone()
        conn.close()
        return row["id"] if row else None
    
    def create_conversation(self, user_id: int, title: str = '') -> int:
        conn = self._connect()
        c = conn.cursor()
        c.execute(
            "INSERT INTO conversations (user_id, summary) VALUES (?, ?)",
            (user_id, title)
        )
        conv_id = c.lastrowid
        conn.commit()
        conn.close()
        return conv_id

    def _get_or_create_conversation(self, user_id: str, title: str = '') -> int:
        conn = self._connect()
        c = conn.cursor()
        c.execute("SELECT id FROM conversations WHERE user_id=?", (user_id,))
        row = c.fetchone()
        if row:
            conv_id = row["id"]
        else:
            c.execute("INSERT INTO conversations (user_id, summary) VALUES (?, ?)", (user_id, title))
            conv_id = c.lastrowid
            conn.commit()
        conn.close()
        return conv_id

    def add_message(self, user_id: str, role: str, content: str, conversation_id: int = None):
        if conversation_id is None:
            conv_id = self._get_or_create_conversation(user_id)
        else:
            conv_id = conversation_id
        
        conn = self._connect()
        c = conn.cursor()
        c.execute("""
            INSERT INTO messages (conversation_id, role, content, created_at)
            VALUES (?, ?, ?, ?)
        """, (conv_id, role, content, datetime.utcnow().isoformat()))
        conn.commit()

        # check recent messages count and auto summarize if needed
        c.execute("""
            SELECT COUNT(1) as cnt FROM messages WHERE conversation_id=?
        """, (conv_id,))
        cnt = c.fetchone()["cnt"]
        if cnt >= self.max_turns:
            # call summarizer on context
            self.auto_summarize(conv_id)
        conn.close()

    def auto_summarize(self, conversation_id: int):
        ctx = self.get_context(conversation_id, include_summary=True)
        try:
            summary = self.summarizer_fn(ctx)
            conn = self._connect()
            c = conn.cursor()
            c.execute("UPDATE conversations SET summary=? WHERE id=?", (summary, conversation_id))
            conn.commit()
            conn.close()
        except Exception as e:
            # don't fail whole flow if summarizer fails
            print(f"[Memory] summarizer error: {e}")

    def get_context(self, conversation_id: int, include_summary: bool = True) -> str:
        conn = self._connect()
        c = conn.cursor()
        parts = []
        if include_summary:
            c.execute("SELECT summary FROM conversations WHERE id=?", (conversation_id,))
            row = c.fetchone()
            if row and row["summary"]:
                parts.append(f"[Tóm tắt trước đó]: {row['summary']}\n")
        c.execute("""
            SELECT role, content FROM messages
            WHERE conversation_id=?
            ORDER BY id ASC
        """, (conversation_id,))
        rows = c.fetchall()
        for r in rows:
            parts.append(f"{r['role'].capitalize()}: {r['content']}")
        conn.close()
        return "\n".join(parts)

    def get_summary(self, conversation_id: int) -> str:
        conn = self._connect()
        c = conn.cursor()
        c.execute("SELECT summary FROM conversations WHERE id=?", (conversation_id,))
        row = c.fetchone()
        conn.close()
        return row["summary"] if row else ""

    def get_recent_messages(self, conversation_id: int, limit: int = 4) -> List[Tuple[str, str]]:
        conn = self._connect()
        c = conn.cursor()
        c.execute("""
            SELECT role, content FROM messages
            WHERE conversation_id=?
            ORDER BY id DESC LIMIT ?
        """, (conversation_id, limit))
        rows = c.fetchall()
        conn.close()
        # return oldest -> newest
        return list(reversed([(r["role"], r["content"]) for r in rows]))

    def get_history(self, user_id: str) -> List[Dict]:
        conv_id = self._get_or_create_conversation(user_id)
        conn = self._connect()
        c = conn.cursor()
        c.execute("""
            SELECT role, content, created_at FROM messages
            WHERE conversation_id=?
            ORDER BY id ASC
        """, (conv_id,))
        rows = c.fetchall()
        conn.close()
        return [{"role": r["role"], "content": r["content"], "time": r["created_at"]} for r in rows]

    def get_conversations(self, user_id: str) -> List[Dict]:
        """Trả về danh sách cuộc trò chuyện của user, nếu chưa có thì tạo mới."""
        # đảm bảo có ít nhất 1 conversation
        conv_id = self._get_or_create_conversation(user_id)

        conn = self._connect()
        c = conn.cursor()
        c.execute("""
            SELECT id, summary, (
                SELECT content FROM messages 
                WHERE conversation_id = conversations.id 
                ORDER BY id ASC LIMIT 1
            ) AS first_message,
            (
                SELECT created_at FROM messages 
                WHERE conversation_id = conversations.id 
                ORDER BY id ASC LIMIT 1
            ) AS created_at
            FROM conversations
            WHERE user_id=?
            ORDER BY created_at DESC
        """, (user_id,))
        rows = c.fetchall()
        conn.close()

        results = []
        for r in rows:
            title = r["summary"] or (r["first_message"] or "Cuộc trò chuyện mới")
            results.append({
                "id": r["id"],
                "title": title.strip()[:50],
                "created_at": datetime.fromisoformat(r["created_at"]) if r["created_at"] else None
            })
        return results

    def get_conversation_messages(self, conversation_id: int) -> List[Dict]:
        """Trả về toàn bộ tin nhắn trong một cuộc trò chuyện"""
        conn = self._connect()
        c = conn.cursor()
        c.execute("""
            SELECT role, content, created_at FROM messages
            WHERE conversation_id=?
            ORDER BY id ASC
        """, (conversation_id,))
        rows = c.fetchall()
        conn.close()
        return [{"role": r["role"], "content": r["content"], "time": r["created_at"]} for r in rows]
