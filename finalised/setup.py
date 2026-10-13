#!/usr/bin/env python3
# Quick Setup Script

import os
import sqlite3

def setup_project():
    print("🫁 RESPIRATORY AI SYSTEM SETUP")
    print("=" * 40)

    # Create directories
    directories = ['uploads', 'reports', 'static/css', 'static/js', 'templates']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created: {directory}/")

    # Initialize database
    conn = sqlite3.connect('respiratory.db')
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        email TEXT,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        filename TEXT,
        prediction TEXT,
        confidence REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')

    conn.commit()
    conn.close()
    print("✅ Database initialized!")

    print("\n🎉 SETUP COMPLETE!")
    print("Next steps:")
    print("1. Move HTML files to templates/ folder")
    print("2. Run: python app.py")
    print("3. Open: http://localhost:5000")

if __name__ == "__main__":
    setup_project()
