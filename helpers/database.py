import sqlite3
import os
from pathlib import Path
from helpers.logger import Logger
from contextlib import contextmanager

DB_PATH = Path(__file__).parent.parent / 'storage' / 'app.db'

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Initialize database with schema and sample data"""
    os.makedirs(DB_PATH.parent, exist_ok=True)
    
    schema = """
    -- Adapted MySQL schema to SQLite
    DROP TABLE IF EXISTS audit_logs;
    DROP TABLE IF EXISTS chat_messages;
    DROP TABLE IF EXISTS chat_sessions;
    DROP TABLE IF EXISTS project_files;
    DROP TABLE IF EXISTS projects;
    DROP TABLE IF EXISTS client_ids;
    DROP TABLE IF EXISTS clients;
    DROP TABLE IF EXISTS employees;
    DROP TABLE IF EXISTS admins;

    CREATE TABLE admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        status TEXT DEFAULT 'active',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        status TEXT DEFAULT 'active',
        created_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (created_by) REFERENCES admins(id)
    );

    CREATE TABLE client_ids (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id_code TEXT UNIQUE NOT NULL,
        client_id_name TEXT NOT NULL,
        status TEXT DEFAULT 'active',
        created_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (created_by) REFERENCES admins(id)
    );

    CREATE TABLE clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL,
        client_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        status TEXT DEFAULT 'active',
        created_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (client_id) REFERENCES client_ids(id),
        FOREIGN KEY (created_by) REFERENCES admins(id)
    );

    CREATE TABLE projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_code TEXT UNIQUE NOT NULL,
        project_name TEXT NOT NULL,
        project_description TEXT,
        client_id INTEGER NOT NULL,
        created_by_employee_id INTEGER NOT NULL,
        status TEXT DEFAULT 'active',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (client_id) REFERENCES client_ids(id),
        FOREIGN KEY (created_by_employee_id) REFERENCES employees(id)
    );

    -- Sample data
    INSERT OR REPLACE INTO admins (id, name, email, password_hash) VALUES
    (1, 'Admin User', 'admin@example.com', '$2y$10$YMjO0kVBqEhJYr0CZmG4..G.1U6QyNFH9t6pLxD3DZ5MfGqBbYpS2');

    INSERT OR REPLACE INTO employees (id, employee_code, name, email, password_hash, created_by) VALUES
    (1, 'EMP-001', 'John Doe', 'john@example.com', '$2y$10$8KzLbOx.YJM5hO8NbUdToeA1fFhQJ2mCBp6S6v5vYV0aZqfcRtSJi', 1);

    INSERT OR REPLACE INTO client_ids (id, client_id_code, client_id_name, created_by) VALUES
    (1, 'CLIENT-001', 'ABC Corporation', 1),
    (2, 'CLIENT-002', 'XYZ Industries', 1);

    INSERT OR REPLACE INTO clients (id, client_id, client_name, email, password_hash, created_by) VALUES
    (1, 1, 'Mr. ABC', 'abc@example.com', '$2y$10$kH4rQE8lDJfcp0pN4uYJku.GV7dF3aXm5P/W2qLjZnQJNPjGhqv3u', 1),
    (2, 2, 'Ms. XYZ', 'xyz@example.com', '$2y$10$kH4rQE8lDJfcp0pN4uYJku.GV7dF3aXm5P/W2qLjZnQJNPjGhqv3u', 2);
    """
    
    with get_db() as conn:
        conn.executescript(schema)
        conn.commit()
    Logger.info('Database initialized at storage/app.db')
    
def db_execute(query, params=(), fetch=False):
    with get_db() as conn:
        cursor = conn.execute(query, params)
        if fetch == 'all':
            return [dict(row) for row in cursor.fetchall()]
        elif fetch:
            return dict(cursor.fetchone())
        conn.commit()
        return True

