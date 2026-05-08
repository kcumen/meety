import sqlite3

def check_db():
    conn = sqlite3.connect("meety.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, platform, native_meeting_id, status FROM meetings")
    rows = cursor.fetchall()
    print("ID | Platform | Native ID | Status")
    print("---|---|---|---")
    for row in rows:
        print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]}")
    conn.close()

if __name__ == "__main__":
    check_db()
