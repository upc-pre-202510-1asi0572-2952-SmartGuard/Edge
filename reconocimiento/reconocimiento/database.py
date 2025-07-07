import sqlite3
import os

DB_PATH = os.path.join(os.getcwd(), "facelock.db")

def init_database():
    """Inicializa la base de datos y las tablas principales si no existen."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            age INTEGER,
            pin TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS access_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT,
            access_method TEXT,
            success BOOLEAN,
            confidence REAL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()
    print("Base de datos y tablas inicializadas correctamente.")

def save_user(name, age, pin):
    """Guarda un usuario nuevo o actualiza el PIN si el usuario ya existe."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO users (name, age, pin, is_active)
        VALUES (?, ?, ?, 1)
    ''', (name, age, pin))
    conn.commit()
    conn.close()
    print(f"Usuario '{name}' guardado en base de datos.")

def get_user_by_name(name):
    """Obtiene los datos de un usuario por nombre."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, age, pin, is_active FROM users WHERE name = ?', (name,))
    user = cursor.fetchone()
    conn.close()
    return user

def get_user_by_pin(pin):
    """Obtiene el nombre del usuario asociado a un PIN activo."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT name FROM users WHERE pin = ? AND is_active = 1', (pin,))
    user = cursor.fetchone()
    conn.close()
    return user[0] if user else None

def log_access(user_name, method, success, confidence=0.0):
    """Registra un intento de acceso en la tabla de logs."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO access_logs (user_name, access_method, success, confidence)
        VALUES (?, ?, ?, ?)
    ''', (user_name, method, int(success), confidence))
    conn.commit()
    conn.close()
    print(f"Log: {'' if success else ''} {user_name} - {method} - {confidence:.2f}")

def get_recent_logs(limit=10):
    """Obtiene los últimos accesos registrados."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT user_name, access_method, success, confidence, timestamp 
        FROM access_logs 
        ORDER BY timestamp DESC 
        LIMIT ?
    ''', (limit,))
    logs = cursor.fetchall()
    conn.close()
    return logs

def get_all_users():
    """Devuelve todos los usuarios registrados."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, age, pin, created_at, is_active FROM users')
    users = cursor.fetchall()
    conn.close()
    return users

def deactivate_user(name):
    """Desactiva (baja lógica) un usuario."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET is_active = 0 WHERE name = ?', (name,))
    conn.commit()
    conn.close()
    print(f"Usuario '{name}' desactivado.")

def activate_user(name):
    """Activa un usuario previamente desactivado."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET is_active = 1 WHERE name = ?', (name,))
    conn.commit()
    conn.close()
    print(f"Usuario '{name}' activado.")

if __name__ == "__main__":
    init_database()
