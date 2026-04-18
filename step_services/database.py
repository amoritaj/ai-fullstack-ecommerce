import sqlite3

conn = sqlite3.connect("services.db")
cursor = conn.cursor()

# حذف الجداول القديمة
cursor.execute("DROP TABLE IF EXISTS users")
cursor.execute("DROP TABLE IF EXISTS requests")

# إنشاء جدول المستخدمين
cursor.execute("""
CREATE TABLE users (

id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT UNIQUE,
password TEXT,
phone TEXT,
role TEXT DEFAULT 'user'

)
""")

# إنشاء جدول الطلبات
cursor.execute("""
CREATE TABLE requests (

id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT,
service TEXT,
phone TEXT,
date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
status TEXT DEFAULT 'Pending'

)
""")

# إنشاء الأدمن
cursor.execute("""
INSERT INTO users (username,password,phone,role)
VALUES ('admin','1234','0000000000','admin')
""")


conn.commit()
conn.close()

print("Database recreated successfully ✔")