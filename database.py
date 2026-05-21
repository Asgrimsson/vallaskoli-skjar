import sqlite3
from pathlib import Path
from datetime import date, datetime

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "vallaskoli_skjar.db"
PUBLIC_RENDER_URL = "https://vallaskoli-skjar.onrender.com"

DATA_DIR.mkdir(exist_ok=True)


def connect():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS menu_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            weekday INTEGER NOT NULL UNIQUE,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            updated_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            category TEXT DEFAULT 'Almennt',
            priority TEXT DEFAULT 'Venjulegt',
            active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            expires_at TEXT DEFAULT ''
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            event_date TEXT NOT NULL,
            event_time TEXT DEFAULT '',
            location TEXT DEFAULT '',
            source TEXT DEFAULT 'Handvirkt',
            active INTEGER DEFAULT 1
        )
    """)

    # Upgrade old v1.0 database if needed
    try:
        cur.execute("ALTER TABLE events ADD COLUMN source TEXT DEFAULT 'Handvirkt'")
    except sqlite3.OperationalError:
        pass

    cur.execute("""
        CREATE TABLE IF NOT EXISTS thoughts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            active INTEGER DEFAULT 1
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            caption TEXT DEFAULT '',
            active INTEGER DEFAULT 1,
            uploaded_at TEXT NOT NULL
        )
    """)

    # Upgrade image table for v1.9 image targeting/placement.
    for sql in [
        "ALTER TABLE images ADD COLUMN target_modes TEXT DEFAULT '[\"Allir\"]'",
        "ALTER TABLE images ADD COLUMN placement TEXT DEFAULT 'Aðalmyndasýning'",
        "ALTER TABLE images ADD COLUMN weight INTEGER DEFAULT 1",
    ]:
        try:
            cur.execute(sql)
        except sqlite3.OperationalError:
            pass


    cur.execute("""
        CREATE TABLE IF NOT EXISTS screen_devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            location TEXT DEFAULT '',
            mode TEXT DEFAULT 'Anddyri',
            playlist TEXT DEFAULT 'Sjálfvirkt',
            active INTEGER DEFAULT 1,
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            last_seen TEXT DEFAULT ''
        )
    """)

    # Upgrade screen table for v1.9 stored direct URLs.
    try:
        cur.execute("ALTER TABLE screen_devices ADD COLUMN url TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass

    defaults = {
        "school_name": "Vallaskóli",
        "subtitle": "Upplýsingaskjár",
        "admin_password": "vallaskoli123",
        "screen_refresh_seconds": "8",
        "slide_seconds": "12",
        "weather_lat": "63.9331",
        "weather_lon": "-20.9971",
        "weather_place": "Selfoss",
        "screen_mode": "Sjálfvirkt",
        "screen_size_default": "Venjulegur skjár",
        "screen_size_Anddyri": "Venjulegur skjár",
        "screen_size_Matsalur": "Venjulegur skjár",
        "screen_size_Kennarastofa": "Venjulegur skjár",
        "screen_size_Sjálfvirkt": "Venjulegur skjár",
        "vallaskoli_menu_enabled": "1",
        "vallaskoli_menu_url": "https://vallaskoli.is/skolinn/matsedill/",
        "sheets_enabled": "0",
        "sheets_csv_url": "",
        "sheets_date_column": "Dagsetning",
        "sheets_weekday_column": "Dagur",
        "sheets_title_column": "Matur",
        "sheets_description_column": "Lýsing",
        "vallaskoli_events_enabled": "1",
        "vallaskoli_events_url": "https://vallaskoli.is/skolinn/vidburdadagatal/",
        "vallaskoli_events_days_ahead": "90",
        "calendar_enabled": "0",
        "calendar_ics_url": "",
        "calendar_days_ahead": "30",
        "emergency_active": "0",
        "emergency_title": "Áríðandi skilaboð",
        "emergency_body": "",
        "logo_url": "https://vallaskoli.is/wp-content/uploads/bb-plugin/cache/logo-med-hvitu-borda-2-300x156-landscape-1f88abc64591c414446c74a40697ddeb-5fc7b0eede877.png",
        "admin_home_note": "",
        "use_screen_editor": "1",
        "editor_seconds_Anddyri": "12",
        "editor_seconds_Matsalur": "14",
        "editor_seconds_Kennarastofa": "16",
        "editor_seconds_Sjálfvirkt": "12",
        "editor_theme_Anddyri": "Blár Vallaskóli",
        "editor_theme_Matsalur": "Grænn matsalur",
        "editor_theme_Kennarastofa": "Fjólublár kennari",
        "editor_theme_Sjálfvirkt": "Blár Vallaskóli",
        "editor_blocks_Anddyri": '["announcements","images","events","weather","menu","thought","quickstats"]',
        "editor_blocks_Matsalur": '["menu","announcements","weather","thought","images"]',
        "editor_blocks_Kennarastofa": '["announcements","events","weather","menu","thought","quickstats"]',
        "editor_blocks_Sjálfvirkt": '["menu","weather","announcements","images","events","thought","quickstats"]',

        "public_base_url": "https://vallaskoli-skjar.onrender.com",
        "show_proverb_all_screens": "1",
        "show_ticker": "1",
        "show_image_sidebar": "1",
        "image_layout_default": "Stór mynd + texti",
        "image_fit_default": "Fylla ramma",
        "use_playlists": "1",
        "playlist_schedule_enabled": "1",
        "default_playlist": "Sjálfgefin",
        "playlist_morning_start": "07:30",
        "playlist_morning_end": "10:30",
        "playlist_noon_start": "10:30",
        "playlist_noon_end": "13:30",
        "playlist_endday_start": "13:30",
        "playlist_endday_end": "16:30",
        "playlist_blocks_Sjálfgefin": '["menu","weather","announcements","images","events","thought","quickstats"]',
        "playlist_seconds_Sjálfgefin": "12",
        "playlist_theme_Sjálfgefin": "Blár Vallaskóli",
        "playlist_blocks_Morgunspilun": '["weather","announcements","events","menu","thought","images"]',
        "playlist_seconds_Morgunspilun": "12",
        "playlist_theme_Morgunspilun": "Blár Vallaskóli",
        "playlist_blocks_Hádegisspilun": '["menu","announcements","weather","images","thought"]',
        "playlist_seconds_Hádegisspilun": "14",
        "playlist_theme_Hádegisspilun": "Grænn matsalur",
        "playlist_blocks_Lok_dags": '["events","announcements","thought","weather","images"]',
        "playlist_seconds_Lok_dags": "16",
        "playlist_theme_Lok_dags": "Fjólublár kennari",
        "playlist_blocks_Viðburðaspilun": '["events","images","announcements","thought"]',
        "playlist_seconds_Viðburðaspilun": "15",
        "playlist_theme_Viðburðaspilun": "Gull og blár",
    }
    for key, value in defaults.items():
        cur.execute("INSERT OR IGNORE INTO settings(key, value) VALUES (?, ?)", (key, value))

    # Render migration: if this database still has localhost from an older version, switch QR/direct URLs to the live site.
    row = cur.execute("SELECT value FROM settings WHERE key='public_base_url'").fetchone()
    if not row or row["value"].strip() in ("", "http://localhost:8501"):
        cur.execute(
            "INSERT INTO settings(key, value) VALUES ('public_base_url', ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (PUBLIC_RENDER_URL,),
        )

    # v1.12 speed migration: update old 60-second refresh installs to faster screen updates.
    refresh_row = cur.execute("SELECT value FROM settings WHERE key='screen_refresh_seconds'").fetchone()
    if not refresh_row or refresh_row["value"].strip() in ("", "60"):
        cur.execute(
            "INSERT INTO settings(key, value) VALUES ('screen_refresh_seconds', '8') ON CONFLICT(key) DO UPDATE SET value=excluded.value"
        )

    cur.execute("SELECT COUNT(*) AS c FROM menu_items")
    if cur.fetchone()["c"] == 0:
        meals = [
            (0, "Mánudagur", "Settu inn matseðil dagsins í stjórnborði eða tengdu Google Sheets."),
            (1, "Þriðjudagur", "Settu inn matseðil dagsins í stjórnborði eða tengdu Google Sheets."),
            (2, "Miðvikudagur", "Settu inn matseðil dagsins í stjórnborði eða tengdu Google Sheets."),
            (3, "Fimmtudagur", "Settu inn matseðil dagsins í stjórnborði eða tengdu Google Sheets."),
            (4, "Föstudagur", "Settu inn matseðil dagsins í stjórnborði eða tengdu Google Sheets."),
            (5, "Helgi", "Enginn skólamatur skráður."),
            (6, "Helgi", "Enginn skólamatur skráður."),
        ]
        for weekday, title, desc in meals:
            cur.execute(
                "INSERT INTO menu_items(weekday, title, description, updated_at) VALUES (?, ?, ?, ?)",
                (weekday, title, desc, datetime.now().isoformat(timespec="seconds")),
            )

    cur.execute("SELECT COUNT(*) AS c FROM announcements")
    if cur.fetchone()["c"] == 0:
        cur.execute(
            "INSERT INTO announcements(title, body, category, priority, active, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            ("Velkomin í skólann!", "Hafið góðan dag og munið að hjálpast að.", "Nemendur", "Venjulegt", 1, datetime.now().isoformat(timespec="seconds")),
        )

    cur.execute("SELECT COUNT(*) AS c FROM thoughts")
    if cur.fetchone()["c"] == 0:
        thoughts = [
            "Mistök eru merki um að heilinn sé að læra.",
            "Við gerum okkar besta og hjálpum hvert öðru.",
            "Góður skólabragur byrjar á litlum góðverkum.",
            "Við erum öll hluti af góðum skóladegi.",
        ]
        for t in thoughts:
            cur.execute("INSERT INTO thoughts(text, active) VALUES (?, 1)", (t,))


    # Ensure standard Vallaskóli screen devices exist, also on already-initialized databases.
    default_devices = [
        ("ANDDYRI-01", "Aðalskjár", "Anddyri Vallaskóla", "Anddyri", "Morgunspilun", "Aðalskjár fyrir nemendur, starfsfólk og gesti"),
        ("MATSALUR-01", "Matsalur", "Matsalur", "Matsalur", "Hádegisspilun", "Matseðill, léttar tilkynningar og myndir"),
        ("KENNARASTOFA-01", "Kennarastofa", "Kennarastofa", "Kennarastofa", "Sjálfgefin", "Upplýsingar fyrir starfsfólk, fundir og viðburðir"),
        ("GANGUR-YNGRA-01", "Gangur yngra stigs", "Yngra stig", "Anddyri", "Morgunspilun", "Barnvænar tilkynningar, myndir og góð hugsun dagsins"),
        ("GANGUR-ELDRA-01", "Gangur eldra stigs", "Eldra stig", "Anddyri", "Sjálfgefin", "Viðburðir, félagslíf, próf og almennar tilkynningar"),
        ("SKRIFSTOFA-01", "Skrifstofa", "Skrifstofa", "Anddyri", "Sjálfgefin", "Upplýsingar fyrir gesti og foreldra"),
    ]
    now = datetime.now().isoformat(timespec="seconds")
    base_row = cur.execute("SELECT value FROM settings WHERE key='public_base_url'").fetchone()
    base_url = (base_row["value"] if base_row else PUBLIC_RENDER_URL).strip().rstrip("/") or PUBLIC_RENDER_URL
    for code, name, location, mode, playlist, notes in default_devices:
        direct_url = f"{base_url}/?view=skjar&device={code}"
        cur.execute(
            "INSERT OR IGNORE INTO screen_devices(code, name, location, mode, playlist, active, notes, created_at, url) VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?)",
            (code, name, location, mode, playlist, notes, now, direct_url),
        )
        cur.execute(
            "UPDATE screen_devices SET url=? WHERE code=? AND (url IS NULL OR url='' OR url LIKE 'http://localhost:%')",
            (direct_url, code),
        )

    conn.commit()
    conn.close()


def get_setting(key, default=""):
    conn = connect()
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default


def set_setting(key, value):
    conn = connect()
    conn.execute(
        "INSERT INTO settings(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, str(value)),
    )
    conn.commit()
    conn.close()


def get_settings():
    conn = connect()
    rows = conn.execute("SELECT key, value FROM settings").fetchall()
    conn.close()
    return {r["key"]: r["value"] for r in rows}


def upsert_menu(weekday, title, description):
    conn = connect()
    conn.execute(
        """
        INSERT INTO menu_items(weekday, title, description, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(weekday) DO UPDATE SET
            title=excluded.title,
            description=excluded.description,
            updated_at=excluded.updated_at
        """,
        (weekday, title, description, datetime.now().isoformat(timespec="seconds")),
    )
    conn.commit()
    conn.close()


def get_menu_week():
    conn = connect()
    rows = conn.execute("SELECT * FROM menu_items ORDER BY weekday").fetchall()
    conn.close()
    return rows


def get_menu_today():
    conn = connect()
    row = conn.execute("SELECT * FROM menu_items WHERE weekday=?", (date.today().weekday(),)).fetchone()
    conn.close()
    return row


def add_announcement(title, body, category, priority, expires_at=""):
    conn = connect()
    conn.execute(
        "INSERT INTO announcements(title, body, category, priority, active, created_at, expires_at) VALUES (?, ?, ?, ?, 1, ?, ?)",
        (title, body, category, priority, datetime.now().isoformat(timespec="seconds"), expires_at),
    )
    conn.commit()
    conn.close()


def list_announcements(active_only=False):
    conn = connect()
    q = "SELECT * FROM announcements"
    if active_only:
        q += " WHERE active=1 AND (expires_at='' OR expires_at>=?)"
        rows = conn.execute(q + " ORDER BY CASE priority WHEN 'Áríðandi' THEN 3 WHEN 'Mikilvægt' THEN 2 ELSE 1 END DESC, created_at DESC", (date.today().isoformat(),)).fetchall()
    else:
        rows = conn.execute(q + " ORDER BY active DESC, created_at DESC").fetchall()
    conn.close()
    return rows


def set_announcement_active(item_id, active):
    conn = connect()
    conn.execute("UPDATE announcements SET active=? WHERE id=?", (1 if active else 0, item_id))
    conn.commit()
    conn.close()


def delete_announcement(item_id):
    conn = connect()
    conn.execute("DELETE FROM announcements WHERE id=?", (item_id,))
    conn.commit()
    conn.close()


def add_event(title, event_date, event_time="", location="", source="Handvirkt"):
    conn = connect()
    conn.execute(
        "INSERT INTO events(title, event_date, event_time, location, source, active) VALUES (?, ?, ?, ?, ?, 1)",
        (title, event_date, event_time, location, source),
    )
    conn.commit()
    conn.close()


def list_events(upcoming_only=True, limit=8):
    conn = connect()
    if upcoming_only:
        rows = conn.execute(
            "SELECT * FROM events WHERE active=1 AND event_date>=? ORDER BY event_date, event_time LIMIT ?",
            (date.today().isoformat(), limit),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM events ORDER BY event_date DESC, event_time DESC").fetchall()
    conn.close()
    return rows


def delete_event(item_id):
    conn = connect()
    conn.execute("DELETE FROM events WHERE id=?", (item_id,))
    conn.commit()
    conn.close()


def add_thought(text):
    conn = connect()
    conn.execute("INSERT INTO thoughts(text, active) VALUES (?, 1)", (text,))
    conn.commit()
    conn.close()


def list_thoughts(active_only=True):
    conn = connect()
    if active_only:
        rows = conn.execute("SELECT * FROM thoughts WHERE active=1 ORDER BY id DESC").fetchall()
    else:
        rows = conn.execute("SELECT * FROM thoughts ORDER BY active DESC, id DESC").fetchall()
    conn.close()
    return rows


def delete_thought(item_id):
    conn = connect()
    conn.execute("DELETE FROM thoughts WHERE id=?", (item_id,))
    conn.commit()
    conn.close()


def add_image(filename, caption="", target_modes=None, placement="Aðalmyndasýning", weight=1):
    conn = connect()
    if target_modes is None:
        target_modes = ["Allir"]
    import json
    conn.execute(
        "INSERT INTO images(filename, caption, active, uploaded_at, target_modes, placement, weight) VALUES (?, ?, 1, ?, ?, ?, ?)",
        (filename, caption, datetime.now().isoformat(timespec="seconds"), json.dumps(target_modes, ensure_ascii=False), placement, int(weight or 1)),
    )
    conn.commit()
    conn.close()


def list_images(active_only=True):
    conn = connect()
    if active_only:
        rows = conn.execute("SELECT * FROM images WHERE active=1 ORDER BY weight DESC, uploaded_at DESC").fetchall()
    else:
        rows = conn.execute("SELECT * FROM images ORDER BY active DESC, weight DESC, uploaded_at DESC").fetchall()
    conn.close()
    return rows


def list_images_for_mode(mode="Sjálfvirkt", active_only=True):
    import json
    rows = list_images(active_only=active_only)
    visible = []
    for r in rows:
        try:
            targets = json.loads(r["target_modes"] or '["Allir"]')
        except Exception:
            targets = ["Allir"]
        if "Allir" in targets or mode in targets:
            visible.append(r)
    return visible


def delete_image(item_id):
    conn = connect()
    row = conn.execute("SELECT filename FROM images WHERE id=?", (item_id,)).fetchone()
    conn.execute("DELETE FROM images WHERE id=?", (item_id,))
    conn.commit()
    conn.close()
    return row["filename"] if row else None



def list_screen_devices(active_only=False):
    conn = connect()
    if active_only:
        rows = conn.execute("SELECT * FROM screen_devices WHERE active=1 ORDER BY location, name").fetchall()
    else:
        rows = conn.execute("SELECT * FROM screen_devices ORDER BY active DESC, location, name").fetchall()
    conn.close()
    return rows


def get_screen_device(code):
    conn = connect()
    row = conn.execute("SELECT * FROM screen_devices WHERE code=?", (code,)).fetchone()
    conn.close()
    return row


def upsert_screen_device(code, name, location, mode, playlist, active=True, notes=""):
    conn = connect()
    now = datetime.now().isoformat(timespec="seconds")
    code_clean = code.strip().upper()
    base_row = conn.execute("SELECT value FROM settings WHERE key='public_base_url'").fetchone()
    base_url = (base_row["value"] if base_row else PUBLIC_RENDER_URL).strip().rstrip("/") or PUBLIC_RENDER_URL
    direct_url = f"{base_url}/?view=skjar&device={code_clean}"
    conn.execute(
        """
        INSERT INTO screen_devices(code, name, location, mode, playlist, active, notes, created_at, url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(code) DO UPDATE SET
            name=excluded.name,
            location=excluded.location,
            mode=excluded.mode,
            playlist=excluded.playlist,
            active=excluded.active,
            notes=excluded.notes,
            url=excluded.url
        """,
        (code_clean, name, location, mode, playlist, 1 if active else 0, notes, now, direct_url),
    )
    conn.commit()
    conn.close()


def refresh_screen_device_urls():
    conn = connect()
    base_row = conn.execute("SELECT value FROM settings WHERE key='public_base_url'").fetchone()
    base_url = (base_row["value"] if base_row else PUBLIC_RENDER_URL).strip().rstrip("/") or PUBLIC_RENDER_URL
    rows = conn.execute("SELECT code FROM screen_devices").fetchall()
    for r in rows:
        conn.execute("UPDATE screen_devices SET url=? WHERE code=?", (f"{base_url}/?view=skjar&device={r['code']}", r["code"]))
    conn.commit()
    conn.close()


def delete_screen_device(code):
    conn = connect()
    conn.execute("DELETE FROM screen_devices WHERE code=?", (code,))
    conn.commit()
    conn.close()


def touch_screen_device(code):
    conn = connect()
    conn.execute("UPDATE screen_devices SET last_seen=? WHERE code=?", (datetime.now().isoformat(timespec="seconds"), code))
    conn.commit()
    conn.close()
