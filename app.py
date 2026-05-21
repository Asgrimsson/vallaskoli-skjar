from pathlib import Path
from datetime import date, datetime, timedelta
from email.utils import parsedate_to_datetime
import csv
import html
import json
import random
import re
import time
from io import StringIO, BytesIO
from urllib.parse import quote

import qrcode

import requests
from bs4 import BeautifulSoup
import streamlit as st
from PIL import Image
from streamlit_autorefresh import st_autorefresh

import database as db

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads" / "myndir"
ASSET_DIR = BASE_DIR / "assets"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ASSET_DIR.mkdir(exist_ok=True)

st.set_page_config(
    page_title="Vallaskóli Skjár",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="collapsed",
)

db.init_db()

WEEKDAYS = ["Mánudagur", "Þriðjudagur", "Miðvikudagur", "Fimmtudagur", "Föstudagur", "Laugardagur", "Sunnudagur"]
SHORT_WEEKDAYS = ["mán", "þri", "mið", "fim", "fös", "lau", "sun"]
PRIORITY_ORDER = {"Áríðandi": 3, "Mikilvægt": 2, "Venjulegt": 1}
SCREEN_MODES = ["Sjálfvirkt", "Anddyri", "Matsalur", "Kennarastofa"]

VERSION = "v1.9"
BLOCKS = {
    "menu": "🍽️ Matseðill",
    "weather": "🌦️ Veður",
    "announcements": "📣 Tilkynningar",
    "images": "🖼️ Myndasýning",
    "events": "🗓️ Viðburðir",
    "thought": "💬 Góð hugsun",
    "proverb": "📜 Málsháttur / orðtak",
    "quickstats": "⚡ Flýtikubbar",
}
DEFAULT_BLOCKS_BY_MODE = {
    "Anddyri": ["announcements", "images", "events", "weather", "menu", "thought", "proverb", "quickstats"],
    "Matsalur": ["menu", "announcements", "weather", "thought", "proverb", "images"],
    "Kennarastofa": ["announcements", "events", "weather", "menu", "thought", "proverb", "quickstats"],
    "Sjálfvirkt": ["menu", "weather", "announcements", "images", "events", "thought", "proverb", "quickstats"],
}
THEMES = {
    "Blár Vallaskóli": "#0f4c81",
    "Grænn matsalur": "#2f7d32",
    "Fjólublár kennari": "#5b3fa3",
    "Gull og blár": "#b98500",
    "Rólegur dökkblár": "#183153",
    "Norðurljós": "#006d77",
    "Hlýr skóladagur": "#d97706",
    "Bleikur föstudagur": "#be185d",
}

PLAYLISTS = {
    "Sjálfgefin": "Sjálfgefin spilun",
    "Morgunspilun": "Morgunspilun",
    "Hádegisspilun": "Hádegisspilun",
    "Lok dags": "Lok dags",
    "Viðburðaspilun": "Viðburðaspilun",
}
DEFAULT_PLAYLISTS = {
    "Sjálfgefin": {"blocks": ["menu", "weather", "announcements", "images", "events", "thought", "proverb", "quickstats"], "seconds": 12, "theme": "Blár Vallaskóli"},
    "Morgunspilun": {"blocks": ["weather", "announcements", "events", "menu", "thought", "proverb", "images"], "seconds": 12, "theme": "Blár Vallaskóli"},
    "Hádegisspilun": {"blocks": ["menu", "announcements", "weather", "images", "thought"], "seconds": 14, "theme": "Grænn matsalur"},
    "Lok dags": {"blocks": ["events", "announcements", "thought", "proverb", "weather", "images"], "seconds": 16, "theme": "Fjólublár kennari"},
    "Viðburðaspilun": {"blocks": ["events", "images", "announcements", "thought", "proverb"], "seconds": 15, "theme": "Gull og blár"},
}


def h(value):
    return html.escape(str(value or ""))


def css(mode="Sjálfvirkt", accent_override=None):
    accent = accent_override or {
        "Anddyri": "#0f4c81",
        "Matsalur": "#2f7d32",
        "Kennarastofa": "#5b3fa3",
        "Sjálfvirkt": "#0f4c81",
    }.get(mode, "#0f4c81")
    st.markdown(
        f"""
        <style>
        :root{{
            --blue:{accent};
            --blue2:#1b75bb;
            --gold:#ffc857;
            --green:#28a745;
            --dark:#0b172a;
            --soft:#f4f8fb;
            --card:rgba(255,255,255,.92);
        }}
        html, body, [data-testid="stAppViewContainer"] {{
            background:
              radial-gradient(circle at top left, rgba(29,117,188,.25), transparent 32%),
              radial-gradient(circle at bottom right, rgba(255,200,87,.22), transparent 34%),
              linear-gradient(135deg, #eef7ff 0%, #f8fbff 42%, #edf9f4 100%);
            color:#102033;
        }}
        [data-testid="stHeader"] {{ background: rgba(255,255,255,0); }}
        [data-testid="stSidebar"] {{ background:#0b172a; }}
        .block-container {{ padding-top: 1.05rem; max-width: 1540px; }}
        .hero-card, .admin-card, .slide-card, .small-card {{
            background: var(--card);
            border: 1px solid rgba(15,76,129,.12);
            box-shadow: 0 18px 55px rgba(15,76,129,.12);
            border-radius: 28px;
            padding: 30px;
            animation: cardIn .65s cubic-bezier(.2,.8,.2,1) both;
        }}
        .topbar {{
            display:flex; align-items:flex-start; justify-content:space-between; gap:28px;
            padding: 26px 34px; border-radius: 34px;
            background:
              radial-gradient(circle at 8% 15%, rgba(255,255,255,.22), transparent 24%),
              linear-gradient(135deg, {accent}, #1b75bb 58%, #0b4f7d);
            color: white; box-shadow: 0 24px 70px rgba(15,76,129,.28);
            margin-bottom: 22px; position:relative; overflow:hidden;
            animation: fadeSlideIn .75s ease both;
        }}
        .topbar:after {{ content:""; position:absolute; inset:-60% -20%; background:linear-gradient(110deg, transparent, rgba(255,255,255,.18), transparent); transform:translateX(-70%); animation: shimmer 7s ease-in-out infinite; }}
        .brand {{ display:flex; align-items:center; gap:24px; position:relative; z-index:2; min-width:0; }}
        .logo-badge {{ width:112px; height:86px; border-radius:22px; background:white; display:grid; place-items:center; color:{accent}; font-weight:900; font-size:25px; box-shadow: inset 0 0 0 2px rgba(15,76,129,.12), 0 12px 32px rgba(0,0,0,.16); overflow:hidden; padding:8px; flex:0 0 auto; }}
        .logo-badge img {{ max-width:100%; max-height:100%; object-fit:contain; display:block; }}
        .admin-quick {{ background:linear-gradient(135deg, rgba(15,76,129,.08), rgba(255,200,87,.12)); border:1px solid rgba(15,76,129,.12); border-radius:22px; padding:18px; margin-bottom:14px; }}
        .admin-quick h3 {{ margin:0 0 6px; }}
        .daily-box {{ background:linear-gradient(135deg, rgba(255,255,255,.92), rgba(232,243,255,.85)); border:1px solid rgba(15,76,129,.14); border-radius:24px; padding:20px; margin-bottom:16px; box-shadow:0 12px 35px rgba(15,76,129,.08); }}
        .daily-box h3 {{ margin:0 0 8px; }}
        .source-good {{ color:#087f5b; font-weight:900; }}
        .source-warn {{ color:#b98500; font-weight:900; }}
        .url-box {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; background:#102033; color:white; padding:14px 16px; border-radius:16px; overflow-wrap:anywhere; font-size:14px; }}
        .playlist-card {{ background:linear-gradient(135deg, rgba(255,255,255,.94), rgba(232,243,255,.78)); border:1px solid rgba(15,76,129,.14); border-radius:24px; padding:18px; margin-bottom:14px; box-shadow:0 12px 35px rgba(15,76,129,.08); }}
        .admin-muted {{ color:#61758a; font-size:14px; }}
        .editor-preview {{ border:2px dashed rgba(15,76,129,.20); border-radius:26px; padding:18px; background:rgba(255,255,255,.55); }}
        .block-chip {{ display:inline-block; padding:9px 13px; margin:4px 5px 4px 0; border-radius:999px; background:rgba(15,76,129,.10); color:{accent}; font-weight:900; }}
        .slide-dots {{ display:flex; gap:8px; justify-content:center; margin:12px 0 4px; }}
        .slide-dot {{ width:12px; height:12px; border-radius:999px; background:rgba(15,76,129,.18); }}
        .slide-dot.active {{ background:{accent}; transform:scale(1.35); }}
        .brand-title {{ font-size: clamp(36px, 5vw, 64px); line-height:.95; font-weight:950; letter-spacing:-.05em; margin-bottom:10px; }}
        .brand-sub {{ font-size: clamp(18px, 1.7vw, 24px); opacity:.90; margin-top:2px; line-height:1.25; }}
        .clock {{ text-align:right; position:relative; z-index:2; }}
        .clock-time {{ font-size: clamp(34px, 5vw, 72px); font-weight:900; letter-spacing:-.05em; line-height:.9; }}
        .clock-date {{ font-size:20px; opacity:.88; margin-top:8px; }}
        .mode-pill {{ display:inline-block; background:rgba(255,255,255,.20); padding:10px 16px; border-radius:999px; margin-top:14px; font-weight:900; backdrop-filter:blur(8px); }}
        .metric {{ font-size: clamp(36px, 5vw, 76px); font-weight: 900; letter-spacing:-.05em; color:{accent}; line-height:1; }}
        .label {{ text-transform:uppercase; letter-spacing:.14em; font-size:13px; font-weight:900; color:#557086; }}
        .big-title {{ font-size: clamp(30px, 4.2vw, 62px); font-weight: 950; letter-spacing:-.045em; color:#102033; line-height:1.02; margin-bottom:12px; }}
        .body-large {{ font-size: clamp(22px, 2.4vw, 38px); line-height:1.22; color:#20364d; }}
        .announcement {{ border-left: 10px solid #1b75bb; padding:18px 20px; border-radius:18px; background:#f8fbff; margin-bottom:14px; }}
        .announcement.urgent {{ border-left-color:#dc3545; background:#fff5f5; }}
        .pill {{ display:inline-block; padding:7px 12px; border-radius:999px; background:#e8f3ff; color:{accent}; font-size:14px; font-weight:900; margin-right:8px; }}
        .pill-red {{ background:#ffe5e5; color:#b02a37; }}
        .event-row {{ padding:14px 0; border-bottom:1px solid rgba(15,76,129,.10); font-size:20px; }}
        .thought {{ font-size: clamp(28px, 3.2vw, 54px); font-weight:850; line-height:1.15; color:{accent}; }}
        .muted {{ color:#60758a; }}
        .image-frame {{ border-radius:28px; overflow:hidden; box-shadow:0 25px 80px rgba(0,0,0,.16); border:1px solid rgba(255,255,255,.5); animation: cardIn .7s ease both; }}
        .image-frame img {{ transition: transform 16s ease; }}
        .image-frame:hover img {{ transform: scale(1.04); }}
        .image-polaroid {{ background:white; padding:18px 18px 52px; border-radius:22px; transform:rotate(-1deg); box-shadow:0 22px 60px rgba(0,0,0,.16); }}
        .image-split {{ display:grid; grid-template-columns:1.1fr .9fr; gap:24px; align-items:center; }}
        .image-caption-card {{ font-size:clamp(24px,2.4vw,44px); font-weight:950; line-height:1.1; color:#102033; }}
        .caption {{ margin-top:-68px; position:relative; padding:18px 24px; color:white; font-size:26px; font-weight:850; background:linear-gradient(transparent, rgba(0,0,0,.65)); border-radius:0 0 28px 28px; }}
        .emergency {{
            min-height:82vh; display:grid; place-items:center; text-align:center; border-radius:36px; padding:70px;
            background: radial-gradient(circle at top, rgba(255,255,255,.22), transparent 40%), linear-gradient(135deg,#b00020,#e63946,#ff7b00);
            color:white; box-shadow:0 30px 90px rgba(176,0,32,.35);
        }}
        .emergency h1 {{ font-size: clamp(48px, 8vw, 120px); line-height:.95; margin:0 0 28px; letter-spacing:-.06em; }}
        .emergency p {{ font-size: clamp(30px, 4vw, 68px); line-height:1.12; margin:0; font-weight:780; }}
        .footer-note {{ text-align:center; color:#6b8296; font-size:15px; margin-top:12px; }}
        .stButton>button {{ border-radius: 14px; font-weight: 850; }}
        div[data-testid="stMetricValue"] {{ font-size: 2.4rem; }}

        .proverb-card {{
            background:
              radial-gradient(circle at top left, rgba(255,200,87,.30), transparent 34%),
              linear-gradient(135deg, rgba(255,255,255,.96), rgba(238,247,255,.88));
            border:1px solid rgba(185,133,0,.22); border-radius:28px; padding:26px;
            box-shadow:0 18px 55px rgba(15,76,129,.12); position:relative; overflow:hidden;
            animation: cardIn .7s ease both;
        }}
        .proverb-card:before {{ content:"❦"; position:absolute; right:18px; top:4px; font-size:72px; opacity:.08; color:{accent}; }}
        .proverb-text {{ font-size:clamp(26px,3vw,48px); line-height:1.08; font-weight:950; color:#102033; letter-spacing:-.03em; }}
        .proverb-meaning {{ margin-top:14px; font-size:clamp(18px,1.6vw,25px); color:#40576e; line-height:1.25; }}
        .screen-ticker {{ position:fixed; left:24px; right:24px; bottom:16px; z-index:999; border-radius:999px; padding:10px 18px; background:rgba(16,32,51,.86); color:#fff; box-shadow:0 15px 45px rgba(0,0,0,.18); overflow:hidden; backdrop-filter:blur(10px); }}
        .ticker-inner {{ white-space:nowrap; display:inline-block; padding-left:100%; animation:ticker 38s linear infinite; font-weight:850; letter-spacing:.02em; }}
        @keyframes fadeSlideIn {{ from {{ opacity:0; transform:translateY(-16px); }} to {{ opacity:1; transform:translateY(0); }} }}
        @keyframes cardIn {{ from {{ opacity:0; transform:translateY(22px) scale(.985); }} to {{ opacity:1; transform:translateY(0) scale(1); }} }}
        @keyframes shimmer {{ 0%,55% {{ transform:translateX(-70%); }} 75%,100% {{ transform:translateX(70%); }} }}
        @keyframes ticker {{ from {{ transform:translateX(0); }} to {{ transform:translateX(-100%); }} }}
        @media (max-width: 900px) {{
          .topbar {{ flex-direction:column; }} .clock {{ text-align:left; }} .logo-badge {{ width:96px; height:74px; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(ttl=900, show_spinner=False)
def get_weather_cached(lat, lon):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,weather_code,wind_speed_10m,wind_gusts_10m,precipitation",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "timezone": "auto",
        "forecast_days": 1,
    }
    r = requests.get(url, params=params, timeout=8)
    r.raise_for_status()
    return r.json()


def get_weather(settings):
    try:
        data = get_weather_cached(settings.get("weather_lat", "63.9331"), settings.get("weather_lon", "-20.9971"))
        current = data.get("current", {})
        daily = data.get("daily", {})
        return {
            "ok": True,
            "temp": current.get("temperature_2m"),
            "wind": current.get("wind_speed_10m"),
            "gust": current.get("wind_gusts_10m"),
            "precip": current.get("precipitation"),
            "code": current.get("weather_code"),
            "max": (daily.get("temperature_2m_max") or [None])[0],
            "min": (daily.get("temperature_2m_min") or [None])[0],
            "rain_sum": (daily.get("precipitation_sum") or [None])[0],
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def weather_text(code):
    mapping = {
        0: "Heiðskírt", 1: "Léttskýjað", 2: "Hálfskýjað", 3: "Skýjað",
        45: "Þoka", 48: "Hrímþoka", 51: "Lítil súld", 53: "Súld", 55: "Mikil súld",
        61: "Lítil rigning", 63: "Rigning", 65: "Mikil rigning", 71: "Lítil snjókoma",
        73: "Snjókoma", 75: "Mikil snjókoma", 80: "Skúrir", 81: "Skúrir", 82: "Miklir skúrir",
        95: "Þrumuveður", 96: "Þrumuveður með hagli", 99: "Þrumuveður með hagli",
    }
    return mapping.get(code, "Veður")


def clothing_tip(weather):
    if not weather.get("ok"):
        return "Veðurupplýsingar náðust ekki — athugið útiveru eftir aðstæðum."
    temp = weather.get("temp") or 0
    wind = weather.get("wind") or 0
    rain = weather.get("rain_sum") or 0
    tips = []
    if temp <= 0:
        tips.append("Kuldagalli, húfa og vettlingar eru góð hugmynd.")
    elif temp <= 6:
        tips.append("Munið hlý föt í frímínútum.")
    elif temp <= 12:
        tips.append("Jakki eða peysa hentar vel í dag.")
    else:
        tips.append("Útivera ætti að vera þægileg með léttum útifötum.")
    if wind >= 12:
        tips.append("Það er nokkuð hvasst — passið laus plögg.")
    if rain and rain > 1:
        tips.append("Regnföt gætu komið sér vel.")
    return " ".join(tips)



def get_mode_key(mode):
    return re.sub(r"[^A-Za-z0-9_ÁÉÍÓÚÝÞÆÖáéíóúýþæö-]", "_", mode or "Sjálfvirkt")


def get_editor_blocks(settings, mode):
    raw = settings.get(f"editor_blocks_{get_mode_key(mode)}", "")
    if raw:
        try:
            blocks = json.loads(raw)
            return [b for b in blocks if b in BLOCKS]
        except Exception:
            pass
    return DEFAULT_BLOCKS_BY_MODE.get(mode, DEFAULT_BLOCKS_BY_MODE["Sjálfvirkt"])


def get_editor_seconds(settings, mode):
    try:
        return int(settings.get(f"editor_seconds_{get_mode_key(mode)}", settings.get("slide_seconds", "12")) or 12)
    except Exception:
        return 12


def get_editor_theme(settings, mode):
    theme = settings.get(f"editor_theme_{get_mode_key(mode)}", "")
    if theme in THEMES:
        return theme
    if mode == "Matsalur":
        return "Grænn matsalur"
    if mode == "Kennarastofa":
        return "Fjólublár kennari"
    return "Blár Vallaskóli"


def get_theme_accent(settings, mode):
    return THEMES.get(get_editor_theme(settings, mode), "#0f4c81")



PROVERBS = [
    ("Betra er seint en aldrei.", "Það er betra að gera gott verk seint en að gera það aldrei."),
    ("Margt smátt gerir eitt stórt.", "Mörg lítil skref geta saman orðið að stórum árangri."),
    ("Ekki er allt gull sem glóir.", "Það sem virðist flott er ekki alltaf best eða rétt."),
    ("Æfingin skapar meistarann.", "Við verðum betri með því að æfa okkur aftur og aftur."),
    ("Enginn verður óbarinn biskup.", "Það þarf oft vinnu og reynslu til að ná góðum árangri."),
    ("Betri er einn fugl í hendi en tveir í skógi.", "Það sem við höfum öruggt getur verið betra en óviss von."),
    ("Góð byrjun er hálfnað verk.", "Þegar við byrjum vel verður verkefnið auðveldara."),
    ("Oft má satt kyrrt liggja.", "Stundum er betra að hugsa áður en maður talar."),
    ("Sá sem spyr, lærir.", "Spurningar hjálpa okkur að skilja betur."),
    ("Það læra börnin sem fyrir þeim er haft.", "Við lærum mikið af fyrirmyndum okkar."),
    ("Drjúgt er það sem drýpur.", "Smá vinna á hverjum degi skilar miklu með tímanum."),
    ("Viljinn dregur hálft hlass.", "Áhugi og jákvætt hugarfar hjálpa okkur áfram."),
    ("Samhentir kraftar flytja fjöll.", "Þegar við vinnum saman getum við gert stóra hluti."),
    ("Hver er sinnar gæfu smiður.", "Við höfum áhrif á eigin árangur með vali okkar og vinnu."),
    ("Lengi býr að fyrstu gerð.", "Góð undirstaða skiptir miklu máli."),
]


def proverb_of_the_day():
    idx = date.today().toordinal() % len(PROVERBS)
    return PROVERBS[idx]


def render_proverb_card(compact=False):
    text, meaning = proverb_of_the_day()
    st.markdown('<div class="proverb-card">', unsafe_allow_html=True)
    st.markdown('<div class="label">Málsháttur / orðtak dagsins</div>', unsafe_allow_html=True)
    size = 'style="font-size:32px;"' if compact else ''
    st.markdown(f'<div class="proverb-text" {size}>“{h(text)}”</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="proverb-meaning"><b>Merking:</b> {h(meaning)}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


def render_ticker(settings, menu, announcements):
    if settings.get("show_ticker", "1") != "1":
        return
    parts = ["Vallaskóli"]
    if menu:
        parts.append(f"Í matinn í dag: {menu.get('title','')}")
    for a in announcements[:3]:
        parts.append(f"{a['title']}: {a['body']}")
    text = "  •  ".join([p for p in parts if p])
    st.markdown(f'<div class="screen-ticker"><div class="ticker-inner">{h(text)}</div></div>', unsafe_allow_html=True)



def image_row_value(img, key, default=""):
    try:
        value = img[key]
        return value if value is not None else default
    except Exception:
        return default


def filter_images_by_placement(images, placement):
    selected = []
    for img in images:
        p = image_row_value(img, "placement", "Aðalmyndasýning")
        if p in (placement, "Alls staðar"):
            selected.append(img)
    return selected or list(images)


def render_quickstats(settings, weather, events):
    st.markdown('<div class="hero-card">', unsafe_allow_html=True)
    st.markdown('<div class="label">Flýtikubbar</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="small-card">', unsafe_allow_html=True)
        st.markdown('<div class="label">Staður</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="font-size:32px;font-weight:900;">{h(settings.get("weather_place","Selfoss"))}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="small-card">', unsafe_allow_html=True)
        st.markdown('<div class="label">Útivera</div>', unsafe_allow_html=True)
        outdoor = "Já" if weather.get("ok") and (weather.get("wind") or 0) < 15 and (weather.get("rain_sum") or 0) < 5 else "Athuga"
        st.markdown(f'<div style="font-size:32px;font-weight:900;">{outdoor}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="small-card">', unsafe_allow_html=True)
        st.markdown('<div class="label">Næsti viðburður</div>', unsafe_allow_html=True)
        next_event = events[0]["title"] if events else "Óskráður"
        st.markdown(f'<div style="font-size:25px;font-weight:900;line-height:1.05;">{h(next_event)}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


def render_block_by_id(block_id, menu, weather, settings, announcements, events, thoughts, images, slide_seconds, mode):
    if block_id == "menu":
        render_menu_card(menu, mode)
    elif block_id == "weather":
        render_weather_card(weather, settings)
    elif block_id == "announcements":
        render_announcements(announcements, limit=5 if mode == "Kennarastofa" else 4)
    elif block_id == "images":
        render_image_panel(images, slide_seconds, settings.get(f"image_placement_{get_mode_key(mode)}", "Aðalmyndasýning"), settings.get(f"image_layout_{get_mode_key(mode)}", settings.get("image_layout_default", "Stór mynd + texti")))
    elif block_id == "events":
        render_events_panel(events)
    elif block_id == "thought":
        render_thought(thoughts)
    elif block_id == "proverb":
        render_proverb_card()
    elif block_id == "quickstats":
        render_quickstats(settings, weather, events)
    else:
        st.info("Óþekktur kubbur.")



def get_playlist_key(name):
    return get_mode_key(name or "Sjálfgefin")


def get_playlist_blocks(settings, playlist_name):
    defaults = DEFAULT_PLAYLISTS.get(playlist_name, DEFAULT_PLAYLISTS["Sjálfgefin"])["blocks"]
    raw = settings.get(f"playlist_blocks_{get_playlist_key(playlist_name)}", "")
    if raw:
        try:
            blocks = json.loads(raw)
            cleaned = [b for b in blocks if b in BLOCKS]
            return cleaned or defaults
        except Exception:
            pass
    return defaults


def get_playlist_seconds(settings, playlist_name):
    default = DEFAULT_PLAYLISTS.get(playlist_name, DEFAULT_PLAYLISTS["Sjálfgefin"])["seconds"]
    try:
        return int(settings.get(f"playlist_seconds_{get_playlist_key(playlist_name)}", default) or default)
    except Exception:
        return default


def get_playlist_theme(settings, playlist_name):
    default = DEFAULT_PLAYLISTS.get(playlist_name, DEFAULT_PLAYLISTS["Sjálfgefin"])["theme"]
    theme = settings.get(f"playlist_theme_{get_playlist_key(playlist_name)}", default)
    return theme if theme in THEMES else default


def resolve_playlist(settings):
    params = st.query_params
    query_playlist = params.get("playlist", "")
    if query_playlist in PLAYLISTS:
        return query_playlist
    if settings.get("playlist_schedule_enabled", "1") != "1":
        return settings.get("default_playlist", "Sjálfgefin") if settings.get("default_playlist", "Sjálfgefin") in PLAYLISTS else "Sjálfgefin"
    now = datetime.now().time()
    checks = [
        ("Morgunspilun", settings.get("playlist_morning_start", "07:30"), settings.get("playlist_morning_end", "10:30")),
        ("Hádegisspilun", settings.get("playlist_noon_start", "10:30"), settings.get("playlist_noon_end", "13:30")),
        ("Lok dags", settings.get("playlist_endday_start", "13:30"), settings.get("playlist_endday_end", "16:30")),
    ]
    for name, start, end in checks:
        try:
            s = datetime.strptime(start, "%H:%M").time()
            e = datetime.strptime(end, "%H:%M").time()
            if s <= now < e:
                return name
        except Exception:
            continue
    return settings.get("default_playlist", "Sjálfgefin") if settings.get("default_playlist", "Sjálfgefin") in PLAYLISTS else "Sjálfgefin"


def get_playlist_accent(settings, playlist_name):
    return THEMES.get(get_playlist_theme(settings, playlist_name), "#0f4c81")


def render_playlist_screen(settings, mode, playlist_name, menu, weather, announcements, events, thoughts, images):
    blocks = get_playlist_blocks(settings, playlist_name)
    if not blocks:
        blocks = DEFAULT_PLAYLISTS["Sjálfgefin"]["blocks"]
    slide_seconds = get_playlist_seconds(settings, playlist_name)
    idx = int(time.time() / max(5, slide_seconds)) % len(blocks)
    current = blocks[idx]
    next_blocks = [blocks[(idx + i) % len(blocks)] for i in range(1, min(4, len(blocks)) + 1)]

    left, right = st.columns([1.18, .82], gap="large")
    with left:
        render_block_by_id(current, menu, weather, settings, announcements, events, thoughts, images, slide_seconds, mode)
        dots = "".join(f'<span class="slide-dot {"active" if i == idx else ""}"></span>' for i in range(len(blocks)))
        st.markdown(f'<div class="slide-dots">{dots}</div>', unsafe_allow_html=True)
        st.caption(f"Spilunarlisti: {PLAYLISTS.get(playlist_name, playlist_name)} · Nú birtist: {BLOCKS.get(current, current)} · {slide_seconds} sek.")
    with right:
        st.markdown('<div class="slide-card">', unsafe_allow_html=True)
        st.markdown('<div class="label">Dagskrá skjásins</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="big-title" style="font-size:34px;">{h(PLAYLISTS.get(playlist_name, playlist_name))}</div>', unsafe_allow_html=True)
        st.markdown('<div class="label">Næst</div>', unsafe_allow_html=True)
        for b in next_blocks:
            st.markdown(f'<span class="block-chip">{h(BLOCKS.get(b,b))}</span>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<br>', unsafe_allow_html=True)
        if settings.get("show_proverb_all_screens", "1") == "1" and current != "proverb" and "proverb" not in blocks:
            render_proverb_card(compact=True)
            st.markdown('<br>', unsafe_allow_html=True)
        side_candidates = [b for b in ["proverb", "images", "events", "weather", "announcements", "menu"] if b in blocks and b != current]
        if side_candidates:
            render_block_by_id(side_candidates[0], menu, weather, settings, announcements, events, thoughts, images, slide_seconds, mode)

def render_editor_controlled_screen(settings, mode, menu, weather, announcements, events, thoughts, images):
    blocks = get_editor_blocks(settings, mode)
    if not blocks:
        blocks = DEFAULT_BLOCKS_BY_MODE.get(mode, DEFAULT_BLOCKS_BY_MODE["Sjálfvirkt"])
    slide_seconds = get_editor_seconds(settings, mode)
    idx = int(time.time() / max(5, slide_seconds)) % len(blocks)
    current = blocks[idx]
    next_blocks = [blocks[(idx + i) % len(blocks)] for i in range(1, min(3, len(blocks)) + 1)]

    left, right = st.columns([1.18, .82], gap="large")
    with left:
        render_block_by_id(current, menu, weather, settings, announcements, events, thoughts, images, slide_seconds, mode)
        dots = "".join(f'<span class="slide-dot {"active" if i == idx else ""}"></span>' for i in range(len(blocks)))
        st.markdown(f'<div class="slide-dots">{dots}</div>', unsafe_allow_html=True)
        st.caption(f"Nú birtist: {BLOCKS.get(current, current)} · skiptir á {slide_seconds} sekúndum")
    with right:
        st.markdown('<div class="slide-card">', unsafe_allow_html=True)
        st.markdown('<div class="label">Næst á skjá</div>', unsafe_allow_html=True)
        for b in next_blocks:
            st.markdown(f'<span class="block-chip">{h(BLOCKS.get(b,b))}</span>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<br>', unsafe_allow_html=True)
        # Sýnum alltaf nytsamlegan aukakubb við hliðina án þess að trufla aðalspilun.
        if settings.get("show_proverb_all_screens", "1") == "1" and current != "proverb" and "proverb" not in blocks:
            render_proverb_card(compact=True)
            st.markdown('<br>', unsafe_allow_html=True)
        side_candidates = [b for b in ["proverb", "images", "events", "weather", "announcements", "menu"] if b in blocks and b != current]
        if side_candidates:
            render_block_by_id(side_candidates[0], menu, weather, settings, announcements, events, thoughts, images, slide_seconds, mode)

def topbar(settings, mode):
    now = datetime.now()
    school = settings.get("school_name", "Vallaskóli")
    subtitle = settings.get("subtitle", "Upplýsingaskjár")
    logo_url = settings.get("logo_url", "")
    logo_html = f'<img src="{h(logo_url)}" alt="Vallaskóli logo">' if logo_url else 'V'
    st.markdown(
        f"""
        <div class="topbar">
          <div class="brand">
            <div class="logo-badge">{logo_html}</div>
            <div>
              <div class="brand-title">{h(school)}</div>
              <div class="brand-sub">{h(subtitle)}</div>
              <div class="mode-pill">{h(mode)}</div>
            </div>
          </div>
          <div class="clock">
            <div class="clock-time">{now.strftime('%H:%M')}</div>
            <div class="clock-date">{WEEKDAYS[now.weekday()]} · {now.strftime('%d.%m.%Y')}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def parse_date_cell(value):
    txt = str(value or "").strip()
    if not txt:
        return None
    for fmt in ["%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%d.%m.%y", "%d/%m/%y"]:
        try:
            return datetime.strptime(txt, fmt).date()
        except ValueError:
            pass
    return None


def weekday_from_cell(value):
    txt = str(value or "").strip().lower()
    if not txt:
        return None
    for i, name in enumerate(WEEKDAYS):
        if txt.startswith(name.lower()[:3]) or txt.startswith(SHORT_WEEKDAYS[i]):
            return i
    return None



ICELANDIC_MONTHS = {
    "janúar": 1, "febrúar": 2, "mars": 3, "apríl": 4, "maí": 5, "júní": 6,
    "júlí": 7, "ágúst": 8, "september": 9, "október": 10, "nóvember": 11, "desember": 12,
}


def parse_icelandic_date_line(line):
    txt = str(line or "").strip().lower()
    m = re.search(r"(\d{1,2})\.\s*([a-záðéíóúýþæö]+)\s+(\d{4})", txt, re.I)
    if not m:
        return None
    day = int(m.group(1))
    month = ICELANDIC_MONTHS.get(m.group(2).lower())
    year = int(m.group(3))
    if not month:
        return None
    try:
        return date(year, month, day)
    except ValueError:
        return None


def is_probably_menu_text(line):
    txt = str(line or "").strip()
    low = txt.lower()
    if not txt or len(txt) < 3:
        return False
    if low in {"•", "prenta", "search", "main menu", "skip to content", "sun mán þri mið fim fös lau"}:
        return False
    if low.startswith("see more details") or low.startswith("image"):
        return False
    if re.fullmatch(r"\d{1,2}", txt):
        return False
    if parse_icelandic_date_line(txt):
        return False
    if re.fullmatch(r"[a-záðéíóúýþæö]+\s+\d{4}", low):
        return False
    if "vallaskóli er hnetulaus" in low:
        return False
    return True


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_vallaskoli_web_menu(menu_url):
    """Sækir matseðil af vallaskoli.is/skolinn/matsedill/.
    Síðan er birt sem dagatal; við lesum textalínur og tengjum rétt við dagsetningu.
    """
    if not menu_url:
        return {"ok": False, "error": "Engin matseðilsslóð skráð."}
    r = requests.get(menu_url, timeout=12, headers={"User-Agent": "VallaskoliSkjar/1.4"})
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    lines = [x.strip() for x in soup.get_text("\n").splitlines() if x.strip()]
    items = []
    seen = set()
    for i, line in enumerate(lines):
        d = parse_icelandic_date_line(line)
        if not d:
            continue
        meal = ""
        # Algengasta uppsetningin: maturinn stendur á línunni rétt á undan dagsetningu.
        for j in range(i - 1, max(-1, i - 10), -1):
            candidate = lines[j].strip().lstrip("*•- ").strip()
            if is_probably_menu_text(candidate):
                meal = candidate
                break
        if meal and (d.isoformat(), meal) not in seen:
            items.append({"date": d, "title": meal, "description": "Vallaskóli er hnetulaus skóli.", "source": "Vallaskóli vefur"})
            seen.add((d.isoformat(), meal))
    today = date.today()
    today_item = next((x for x in items if x["date"] == today), None)
    upcoming = [x for x in items if x["date"] >= today]
    latest = max([x["date"] for x in items], default=None)
    earliest = min([x["date"] for x in items], default=None)
    return {
        "ok": True,
        "today": today_item,
        "items": items,
        "upcoming": upcoming[:10],
        "count": len(items),
        "earliest": earliest.isoformat() if earliest else "",
        "latest": latest.isoformat() if latest else "",
        "url": menu_url,
    }


@st.cache_data(ttl=600, show_spinner=False)
def fetch_google_sheet_menu(csv_url, date_col, weekday_col, title_col, desc_col):
    if not csv_url:
        return {"ok": False, "error": "Engin Google Sheets CSV slóð skráð."}
    r = requests.get(csv_url, timeout=10)
    r.raise_for_status()
    text = r.content.decode("utf-8-sig", errors="replace")
    rows = list(csv.DictReader(StringIO(text)))
    today = date.today()
    today_weekday = today.weekday()
    chosen = None
    fallback = None
    week_items = []

    for row in rows:
        title = (row.get(title_col) or "").strip()
        desc = (row.get(desc_col) or "").strip() if desc_col else ""
        if not title:
            continue
        row_date = parse_date_cell(row.get(date_col)) if date_col else None
        row_weekday = weekday_from_cell(row.get(weekday_col)) if weekday_col else None
        item = {"title": title, "description": desc, "date": row_date, "weekday": row_weekday}
        week_items.append(item)
        if row_date == today:
            chosen = item
        if row_weekday == today_weekday and fallback is None:
            fallback = item
    return {"ok": True, "today": chosen or fallback, "items": week_items, "count": len(week_items)}


def get_menu(settings):
    # 1. Reynir fyrst matseðil beint af Vallaskóla vefnum, ef virkt.
    if settings.get("vallaskoli_menu_enabled", "1") == "1" and settings.get("vallaskoli_menu_url", ""):
        try:
            data = fetch_vallaskoli_web_menu(settings.get("vallaskoli_menu_url", ""))
            if data.get("ok") and data.get("today"):
                today_item = data["today"]
                return {"title": today_item["title"], "description": today_item.get("description", ""), "source": "Vallaskóli vefur"}
        except Exception:
            # Föllum hljóðlega á næstu heimild svo skjárinn verði aldrei auður.
            pass

    # 2. Google Sheets varaheimild.
    if settings.get("sheets_enabled", "0") == "1" and settings.get("sheets_csv_url", ""):
        try:
            data = fetch_google_sheet_menu(
                settings.get("sheets_csv_url", ""),
                settings.get("sheets_date_column", "Dagsetning"),
                settings.get("sheets_weekday_column", "Dagur"),
                settings.get("sheets_title_column", "Matur"),
                settings.get("sheets_description_column", "Lýsing"),
            )
            if data.get("ok") and data.get("today"):
                return {"title": data["today"]["title"], "description": data["today"].get("description", ""), "source": "Google Sheets"}
        except Exception:
            pass

    # 3. Handvirkur matseðill er loka-varaáætlun.
    menu = db.get_menu_today()
    if menu:
        return {"title": menu["title"], "description": menu["description"], "source": "Handvirkt"}
    return {"title": "Matseðill óskráður", "description": "Settu inn matseðil í stjórnborði.", "source": "Handvirkt"}


def unfold_ics(text):
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    out = []
    for line in lines:
        if line.startswith(" ") or line.startswith("\t"):
            if out:
                out[-1] += line[1:]
        else:
            out.append(line)
    return out


def clean_ics_text(value):
    return (value or "").replace("\\n", " ").replace("\\,", ",").replace("\\;", ";").replace("\\\\", "\\").strip()


def parse_ics_date(raw):
    if not raw:
        return None
    value = raw.split(":", 1)[-1].strip()
    try:
        if len(value) == 8 and value.isdigit():
            return datetime.strptime(value, "%Y%m%d")
        if value.endswith("Z"):
            return datetime.strptime(value, "%Y%m%dT%H%M%SZ")
        if "T" in value:
            return datetime.strptime(value[:15], "%Y%m%dT%H%M%S")
    except Exception:
        return None
    return None


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_calendar_events(ics_url, days_ahead=30):
    if not ics_url:
        return {"ok": False, "error": "Engin iCal slóð skráð."}
    r = requests.get(ics_url, timeout=10)
    r.raise_for_status()
    lines = unfold_ics(r.text)
    events = []
    current = None
    now = datetime.now()
    end = now + timedelta(days=int(days_ahead or 30))
    for line in lines:
        if line == "BEGIN:VEVENT":
            current = {}
        elif line == "END:VEVENT" and current is not None:
            start = parse_ics_date(current.get("DTSTART"))
            if start and start.date() >= date.today() and start <= end:
                events.append({
                    "title": clean_ics_text(current.get("SUMMARY", "Viðburður")),
                    "event_date": start.date().isoformat(),
                    "event_time": "" if start.hour == 0 and start.minute == 0 else start.strftime("%H:%M"),
                    "location": clean_ics_text(current.get("LOCATION", "")),
                    "source": "Google Calendar",
                })
            current = None
        elif current is not None:
            key = line.split(":", 1)[0].split(";", 1)[0]
            if key in ["DTSTART", "SUMMARY", "LOCATION"]:
                current[key] = line
    events.sort(key=lambda e: (e["event_date"], e["event_time"]))
    return {"ok": True, "events": events[:12], "count": len(events)}


def is_probably_event_title(line):
    txt = str(line or "").strip()
    low = txt.lower()
    if not txt or len(txt) < 3:
        return False
    blocked = {
        "vallaskóli", "viðburðadagatal", "skólinn", "leit", "search", "main menu",
        "skip to content", "fyrri", "næsti", "næsta", "í dag", "dagatal",
        "listi", "mánuður", "vika", "dagur", "export events", "subscribe to calendar",
    }
    if low in blocked:
        return False
    if low.startswith("see more details") or low.startswith("image"):
        return False
    if re.fullmatch(r"\d{1,2}", txt):
        return False
    if parse_icelandic_date_line(txt):
        return False
    if re.fullmatch(r"[a-záðéíóúýþæö]+\s+\d{4}", low):
        return False
    if any(x in low for x in ["cookie", "persónuvernd", "sími", "netfang", "sólvöllum", "800 selfossi"]):
        return False
    return True


def parse_event_time(line):
    txt = str(line or "")
    m = re.search(r"(\d{1,2}:\d{2})", txt)
    return m.group(1) if m else ""


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_vallaskoli_web_events(events_url, days_ahead=90):
    """Sækir viðburði af Vallaskóli viðburðadagatalssíðu.
    Þetta er viljandi umburðarlynt: ef vefurinn breytir HTML uppsetningu reynum við
    að lesa dagsetningar úr texta og finna næsta líklega viðburðarheiti í kring.
    """
    if not events_url:
        return {"ok": False, "error": "Engin viðburðaslóð skráð."}
    r = requests.get(events_url, timeout=12, headers={"User-Agent": "VallaskoliSkjar/1.6"})
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    # Fyrst reynum við hefðbundin viðburðakort ef WordPress/The Events Calendar er notað.
    candidates = []
    for card in soup.select("article, .tribe-events-calendar-list__event, .tribe-common-g-row, .event, .type-tribe_events"):
        text = card.get_text("\n", strip=True)
        if not text:
            continue
        lines = [x.strip() for x in text.splitlines() if x.strip()]
        found_date = None
        title = ""
        tm = ""
        for line in lines:
            found_date = found_date or parse_icelandic_date_line(line)
            tm = tm or parse_event_time(line)
        for line in lines[:8]:
            if is_probably_event_title(line):
                title = line
                break
        if found_date and title:
            candidates.append({"date": found_date, "title": title, "time": tm})

    # Síðan almenn textagreining sem virkar á flestum dagatalssíðum.
    lines = [x.strip() for x in soup.get_text("\n").splitlines() if x.strip()]
    for i, line in enumerate(lines):
        d = parse_icelandic_date_line(line)
        if not d:
            continue
        title = ""
        tm = parse_event_time(line)
        # Algengt: titill fyrir ofan dagsetningu; annars rétt fyrir neðan.
        for j in range(i - 1, max(-1, i - 8), -1):
            cand = lines[j].strip().lstrip("*•- ").strip()
            if is_probably_event_title(cand):
                title = cand
                break
        if not title:
            for j in range(i + 1, min(len(lines), i + 8)):
                cand = lines[j].strip().lstrip("*•- ").strip()
                if is_probably_event_title(cand):
                    title = cand
                    break
        if title:
            candidates.append({"date": d, "title": title, "time": tm})

    today = date.today()
    end = today + timedelta(days=int(days_ahead or 90))
    seen = set()
    events = []
    for item in candidates:
        d = item["date"]
        title = re.sub(r"\s+", " ", item["title"]).strip()
        if not title or not (today <= d <= end):
            continue
        key = (d.isoformat(), title.lower())
        if key in seen:
            continue
        seen.add(key)
        events.append({
            "title": title,
            "event_date": d.isoformat(),
            "event_time": item.get("time", ""),
            "location": "Vallaskóli",
            "source": "Vallaskóli vefur",
        })
    events.sort(key=lambda e: (e["event_date"], e.get("event_time", ""), e["title"]))
    return {"ok": True, "events": events[:20], "count": len(events), "url": events_url}

def get_events(settings):
    manual = [dict(e) for e in db.list_events(upcoming_only=True, limit=8)]
    sources = []

    # 1. Vallaskóli viðburðadagatal af heimasíðu.
    if settings.get("vallaskoli_events_enabled", "1") == "1" and settings.get("vallaskoli_events_url", ""):
        try:
            web_events = fetch_vallaskoli_web_events(
                settings.get("vallaskoli_events_url", ""),
                settings.get("vallaskoli_events_days_ahead", settings.get("calendar_days_ahead", "90")),
            )
            if web_events.get("ok"):
                sources.extend(web_events.get("events", []))
        except Exception:
            pass

    # 2. Google Calendar iCal sem aukaheimild.
    if settings.get("calendar_enabled", "0") == "1" and settings.get("calendar_ics_url", ""):
        try:
            cal = fetch_calendar_events(settings.get("calendar_ics_url"), settings.get("calendar_days_ahead", "30"))
            if cal.get("ok"):
                sources.extend(cal.get("events", []))
        except Exception:
            pass

    merged = sources + manual
    merged.sort(key=lambda e: (e.get("event_date", "9999"), e.get("event_time", ""), e.get("title", "")))
    return merged[:10]


def get_effective_mode(settings):
    params = st.query_params
    query_mode = params.get("mode", "")
    if query_mode in SCREEN_MODES:
        return query_mode
    stored = settings.get("screen_mode", "Sjálfvirkt")
    if stored != "Sjálfvirkt":
        return stored
    hour = datetime.now().hour
    if 10 <= hour <= 13:
        return "Matsalur"
    if 14 <= hour <= 16:
        return "Kennarastofa"
    return "Anddyri"


def render_menu_card(menu, mode):
    label = "Í matinn í dag" if mode != "Kennarastofa" else "Starfsfólk / matur dagsins"
    st.markdown('<div class="hero-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="label">{label} · {h(menu.get("source", ""))}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="big-title">{h(menu.get("title"))}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="body-large">{h(menu.get("description"))}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


def render_weather_card(weather, settings):
    st.markdown('<div class="hero-card">', unsafe_allow_html=True)
    st.markdown('<div class="label">Veðrið núna</div>', unsafe_allow_html=True)
    if weather["ok"]:
        st.markdown(f'<div class="metric">{weather["temp"]:.1f}°C</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="body-large">{weather_text(weather.get("code"))} · Vindur {weather.get("wind",0):.0f} km/klst</div>', unsafe_allow_html=True)
        st.markdown(f'<p class="muted" style="font-size:24px;">{h(clothing_tip(weather))}</p>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="big-title">Veðurupplýsingar náðust ekki</div>', unsafe_allow_html=True)
        st.markdown('<div class="body-large">Skjárinn reynir aftur síðar.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


def render_announcements(announcements, limit=4):
    st.markdown('<div class="hero-card">', unsafe_allow_html=True)
    st.markdown('<div class="label">Tilkynningar</div>', unsafe_allow_html=True)
    if announcements:
        for a in announcements[:limit]:
            cls = "announcement urgent" if a["priority"] == "Áríðandi" else "announcement"
            pill = "pill pill-red" if a["priority"] == "Áríðandi" else "pill"
            st.markdown(
                f'<div class="{cls}"><span class="{pill}">{h(a["priority"])}</span><span class="pill">{h(a["category"])}</span><h2 style="margin:.35rem 0 .2rem;font-size:34px;">{h(a["title"])}</h2><div style="font-size:25px;line-height:1.22;">{h(a["body"])}</div></div>',
                unsafe_allow_html=True,
            )
    else:
        st.markdown('<div class="body-large">Engar virkar tilkynningar í dag.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


def render_thought(thoughts):
    st.markdown('<div class="hero-card">', unsafe_allow_html=True)
    st.markdown('<div class="label">Góð hugsun dagsins</div>', unsafe_allow_html=True)
    txt = random.choice(thoughts)["text"] if thoughts else "Eigum góðan dag saman."
    st.markdown(f'<div class="thought">“{h(txt)}”</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


def render_image_panel(images, slide_seconds, placement="Aðalmyndasýning", layout="Sjálfvirkt"):
    images = filter_images_by_placement(images, placement)
    if images:
        img = images[int(time.time() / max(7, slide_seconds)) % len(images)]
        path = UPLOAD_DIR / img["filename"]
        caption = image_row_value(img, "caption", "")
        if path.exists():
            if layout == "Mynd + textaspjald" and caption:
                st.markdown('<div class="slide-card image-split">', unsafe_allow_html=True)
                st.image(str(path), use_container_width=True)
                st.markdown(f'<div class="image-caption-card">{h(caption)}</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            elif layout == "Polaroid":
                st.markdown('<div class="image-polaroid">', unsafe_allow_html=True)
                st.image(str(path), use_container_width=True)
                if caption:
                    st.markdown(f'<div style="font-size:24px;font-weight:850;color:#102033;margin-top:10px;text-align:center;">{h(caption)}</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="image-frame">', unsafe_allow_html=True)
                st.image(str(path), use_container_width=True)
                if caption:
                    st.markdown(f'<div class="caption">{h(caption)}</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            return
    st.markdown('<div class="slide-card">', unsafe_allow_html=True)
    st.markdown('<div class="label">Myndasýning</div>', unsafe_allow_html=True)
    st.markdown('<div class="big-title">Bættu við myndum í stjórnborði</div>', unsafe_allow_html=True)
    st.markdown('<div class="body-large">Hér birtast myndir úr skólastarfi, verkefnum og viðburðum.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


def render_events_panel(events):
    st.markdown('<div class="slide-card">', unsafe_allow_html=True)
    st.markdown('<div class="label">Framundan</div>', unsafe_allow_html=True)
    if events:
        for e in events[:6]:
            try:
                d = datetime.fromisoformat(e["event_date"]).strftime("%d.%m")
            except Exception:
                d = e.get("event_date", "")
            t = f" · {h(e.get('event_time',''))}" if e.get("event_time") else ""
            loc = f"<br><span class='muted'>{h(e.get('location',''))}</span>" if e.get("location") else ""
            source = f" <span class='pill'>{h(e.get('source',''))}</span>" if e.get("source") else ""
            st.markdown(f'<div class="event-row"><b>{d}{t}</b>{source}<br>{h(e.get("title", "Viðburður"))}{loc}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="font-size:24px;">Engir viðburðir skráðir.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


def screen_page():
    settings = db.get_settings()
    device = get_device_from_query()
    mode = device.get("mode") if device else get_effective_mode(settings)
    if mode not in SCREEN_MODES:
        mode = "Anddyri"
    query_playlist = st.query_params.get("playlist", "")
    if query_playlist in PLAYLISTS:
        playlist_name = query_playlist
    elif device and device.get("playlist") and device.get("playlist") != "Sjálfvirkt" and device.get("playlist") in PLAYLISTS:
        playlist_name = device.get("playlist")
    else:
        playlist_name = resolve_playlist(settings)
    accent = get_playlist_accent(settings, playlist_name) if settings.get("use_playlists", "1") == "1" else get_theme_accent(settings, mode)
    css(mode, accent)
    refresh = int(settings.get("screen_refresh_seconds", "60") or 60)
    st_autorefresh(interval=max(10, refresh) * 1000, key="screen_refresh")

    if settings.get("emergency_active", "0") == "1":
        st.markdown(
            f"""
            <div class="emergency">
              <div>
                <h1>{h(settings.get('emergency_title','Áríðandi skilaboð'))}</h1>
                <p>{h(settings.get('emergency_body',''))}</p>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    topbar(settings, mode)
    menu = get_menu(settings)
    announcements = sorted(db.list_announcements(active_only=True), key=lambda r: PRIORITY_ORDER.get(r["priority"], 1), reverse=True)
    events = get_events(settings)
    thoughts = db.list_thoughts(active_only=True)
    images = db.list_images_for_mode(mode, active_only=True)
    weather = get_weather(settings)
    slide_seconds = int(settings.get("slide_seconds", "12") or 12)

    if settings.get("use_playlists", "1") == "1":
        render_playlist_screen(settings, mode, playlist_name, menu, weather, announcements, events, thoughts, images)
        render_ticker(settings, menu, announcements)
    elif settings.get("use_screen_editor", "1") == "1":
        render_editor_controlled_screen(settings, mode, menu, weather, announcements, events, thoughts, images)
    elif mode == "Matsalur":
        left, right = st.columns([1.05, .95], gap="large")
        with left:
            render_menu_card(menu, mode)
            st.markdown("<br>", unsafe_allow_html=True)
            render_thought(thoughts)
            render_proverb_card()
        with right:
            render_announcements(announcements, limit=3)
            st.markdown("<br>", unsafe_allow_html=True)
            render_weather_card(weather, settings)
    elif mode == "Kennarastofa":
        left, right = st.columns([1, 1], gap="large")
        with left:
            render_announcements(announcements, limit=5)
            st.markdown("<br>", unsafe_allow_html=True)
            render_events_panel(events)
        with right:
            render_weather_card(weather, settings)
            st.markdown("<br>", unsafe_allow_html=True)
            render_menu_card(menu, mode)
    else:
        slide_index = int(time.time() / max(5, slide_seconds)) % 4
        left, right = st.columns([1.15, .85], gap="large")
        with left:
            if slide_index == 0:
                render_menu_card(menu, mode)
            elif slide_index == 1:
                render_weather_card(weather, settings)
            elif slide_index == 2:
                render_announcements(announcements, limit=4)
            else:
                render_thought(thoughts)
            st.markdown("<br>", unsafe_allow_html=True)
            render_quickstats(settings, weather, events)
        with right:
            render_image_panel(images, slide_seconds, settings.get(f"image_placement_{get_mode_key(mode)}", "Aðalmyndasýning"), settings.get(f"image_layout_{get_mode_key(mode)}", settings.get("image_layout_default", "Stór mynd + texti")))
            st.markdown("<br>", unsafe_allow_html=True)
            render_events_panel(events)

    device_label = f" · {h(device.get('code'))}" if device else ""
    st.markdown(f'<div class="footer-note">Vallaskóli Skjár {VERSION} · {h(mode)}{device_label} · {h(PLAYLISTS.get(playlist_name, playlist_name) if settings.get("use_playlists", "1") == "1" else "Skjáritstjóri")} · Uppfærist sjálfkrafa</div>', unsafe_allow_html=True)


def login_box():
    settings = db.get_settings()
    st.title("🔐 Stjórnborð")
    with st.form("login"):
        password = st.text_input("Lykilorð", type="password")
        ok = st.form_submit_button("Innskrá")
    if ok:
        if password == settings.get("admin_password", "vallaskoli123"):
            st.session_state["admin"] = True
            st.rerun()
        else:
            st.error("Rangt lykilorð.")



def screen_url(mode=None, playlist=None, device=None):
    parts = ["view=skjar"]
    if device:
        parts.append(f"device={quote(str(device))}")
    if mode:
        parts.append(f"mode={quote(str(mode))}")
    if playlist:
        parts.append(f"playlist={quote(str(playlist))}")
    return "?" + "&".join(parts)


def get_public_base_url(settings):
    base = (settings.get("public_base_url", "") or "http://localhost:8501").strip().rstrip("/")
    return base or "http://localhost:8501"


def absolute_local_url(path):
    return "http://localhost:8501" + path


def absolute_public_url(path, settings):
    return get_public_base_url(settings) + path


def qr_image_for_url(url):
    img = qrcode.make(url)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def get_device_from_query():
    code = (st.query_params.get("device", "") or "").strip().upper()
    if not code:
        return None
    device = db.get_screen_device(code)
    if device and device["active"]:
        db.touch_screen_device(code)
        return dict(device)
    return None


def quick_announcement_templates():
    return {
        "Velkomin í dag": ("Velkomin í skólann", "Eigum góðan dag saman. Munið að ganga vel um og hjálpast að.", "Nemendur", "Venjulegt"),
        "Útiföt": ("Munið útiföt", "Það er gott að vera vel klædd í frímínútum í dag.", "Nemendur", "Mikilvægt"),
        "Matsalur": ("Matsalur", "Munið góðan skólabrag í matsalnum og ganga frá eftir ykkur.", "Matsalur", "Venjulegt"),
        "Foreldrar": ("Skilaboð til foreldra", "Nánari upplýsingar eru á heimasíðu skólans eða í tölvupósti frá skólanum.", "Foreldrar", "Venjulegt"),
        "Áríðandi": ("Áríðandi skilaboð", "Settu hér inn stutt og skýr skilaboð sem eiga að birtast á skjánum.", "Almennt", "Áríðandi"),
    }


def admin_home_dashboard(settings):
    st.subheader("Stjórnborðsheimili")
    st.caption("Hér eru algengustu aðgerðirnar á einum stað — hugsað fyrir þann sem þarf að uppfæra skjáinn hratt.")
    st.info("Nýtt í v1.9: sérslóðir skjáa vistast sjálfkrafa og myndir geta verið merktar á ákveðna skjái/staðsetningar.")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Virkar tilkynningar", len(db.list_announcements(active_only=True)))
    c2.metric("Viðburðir framundan", len(get_events(settings)))
    c3.metric("Myndir í sýningu", len(db.list_images(active_only=True)))
    c4.metric("Skjáhamur", settings.get("screen_mode", "Sjálfvirkt"))

    st.markdown("### Opna skjái")
    s1, s2, s3, s4 = st.columns(4)
    s1.link_button("📺 Aðalskjár", screen_url(), use_container_width=True)
    s2.link_button("🏫 Anddyri", screen_url("Anddyri"), use_container_width=True)
    s3.link_button("🍽️ Matsalur", screen_url("Matsalur"), use_container_width=True)
    s4.link_button("☕ Kennarastofa", screen_url("Kennarastofa"), use_container_width=True)

    st.markdown("### Fljótleg tilkynning")
    templates = quick_announcement_templates()
    with st.form("quick_announcement_form"):
        tcol, pcol = st.columns([2, 1])
        template_name = tcol.selectbox("Velja tilbúið sniðmát", list(templates.keys()))
        ttl, body, cat, pri = templates[template_name]
        priority = pcol.selectbox("Forgangur", ["Venjulegt", "Mikilvægt", "Áríðandi"], index=["Venjulegt", "Mikilvægt", "Áríðandi"].index(pri))
        title = st.text_input("Fyrirsögn", value=ttl)
        body_text = st.text_area("Texti", value=body, height=95)
        c1, c2 = st.columns(2)
        category = c1.selectbox("Flokkur", ["Almennt", "Nemendur", "Starfsfólk", "Foreldrar", "Viðburður", "Matsalur", "Anddyri"], index=max(0, ["Almennt", "Nemendur", "Starfsfólk", "Foreldrar", "Viðburður", "Matsalur", "Anddyri"].index(cat) if cat in ["Almennt", "Nemendur", "Starfsfólk", "Foreldrar", "Viðburður", "Matsalur", "Anddyri"] else 0))
        expires = c2.date_input("Gildir til", value=None)
        if st.form_submit_button("Birta tilkynningu strax", use_container_width=True):
            if title and body_text:
                db.add_announcement(title, body_text, category, priority, expires.isoformat() if expires else "")
                st.success("Tilkynningin er komin á skjáinn.")
                st.rerun()
            else:
                st.warning("Fyrirsögn og texti þurfa að vera til staðar.")

    st.markdown("### Flýtistýring skjás")
    e1, e2 = st.columns([1, 2])
    with e1:
        current_emergency = settings.get("emergency_active", "0") == "1"
        if current_emergency:
            if st.button("Slökkva á neyðarham", type="primary", use_container_width=True):
                db.set_setting("emergency_active", "0")
                st.rerun()
        else:
            st.info("Neyðarhamur er óvirkur.")
    with e2:
        st.markdown("<div class='admin-quick'><h3>Ábending</h3><div class='admin-muted'>Notaðu neyðarham aðeins fyrir skilaboð sem eiga að yfirtaka allan skjáinn. Fyrir venjuleg skilaboð er betra að nota fljótlega tilkynningu hér fyrir ofan.</div></div>", unsafe_allow_html=True)

    st.markdown("### Staða tenginga")
    t1, t2, t3 = st.columns(3)
    t1.success("Vallaskóli matseðill virkur" if settings.get("vallaskoli_menu_enabled", "1") == "1" else "Vallaskóli matseðill óvirkur")
    t2.success("Google Sheets virkt" if settings.get("sheets_enabled", "0") == "1" else "Google Sheets óvirkt")
    t3.success("Google Calendar virkt" if settings.get("calendar_enabled", "0") == "1" else "Google Calendar óvirkt")


def daily_editor(settings):
    st.subheader("Ofur einföld dagleg uppfærsla")
    st.caption("Ein síða fyrir það sem stjórnandi þarf oftast að breyta: matur, aðaltilkynning, mynd dagsins, hugsun og neyðarhamur.")

    menu = get_menu(settings)
    st.markdown(f"""
    <div class='daily-box'>
      <h3>🍽️ Matseðill dagsins</h3>
      <div class='admin-muted'>Núverandi heimild: <b>{h(menu.get('source'))}</b></div>
      <div style='font-size:26px;font-weight:900;margin-top:8px'>{h(menu.get('title'))}</div>
      <div class='admin-muted'>{h(menu.get('description'))}</div>
    </div>
    """, unsafe_allow_html=True)

    if settings.get("vallaskoli_menu_enabled", "1") == "1":
        try:
            web_menu = fetch_vallaskoli_web_menu(settings.get("vallaskoli_menu_url", ""))
            if web_menu.get("today"):
                st.success("Matseðill dagsins fannst á vef Vallaskóla.")
            else:
                st.warning(f"Vallaskóla matseðillinn náðist, en enginn réttur fannst fyrir daginn í dag. Síðan virðist innihalda tímabilið {web_menu.get('earliest') or '?'} til {web_menu.get('latest') or '?'}. Handvirki matseðillinn eða Google Sheets tekur þá við.")
        except Exception as e:
            st.warning(f"Náði ekki að lesa matseðil af vef Vallaskóla núna: {e}")

    with st.form("daily_menu_form"):
        st.markdown("#### Breyta handvirkum matseðli dagsins")
        today_row = db.get_menu_today()
        title = st.text_input("Réttur dagsins", value=today_row["title"] if today_row else "")
        desc = st.text_area("Lýsing / aukatexti", value=today_row["description"] if today_row else "", height=90)
        save_menu = st.form_submit_button("Vista handvirkan matseðil dagsins", use_container_width=True)
        if save_menu:
            db.upsert_menu(date.today().weekday(), title, desc)
            st.success("Matseðill dagsins vistaður sem varaáætlun/handvirkur matseðill.")
            st.rerun()

    st.divider()
    left, right = st.columns(2)
    with left:
        st.markdown("### 📣 Aðaltilkynning dagsins")
        with st.form("daily_main_announcement"):
            a_title = st.text_input("Fyrirsögn", value="Tilkynning dagsins")
            a_body = st.text_area("Texti", height=120, placeholder="Skrifaðu stutt skilaboð sem eiga að sjást á skjánum í dag.")
            a_priority = st.selectbox("Forgangur", ["Venjulegt", "Mikilvægt", "Áríðandi"], index=1)
            if st.form_submit_button("Birta tilkynningu dagsins", use_container_width=True):
                if a_title and a_body:
                    db.add_announcement(a_title, a_body, "Almennt", a_priority, date.today().isoformat())
                    st.success("Tilkynning dagsins er komin á skjáinn.")
                    st.rerun()
                else:
                    st.warning("Settu inn fyrirsögn og texta.")

        st.markdown("### 💬 Hugsun dagsins")
        with st.form("daily_thought"):
            thought = st.text_area("Texti", height=90, value="Við gerum okkar besta og hjálpum hvert öðru.")
            if st.form_submit_button("Bæta við hugsun", use_container_width=True):
                if thought:
                    db.add_thought(thought)
                    st.success("Hugsun bætt við.")
                    st.rerun()

    with right:
        st.markdown("### 🖼️ Mynd dagsins")
        uploaded = st.file_uploader("Veldu mynd", type=["png", "jpg", "jpeg", "webp"], key="daily_image_upload")
        caption = st.text_input("Myndatexti", key="daily_image_caption")
        target_modes_daily = st.multiselect("Hvar á mynd dagsins að birtast?", ["Allir", "Anddyri", "Matsalur", "Kennarastofa", "Sjálfvirkt"], default=["Allir"], key="daily_image_targets")
        placement_daily = st.selectbox("Staðsetning myndar", ["Aðalmyndasýning", "Hægri hlið", "Bakgrunnur/hero", "Alls staðar"], index=0, key="daily_image_place")
        if st.button("Setja mynd í myndasýningu", use_container_width=True):
            if uploaded:
                safe_name = f"{int(time.time())}_{uploaded.name.replace(' ', '_')}"
                out = UPLOAD_DIR / safe_name
                out.write_bytes(uploaded.getbuffer())
                try:
                    Image.open(out).verify()
                    db.add_image(safe_name, caption, target_modes_daily, placement_daily, 2)
                    st.success("Myndin er komin í myndasýninguna á valda skjái.")
                    st.rerun()
                except Exception:
                    out.unlink(missing_ok=True)
                    st.error("Ekki tókst að lesa myndina.")
            else:
                st.warning("Veldu mynd fyrst.")

        st.markdown("### 🚨 Neyðarhamur")
        with st.form("daily_emergency"):
            active = st.checkbox("Virkja neyðarham", value=settings.get("emergency_active", "0") == "1")
            e_title = st.text_input("Fyrirsögn", value=settings.get("emergency_title", "Áríðandi skilaboð"))
            e_body = st.text_area("Skilaboð", value=settings.get("emergency_body", ""), height=90)
            if st.form_submit_button("Vista neyðarham", use_container_width=True):
                db.set_setting("emergency_active", "1" if active else "0")
                db.set_setting("emergency_title", e_title)
                db.set_setting("emergency_body", e_body)
                st.success("Neyðarhamur uppfærður.")
                st.rerun()

    st.divider()
    st.markdown("### 👀 Flýtiforskoðun")
    c1, c2, c3 = st.columns(3)
    c1.link_button("Opna Anddyri", screen_url("Anddyri"), use_container_width=True)
    c2.link_button("Opna Matsal", screen_url("Matsalur"), use_container_width=True)
    c3.link_button("Opna Kennarastofu", screen_url("Kennarastofa"), use_container_width=True)



def playlist_editor(settings):
    st.subheader("Skjáspilunarlisti og dagskrá dagsins")
    st.caption("Hér getur stjórnandi ákveðið hvað birtist á skjánum á morgnana, í hádeginu og í lok dags.")

    with st.form("playlist_master_settings"):
        c1, c2 = st.columns(2)
        use_playlists = c1.checkbox("Nota skjáspilunarlista", value=settings.get("use_playlists", "1") == "1")
        schedule_enabled = c2.checkbox("Skipta sjálfkrafa eftir tíma dags", value=settings.get("playlist_schedule_enabled", "1") == "1")
        default_playlist = st.selectbox("Sjálfgefinn spilunarlisti þegar engin tímasetning á við", list(PLAYLISTS.keys()), index=list(PLAYLISTS.keys()).index(settings.get("default_playlist", "Sjálfgefin")) if settings.get("default_playlist", "Sjálfgefin") in PLAYLISTS else 0)
        c1, c2, c3 = st.columns(3)
        m_start = c1.text_input("Morgun byrjar", value=settings.get("playlist_morning_start", "07:30"))
        m_end = c1.text_input("Morgun endar", value=settings.get("playlist_morning_end", "10:30"))
        n_start = c2.text_input("Hádegi byrjar", value=settings.get("playlist_noon_start", "10:30"))
        n_end = c2.text_input("Hádegi endar", value=settings.get("playlist_noon_end", "13:30"))
        e_start = c3.text_input("Lok dags byrjar", value=settings.get("playlist_endday_start", "13:30"))
        e_end = c3.text_input("Lok dags endar", value=settings.get("playlist_endday_end", "16:30"))
        if st.form_submit_button("Vista dagskrá dagsins", use_container_width=True):
            for val in [m_start, m_end, n_start, n_end, e_start, e_end]:
                datetime.strptime(val, "%H:%M")
            db.set_setting("use_playlists", "1" if use_playlists else "0")
            db.set_setting("playlist_schedule_enabled", "1" if schedule_enabled else "0")
            db.set_setting("default_playlist", default_playlist)
            db.set_setting("playlist_morning_start", m_start)
            db.set_setting("playlist_morning_end", m_end)
            db.set_setting("playlist_noon_start", n_start)
            db.set_setting("playlist_noon_end", n_end)
            db.set_setting("playlist_endday_start", e_start)
            db.set_setting("playlist_endday_end", e_end)
            st.success("Dagskrá vistuð.")
            st.rerun()

    st.markdown("### Ritill fyrir spilunarlista")
    playlist_name = st.selectbox("Veldu spilunarlista", list(PLAYLISTS.keys()), format_func=lambda x: PLAYLISTS[x])
    blocks_now = get_playlist_blocks(settings, playlist_name)
    block_options = [""] + list(BLOCKS.keys())
    block_labels = {"": "— ekkert —", **BLOCKS}
    with st.form("playlist_editor_form"):
        c1, c2 = st.columns(2)
        theme = c1.selectbox("Þema", list(THEMES.keys()), index=list(THEMES.keys()).index(get_playlist_theme(settings, playlist_name)))
        seconds = c2.number_input("Sekúndur á hverjum kubb", min_value=5, max_value=120, value=get_playlist_seconds(settings, playlist_name), step=1)
        chosen = []
        cols = st.columns(2)
        for i in range(8):
            default = blocks_now[i] if i < len(blocks_now) else ""
            idx = block_options.index(default) if default in block_options else 0
            with cols[i % 2]:
                chosen.append(st.selectbox(f"Sæti {i+1}", block_options, index=idx, format_func=lambda x: block_labels.get(x, x), key=f"playlist_{get_playlist_key(playlist_name)}_{i}"))
        c1, c2 = st.columns(2)
        save = c1.form_submit_button("Vista spilunarlista", use_container_width=True)
        reset = c2.form_submit_button("Endurstilla", use_container_width=True)
        if save:
            cleaned = []
            for b in chosen:
                if b and b in BLOCKS and b not in cleaned:
                    cleaned.append(b)
            if not cleaned:
                cleaned = DEFAULT_PLAYLISTS.get(playlist_name, DEFAULT_PLAYLISTS["Sjálfgefin"])["blocks"]
            db.set_setting(f"playlist_blocks_{get_playlist_key(playlist_name)}", json.dumps(cleaned, ensure_ascii=False))
            db.set_setting(f"playlist_seconds_{get_playlist_key(playlist_name)}", str(seconds))
            db.set_setting(f"playlist_theme_{get_playlist_key(playlist_name)}", theme)
            st.success("Spilunarlisti vistaður.")
            st.rerun()
        if reset:
            d = DEFAULT_PLAYLISTS.get(playlist_name, DEFAULT_PLAYLISTS["Sjálfgefin"])
            db.set_setting(f"playlist_blocks_{get_playlist_key(playlist_name)}", json.dumps(d["blocks"], ensure_ascii=False))
            db.set_setting(f"playlist_seconds_{get_playlist_key(playlist_name)}", str(d["seconds"]))
            db.set_setting(f"playlist_theme_{get_playlist_key(playlist_name)}", d["theme"])
            st.success("Spilunarlisti endurstilltur.")
            st.rerun()

    saved = get_playlist_blocks(db.get_settings(), playlist_name)
    chips = "".join(f'<span class="block-chip">{h(BLOCKS.get(b,b))}</span>' for b in saved)
    st.markdown(f'<div class="playlist-card"><div class="label">Núverandi röð</div>{chips}</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.link_button("Forskoða í Anddyri", screen_url("Anddyri", playlist_name), use_container_width=True)
    c2.link_button("Forskoða í Matsal", screen_url("Matsalur", playlist_name), use_container_width=True)
    c3.link_button("Forskoða í Kennarastofu", screen_url("Kennarastofa", playlist_name), use_container_width=True)

    st.markdown("### Dagskrá dagsins")
    rows = [
        (settings.get("playlist_morning_start", "07:30") + "–" + settings.get("playlist_morning_end", "10:30"), "Morgunspilun"),
        (settings.get("playlist_noon_start", "10:30") + "–" + settings.get("playlist_noon_end", "13:30"), "Hádegisspilun"),
        (settings.get("playlist_endday_start", "13:30") + "–" + settings.get("playlist_endday_end", "16:30"), "Lok dags"),
    ]
    st.table([{"Tími": t, "Spilunarlisti": PLAYLISTS[p], "Kubbar": " → ".join(BLOCKS.get(b,b) for b in get_playlist_blocks(settings, p))} for t, p in rows])


def screen_devices_admin(settings):
    st.subheader("Skjápar og QR-tenging")
    st.caption("Búðu til auðkenni fyrir hvern skjá. Þá þarf aðeins að opna eina slóð eða skanna QR-kóða á skjátölvunni.")

    with st.form("public_base_url_form"):
        base_url = st.text_input(
            "Opinber grunnslóð vefsins",
            value=settings.get("public_base_url", "http://localhost:8501"),
            help="Á meðan þú keyrir á tölvunni: http://localhost:8501. Þegar vefurinn fer á Render: https://nafn-a-vef.onrender.com",
        )
        if st.form_submit_button("Vista grunnslóð", use_container_width=True):
            db.set_setting("public_base_url", base_url.strip().rstrip("/"))
            db.refresh_screen_device_urls()
            st.success("Grunnslóð vistuð og sérslóðir skjáa uppfærðar sjálfkrafa.")
            st.rerun()

    st.markdown("### Bæta við eða breyta skjá")
    playlist_options = ["Sjálfvirkt"] + list(PLAYLISTS.keys())
    with st.form("screen_device_form"):
        c1, c2 = st.columns(2)
        code = c1.text_input("Skjáauðkenni", placeholder="t.d. ANDDYRI-02").upper().replace(" ", "-")
        name = c2.text_input("Heiti skjás", placeholder="t.d. Anddyri aukaskjár")
        c3, c4, c5 = st.columns(3)
        location = c3.text_input("Staðsetning", placeholder="t.d. Anddyri")
        mode = c4.selectbox("Skjáhamur", ["Anddyri", "Matsalur", "Kennarastofa", "Sjálfvirkt"])
        playlist = c5.selectbox("Spilunarlisti", playlist_options)
        notes = st.text_area("Athugasemd", placeholder="t.d. tengdur við mini-tölvu við aðalinngang", height=80)
        active = st.checkbox("Skjár virkur", value=True)
        if st.form_submit_button("Vista skjá", use_container_width=True):
            if not code or not name:
                st.warning("Settu inn skjáauðkenni og heiti skjás.")
            else:
                db.upsert_screen_device(code, name, location, mode, playlist, active, notes)
                st.success("Skjár vistaður.")
                st.rerun()

    st.markdown("### Skráðir skjáir")
    devices = db.list_screen_devices(active_only=False)
    if not devices:
        st.info("Engir skjáir skráðir enn.")
        return

    for d in devices:
        device_url = screen_url(device=d["code"])
        full_url = d["url"] if "url" in d.keys() and d["url"] else absolute_public_url(device_url, settings)
        with st.container(border=True):
            c1, c2, c3 = st.columns([1.3, 1.1, .8])
            with c1:
                st.markdown(f"### {h(d['name'])}")
                st.caption(f"Auðkenni: `{d['code']}` · Staðsetning: {d['location'] or 'óskráð'} · Virkur: {'Já' if d['active'] else 'Nei'}")
                st.markdown(f"**Hamur:** {h(d['mode'])}  ")
                st.markdown(f"**Spilunarlisti:** {h(d['playlist'])}")
                if d["last_seen"]:
                    st.caption(f"Síðast séður: {d['last_seen']}")
                if d["notes"]:
                    st.write(d["notes"])
                st.markdown(f'<div class="url-box">{h(full_url)}</div>', unsafe_allow_html=True)
                st.link_button("Opna skjá", device_url, use_container_width=True)
            with c2:
                st.image(qr_image_for_url(full_url), caption="Skannaðu á skjátölvunni", width=230)
                st.code(full_url, language="text")
            with c3:
                with st.expander("Breyta"):
                    with st.form(f"edit_device_{d['code']}"):
                        ename = st.text_input("Heiti", value=d["name"], key=f"ename_{d['code']}")
                        elocation = st.text_input("Staðsetning", value=d["location"], key=f"eloc_{d['code']}")
                        emode = st.selectbox("Hamur", ["Anddyri", "Matsalur", "Kennarastofa", "Sjálfvirkt"], index=["Anddyri", "Matsalur", "Kennarastofa", "Sjálfvirkt"].index(d["mode"]) if d["mode"] in ["Anddyri", "Matsalur", "Kennarastofa", "Sjálfvirkt"] else 0, key=f"emode_{d['code']}")
                        eplaylist = st.selectbox("Spilunarlisti", playlist_options, index=playlist_options.index(d["playlist"]) if d["playlist"] in playlist_options else 0, key=f"epl_{d['code']}")
                        enotes = st.text_area("Athugasemd", value=d["notes"], key=f"enotes_{d['code']}")
                        eactive = st.checkbox("Virkur", value=bool(d["active"]), key=f"eactive_{d['code']}")
                        if st.form_submit_button("Vista breytingar"):
                            db.upsert_screen_device(d["code"], ename, elocation, emode, eplaylist, eactive, enotes)
                            st.success("Vistað.")
                            st.rerun()
                if st.button("Eyða skjá", key=f"delete_device_{d['code']}"):
                    db.delete_screen_device(d["code"])
                    st.rerun()

    st.markdown("### Fljótleg kiosk-skipun")
    st.code(f'chrome.exe --kiosk "{absolute_public_url(screen_url(device="ANDDYRI-01"), settings)}"', language="bash")
    st.caption("Skiptu ANDDYRI-01 út fyrir auðkenni skjásins sem þú ert að setja upp.")


def screen_connection_guide(settings):
    st.subheader("Tengja við skjái")
    st.caption("Hver skjár fær sína slóð. Opnaðu slóðina á tölvunni sem er tengd skjánum og settu vafrann í fullan skjá með F11.")
    base_note = "Þegar vefurinn er kominn á Render notarðu Render-slóðina í stað localhost. Dæmi: https://nafn-a-vef.onrender.com/?view=skjar&mode=Matsalur"
    st.info(base_note)

    combos = [
        ("Anddyri", "Anddyri", None, "Sjálfvirk dagskrá eftir tíma dags"),
        ("Matsalur", "Matsalur", "Hádegisspilun", "Matseðill stærstur í kringum hádegi"),
        ("Kennarastofa", "Kennarastofa", None, "Viðburðir, tilkynningar og veður"),
        ("Viðburðaskjár", "Anddyri", "Viðburðaspilun", "Fyrir árshátíð, opið hús eða sérstaka daga"),
    ]
    for title, mode, playlist, desc in combos:
        url = absolute_local_url(screen_url(mode, playlist))
        with st.container(border=True):
            st.markdown(f"### {title}")
            st.write(desc)
            st.markdown(f'<div class="url-box">{h(url)}</div>', unsafe_allow_html=True)
            st.link_button(f"Opna {title}", screen_url(mode, playlist), use_container_width=True)

    st.markdown("### Mælt verklag á skjátölvu")
    st.markdown("""
1. Opnaðu réttu slóðina fyrir skjáinn.
2. Ýttu á **F11** til að setja vafrann í fullscreen.
3. Stilltu tölvuna þannig að hún sofi ekki sjálfkrafa.
4. Settu síðuna sem upphafssíðu eða vistaðu hana sem bókamerki.
5. Ef skjárinn er á Render þarf aðeins internet; ef hann er á localhost þarf tölvan sem keyrir Python að vera í gangi.
""")

    st.markdown("### Snjallstilling fyrir Chrome")
    st.code('chrome.exe --kiosk "http://localhost:8501/?view=skjar&mode=Anddyri"', language="bash")
    st.caption("Kiosk-hamur er góður fyrir skjái sem eiga bara að sýna upplýsingaskjáinn.")

def admin_page():
    settings = db.get_settings()
    css(settings.get("screen_mode", "Sjálfvirkt"), get_theme_accent(settings, settings.get("screen_mode", "Sjálfvirkt")))
    if not st.session_state.get("admin"):
        login_box()
        return

    st.title(f"🏫 Vallaskóli Skjár {VERSION} — Ritstjórnarkerfi")
    st.caption("Ofur einföld dagleg uppfærsla, matseðill af Vallaskóla-vef, Google Sheets, Google Calendar og skjáritstjóri.")

    if st.button("Skrá út"):
        st.session_state["admin"] = False
        st.rerun()

    tabs = st.tabs(["🚀 Heimili", "✏️ Dagleg uppfærsla", "▶️ Spilunarlistar", "📺 Skjápar & QR", "🔌 Tengja skjái", "🎛️ Skjáritstjóri", "🍽️ Matseðill", "📣 Tilkynningar", "🗓️ Viðburðir", "🖼️ Myndir", "💬 Hugsanir", "🔗 Tengingar", "⚙️ Stillingar"])

    with tabs[0]:
        admin_home_dashboard(settings)
        st.markdown("### Neyðarhamur")
        emergency = settings.get("emergency_active", "0") == "1"
        with st.form("emergency_form"):
            active = st.checkbox("Virkja áríðandi skjá", value=emergency)
            title = st.text_input("Fyrirsögn", value=settings.get("emergency_title", "Áríðandi skilaboð"))
            body = st.text_area("Skilaboð", value=settings.get("emergency_body", ""), height=120)
            if st.form_submit_button("Vista neyðarham"):
                db.set_setting("emergency_active", "1" if active else "0")
                db.set_setting("emergency_title", title)
                db.set_setting("emergency_body", body)
                st.success("Vistað.")
                st.rerun()

    with tabs[1]:
        daily_editor(settings)

    with tabs[2]:
        playlist_editor(settings)

    with tabs[3]:
        screen_devices_admin(settings)

    with tabs[4]:
        screen_connection_guide(settings)

    with tabs[5]:
        st.subheader("Skjáritstjóri")
        st.caption("Veldu hvað birtist í hverjum skjáham, í hvaða röð, hversu lengi og með hvaða þema.")
        mode_to_edit = st.selectbox("Veldu skjáham til að stilla", ["Anddyri", "Matsalur", "Kennarastofa", "Sjálfvirkt"])
        key = get_mode_key(mode_to_edit)
        current_blocks = get_editor_blocks(settings, mode_to_edit)
        block_options = [""] + list(BLOCKS.keys())
        block_labels = {"": "— ekkert —", **BLOCKS}

        with st.form("screen_editor_form"):
            use_editor = st.checkbox("Nota skjáritstjóra fyrir skjáina", value=settings.get("use_screen_editor", "1") == "1")
            theme = st.selectbox(
                "Þema / litur",
                list(THEMES.keys()),
                index=list(THEMES.keys()).index(get_editor_theme(settings, mode_to_edit)) if get_editor_theme(settings, mode_to_edit) in THEMES else 0,
            )
            seconds = st.number_input("Hversu lengi birtist hver kubbur?", min_value=5, max_value=120, value=get_editor_seconds(settings, mode_to_edit), step=1)
            layout_style = st.selectbox("Útlitsstilling", ["Deluxe", "Standard", "Compact"], index=0, help="Fyrir næstu útgáfur: deluxe gefur stærri, sjónrænni skjá; compact hentar smærri skjám.")
            animation_style = st.selectbox("Hreyfing / animation", ["Mjúk hreyfing", "Rólegt", "Meiri orka"], index=0)
            show_proverb = st.checkbox("Sýna málshátt/orðtak dagsins á öllum skjám", value=settings.get("show_proverb_all_screens", "1") == "1")
            show_ticker = st.checkbox("Sýna rennilínu neðst með stuttum skilaboðum", value=settings.get("show_ticker", "1") == "1")
            image_layout = st.selectbox("Myndaútlit", ["Stór mynd + texti", "Mynd + textaspjald", "Polaroid"], index=["Stór mynd + texti", "Mynd + textaspjald", "Polaroid"].index(settings.get(f"image_layout_{key}", settings.get("image_layout_default", "Stór mynd + texti"))) if settings.get(f"image_layout_{key}", settings.get("image_layout_default", "Stór mynd + texti")) in ["Stór mynd + texti", "Mynd + textaspjald", "Polaroid"] else 0)
            image_placement = st.selectbox("Hvaða myndastaðsetning birtist í þessum ham?", ["Aðalmyndasýning", "Hægri hlið", "Bakgrunnur/hero", "Alls staðar"], index=["Aðalmyndasýning", "Hægri hlið", "Bakgrunnur/hero", "Alls staðar"].index(settings.get(f"image_placement_{key}", "Aðalmyndasýning")) if settings.get(f"image_placement_{key}", "Aðalmyndasýning") in ["Aðalmyndasýning", "Hægri hlið", "Bakgrunnur/hero", "Alls staðar"] else 0)
            st.markdown("#### Röð kubba")
            st.caption("Veldu kubb í hvert sæti. Sama kubb má velja oftar en kerfið fjarlægir tvítekin sæti þegar vistað er.")
            chosen = []
            for i in range(8):
                default = current_blocks[i] if i < len(current_blocks) else ""
                idx = block_options.index(default) if default in block_options else 0
                chosen.append(st.selectbox(f"Sæti {i+1}", block_options, index=idx, format_func=lambda x: block_labels.get(x, x), key=f"editor_{key}_{i}"))
            c1, c2, c3, c4, c5 = st.columns(5)
            save = c1.form_submit_button("Vista þennan skjáham", use_container_width=True)
            apply_all = c2.form_submit_button("Apply to all screens", use_container_width=True)
            apply_matsalur = c3.form_submit_button("Apply only to Matsalur", use_container_width=True)
            apply_kennarastofa = c4.form_submit_button("Apply only to Kennarastofa", use_container_width=True)
            reset = c5.form_submit_button("Endurstilla", use_container_width=True)
            if save or apply_all or apply_matsalur or apply_kennarastofa:
                cleaned = []
                for b in chosen:
                    if b and b in BLOCKS and b not in cleaned:
                        cleaned.append(b)
                if not cleaned:
                    cleaned = DEFAULT_BLOCKS_BY_MODE.get(mode_to_edit, DEFAULT_BLOCKS_BY_MODE["Sjálfvirkt"])
                db.set_setting("use_screen_editor", "1" if use_editor else "0")
                db.set_setting("show_proverb_all_screens", "1" if show_proverb else "0")
                db.set_setting("show_ticker", "1" if show_ticker else "0")
                db.set_setting(f"editor_layout_{key}", layout_style)
                db.set_setting(f"editor_animation_{key}", animation_style)
                target_modes = [mode_to_edit]
                if apply_all:
                    target_modes = ["Anddyri", "Matsalur", "Kennarastofa", "Sjálfvirkt"]
                elif apply_matsalur:
                    target_modes = ["Matsalur"]
                elif apply_kennarastofa:
                    target_modes = ["Kennarastofa"]
                for target in target_modes:
                    tkey = get_mode_key(target)
                    db.set_setting(f"editor_blocks_{tkey}", json.dumps(cleaned, ensure_ascii=False))
                    db.set_setting(f"editor_seconds_{tkey}", str(seconds))
                    db.set_setting(f"editor_theme_{tkey}", theme)
                    db.set_setting(f"editor_layout_{tkey}", layout_style)
                    db.set_setting(f"editor_animation_{tkey}", animation_style)
                    db.set_setting(f"image_layout_{tkey}", image_layout)
                    db.set_setting(f"image_placement_{tkey}", image_placement)
                st.success("Skjáritstjóri vistaður.")
                st.rerun()
            if reset:
                db.set_setting(f"editor_blocks_{key}", json.dumps(DEFAULT_BLOCKS_BY_MODE.get(mode_to_edit, DEFAULT_BLOCKS_BY_MODE["Sjálfvirkt"]), ensure_ascii=False))
                db.set_setting(f"editor_seconds_{key}", settings.get("slide_seconds", "12"))
                db.set_setting(f"editor_theme_{key}", "")
                st.success("Skjáhamur endurstilltur.")
                st.rerun()

        saved_blocks = get_editor_blocks(db.get_settings(), mode_to_edit)
        st.markdown("#### Núverandi spilun")
        chips = "".join(f'<span class="block-chip">{h(BLOCKS.get(b,b))}</span>' for b in saved_blocks)
        st.markdown(f'<div class="editor-preview">{chips}</div>', unsafe_allow_html=True)
        p1, p2, p3 = st.columns(3)
        p1.link_button(f"Preview mode: {mode_to_edit}", screen_url(mode_to_edit), use_container_width=True)
        p2.link_button("Preview Matsalur", "https://vallaskoli-skjar.onrender.com/?view=skjar&device=MATSALUR-01", use_container_width=True)
        p3.link_button("Preview Kennarastofa", "https://vallaskoli-skjar.onrender.com/?view=skjar&device=KENNARASTOFA-01", use_container_width=True)

        st.markdown("#### Tillögur að uppsetningu")
        st.info("Anddyri: Tilkynningar → Myndir → Viðburðir → Veður.  Matsalur: Matseðill → Tilkynningar → Veður.  Kennarastofa: Tilkynningar → Viðburðir → Veður → Matseðill.")

    with tabs[6]:
        st.subheader("Matseðill vikunnar")
        st.info("Ef Google Sheets tenging er virk notar skjárinn hana fyrir matseðil dagsins. Handvirki matseðillinn er varaáætlun.")
        for row in db.get_menu_week():
            with st.expander(WEEKDAYS[row["weekday"]], expanded=row["weekday"] == date.today().weekday()):
                with st.form(f"menu_{row['weekday']}"):
                    title = st.text_input("Réttur / fyrirsögn", value=row["title"], key=f"mt{row['weekday']}")
                    desc = st.text_area("Lýsing", value=row["description"], key=f"md{row['weekday']}", height=110)
                    if st.form_submit_button("Vista"):
                        db.upsert_menu(row["weekday"], title, desc)
                        st.success("Matseðill vistaður.")
                        st.rerun()

    with tabs[7]:
        st.subheader("Tilkynningar")
        with st.form("add_announcement"):
            title = st.text_input("Fyrirsögn")
            body = st.text_area("Texti", height=120)
            c1, c2, c3 = st.columns(3)
            category = c1.selectbox("Flokkur", ["Almennt", "Nemendur", "Starfsfólk", "Foreldrar", "Viðburður", "Matsalur", "Anddyri"])
            priority = c2.selectbox("Forgangur", ["Venjulegt", "Mikilvægt", "Áríðandi"])
            expires = c3.date_input("Gildir til", value=None)
            if st.form_submit_button("Bæta við tilkynningu"):
                if title and body:
                    db.add_announcement(title, body, category, priority, expires.isoformat() if expires else "")
                    st.success("Tilkynning bætt við.")
                    st.rerun()
                else:
                    st.warning("Settu inn fyrirsögn og texta.")
        st.divider()
        for a in db.list_announcements(active_only=False):
            with st.container(border=True):
                st.markdown(f"**{a['title']}**")
                st.write(a["body"])
                st.caption(f"{a['category']} · {a['priority']} · Virk: {'Já' if a['active'] else 'Nei'}")
                c1, c2 = st.columns([1,1])
                if c1.button("Virk/óvirk", key=f"ann_active_{a['id']}"):
                    db.set_announcement_active(a["id"], not bool(a["active"]))
                    st.rerun()
                if c2.button("Eyða", key=f"ann_del_{a['id']}"):
                    db.delete_announcement(a["id"])
                    st.rerun()

    with tabs[8]:
        st.subheader("Viðburðir framundan")
        st.info("Google Calendar viðburðir birtast sjálfkrafa ef iCal tenging er virk. Handvirkir viðburðir birtast líka.")
        with st.form("add_event"):
            title = st.text_input("Heiti viðburðar")
            c1, c2 = st.columns(2)
            event_date = c1.date_input("Dagsetning", value=date.today())
            event_time = c2.text_input("Tími", placeholder="t.d. 10:30")
            location = st.text_input("Staðsetning", placeholder="t.d. Salur / íþróttahús")
            if st.form_submit_button("Bæta við viðburði"):
                if title:
                    db.add_event(title, event_date.isoformat(), event_time, location)
                    st.success("Viðburði bætt við.")
                    st.rerun()
        st.divider()
        for e in db.list_events(upcoming_only=False):
            with st.container(border=True):
                st.markdown(f"**{e['title']}**")
                st.caption(f"{e['event_date']} {e['event_time']} · {e['location']} · {e['source']}")
                if st.button("Eyða", key=f"event_del_{e['id']}"):
                    db.delete_event(e["id"])
                    st.rerun()

    with tabs[9]:
        st.subheader("Myndasýning")
        uploaded = st.file_uploader("Hlaða upp mynd", type=["png", "jpg", "jpeg", "webp"])
        caption = st.text_input("Myndatexti")
        target_modes = st.multiselect("Birta á skjám", ["Allir", "Anddyri", "Matsalur", "Kennarastofa", "Sjálfvirkt"], default=["Allir"], help="Veldu Allir eða ákveðna skjáhama.")
        placement = st.selectbox("Hvar á myndin helst að birtast?", ["Aðalmyndasýning", "Hægri hlið", "Bakgrunnur/hero", "Alls staðar"], help="Kerfið notar þessa merkingu til að velja réttar myndir í mismunandi kubba.")
        weight = st.slider("Forgangur myndar", 1, 5, 1, help="Hærri tala birtist oftar/framar í myndalista.")
        if st.button("Vista mynd"):
            if uploaded:
                safe_name = f"{int(time.time())}_{uploaded.name.replace(' ', '_')}"
                out = UPLOAD_DIR / safe_name
                out.write_bytes(uploaded.getbuffer())
                try:
                    Image.open(out).verify()
                    db.add_image(safe_name, caption, target_modes, placement, weight)
                    st.success("Mynd vistuð með staðsetningu og skjámerkingu.")
                    st.rerun()
                except Exception:
                    out.unlink(missing_ok=True)
                    st.error("Ekki tókst að lesa myndina.")
            else:
                st.warning("Veldu mynd fyrst.")
        st.divider()
        cols = st.columns(3)
        for i, img in enumerate(db.list_images(active_only=False)):
            with cols[i % 3]:
                path = UPLOAD_DIR / img["filename"]
                if path.exists():
                    st.image(str(path), caption=img["caption"], use_container_width=True)
                    st.caption(f"Birting: {image_row_value(img, 'target_modes', '[\"Allir\"]')} · Staðsetning: {image_row_value(img, 'placement', 'Aðalmyndasýning')}")
                if st.button("Eyða mynd", key=f"img_del_{img['id']}"):
                    fname = db.delete_image(img["id"])
                    if fname:
                        (UPLOAD_DIR / fname).unlink(missing_ok=True)
                    st.rerun()

    with tabs[10]:
        st.subheader("Góð hugsun dagsins")
        with st.form("add_thought"):
            text = st.text_area("Ný hugsun", height=100)
            if st.form_submit_button("Bæta við"):
                if text:
                    db.add_thought(text)
                    st.success("Bætt við.")
                    st.rerun()
        st.divider()
        for t in db.list_thoughts(active_only=False):
            with st.container(border=True):
                st.write(t["text"])
                if st.button("Eyða", key=f"thought_del_{t['id']}"):
                    db.delete_thought(t["id"])
                    st.rerun()

    with tabs[11]:
        st.subheader("Vallaskóli matseðill af heimasíðu")
        with st.form("vallaskoli_menu_settings"):
            v_enabled = st.checkbox("Virkja matseðil beint af vallaskoli.is", value=settings.get("vallaskoli_menu_enabled", "1") == "1")
            v_url = st.text_input("Matseðilsslóð", value=settings.get("vallaskoli_menu_url", "https://vallaskoli.is/skolinn/matsedill/"))
            if st.form_submit_button("Vista Vallaskóla matseðilstengingu"):
                db.set_setting("vallaskoli_menu_enabled", "1" if v_enabled else "0")
                db.set_setting("vallaskoli_menu_url", v_url)
                fetch_vallaskoli_web_menu.clear()
                st.success("Matseðilstenging vistuð.")
                st.rerun()
        if st.button("Prófa Vallaskóla matseðil"):
            try:
                fetch_vallaskoli_web_menu.clear()
                test = fetch_vallaskoli_web_menu(settings.get("vallaskoli_menu_url", "https://vallaskoli.is/skolinn/matsedill/"))
                st.write({k: v for k, v in test.items() if k != "items"})
                if test.get("today"):
                    st.success(f"Matur dagsins fannst: {test['today']['title']}")
                else:
                    st.warning("Tengingin virkar, en fann ekki mat fyrir daginn í dag á síðunni. Þá notar kerfið næstu varaheimild.")
            except Exception as e:
                st.error(str(e))

        st.divider()
        st.subheader("Google Sheets matseðill")
        with st.form("sheets_settings"):
            sheets_enabled = st.checkbox("Virkja Google Sheets matseðil", value=settings.get("sheets_enabled", "0") == "1")
            csv_url = st.text_input("CSV slóð úr Google Sheets", value=settings.get("sheets_csv_url", ""), placeholder="https://docs.google.com/spreadsheets/d/e/.../pub?output=csv")
            c1, c2 = st.columns(2)
            date_col = c1.text_input("Dálkur fyrir dagsetningu", value=settings.get("sheets_date_column", "Dagsetning"))
            weekday_col = c2.text_input("Dálkur fyrir vikudag", value=settings.get("sheets_weekday_column", "Dagur"))
            c3, c4 = st.columns(2)
            title_col = c3.text_input("Dálkur fyrir mat", value=settings.get("sheets_title_column", "Matur"))
            desc_col = c4.text_input("Dálkur fyrir lýsingu", value=settings.get("sheets_description_column", "Lýsing"))
            if st.form_submit_button("Vista Google Sheets tengingu"):
                db.set_setting("sheets_enabled", "1" if sheets_enabled else "0")
                db.set_setting("sheets_csv_url", csv_url)
                db.set_setting("sheets_date_column", date_col)
                db.set_setting("sheets_weekday_column", weekday_col)
                db.set_setting("sheets_title_column", title_col)
                db.set_setting("sheets_description_column", desc_col)
                fetch_google_sheet_menu.clear()
                st.success("Google Sheets stillingar vistaðar.")
                st.rerun()
        if st.button("Prófa Google Sheets tengingu"):
            try:
                fetch_google_sheet_menu.clear()
                test = fetch_google_sheet_menu(csv_url, date_col, weekday_col, title_col, desc_col)
                st.write(test)
            except Exception as e:
                st.error(str(e))

        st.divider()
        st.subheader("Vallaskóli viðburðadagatal af heimasíðu")
        st.caption("Aðalheimild fyrir viðburði. Ef ekkert finnst hér notar skjárinn Google Calendar og handvirka viðburði sem varaheimildir.")
        with st.form("vallaskoli_events_settings"):
            ev_enabled = st.checkbox("Virkja viðburði beint af vallaskoli.is", value=settings.get("vallaskoli_events_enabled", "1") == "1")
            ev_url = st.text_input("Viðburðadagatalsslóð", value=settings.get("vallaskoli_events_url", "https://vallaskoli.is/skolinn/vidburdadagatal/"))
            ev_days = st.number_input("Sýna viðburði næstu daga af Vallaskóla-vef", min_value=1, max_value=365, value=int(settings.get("vallaskoli_events_days_ahead", "90") or 90))
            if st.form_submit_button("Vista Vallaskóla viðburðatengingu"):
                db.set_setting("vallaskoli_events_enabled", "1" if ev_enabled else "0")
                db.set_setting("vallaskoli_events_url", ev_url)
                db.set_setting("vallaskoli_events_days_ahead", str(ev_days))
                fetch_vallaskoli_web_events.clear()
                st.success("Viðburðatenging vistuð.")
                st.rerun()
        if st.button("Prófa Vallaskóla viðburðadagatal"):
            try:
                fetch_vallaskoli_web_events.clear()
                test = fetch_vallaskoli_web_events(settings.get("vallaskoli_events_url", "https://vallaskoli.is/skolinn/vidburdadagatal/"), settings.get("vallaskoli_events_days_ahead", "90"))
                st.write(test)
                if test.get("events"):
                    st.success(f"Fann {len(test['events'])} viðburði til birtingar.")
                else:
                    st.warning("Tengingin svaraði, en engir framtíðarviðburðir fundust í texta síðunnar. Þá notar kerfið Google Calendar eða handvirka viðburði.")
            except Exception as e:
                st.error(str(e))

        st.divider()
        st.subheader("Google Calendar viðburðir")
        st.caption("Aukaheimild ef þú vilt nota public iCal slóð úr Google Calendar.")
        with st.form("calendar_settings"):
            cal_enabled = st.checkbox("Virkja Google Calendar iCal viðburði", value=settings.get("calendar_enabled", "0") == "1")
            ics_url = st.text_input("Public address in iCal format", value=settings.get("calendar_ics_url", ""), placeholder="https://calendar.google.com/calendar/ical/.../public/basic.ics")
            days = st.number_input("Sýna Google Calendar viðburði næstu daga", min_value=1, max_value=365, value=int(settings.get("calendar_days_ahead", "30") or 30))
            if st.form_submit_button("Vista Google Calendar tengingu"):
                db.set_setting("calendar_enabled", "1" if cal_enabled else "0")
                db.set_setting("calendar_ics_url", ics_url)
                db.set_setting("calendar_days_ahead", str(days))
                fetch_calendar_events.clear()
                st.success("Google Calendar stillingar vistaðar.")
                st.rerun()
        if st.button("Prófa Google Calendar tengingu"):
            try:
                fetch_calendar_events.clear()
                test = fetch_calendar_events(ics_url, days)
                st.write(test)
            except Exception as e:
                st.error(str(e))

    with tabs[12]:
        st.subheader("Stillingar")
        with st.form("settings"):
            school = st.text_input("Nafn skóla", value=settings.get("school_name", "Vallaskóli"))
            subtitle = st.text_input("Undirtitill", value=settings.get("subtitle", "Upplýsingaskjár"))
            logo_url = st.text_input("Logo slóð", value=settings.get("logo_url", ""), help="Logo birtist uppi í vinstra horni skjásins.")
            screen_mode = st.selectbox("Sjálfgefinn skjáhamur", SCREEN_MODES, index=SCREEN_MODES.index(settings.get("screen_mode", "Sjálfvirkt")) if settings.get("screen_mode", "Sjálfvirkt") in SCREEN_MODES else 0)
            c1, c2 = st.columns(2)
            refresh = c1.number_input("Sjálfvirk endurhleðsla skjás, sek", min_value=10, max_value=600, value=int(settings.get("screen_refresh_seconds", "60")))
            slide = c2.number_input("Skipta um áhersluslide á, sek", min_value=5, max_value=120, value=int(settings.get("slide_seconds", "12")))
            st.markdown("#### Veðurstaðsetning")
            c1, c2, c3 = st.columns(3)
            place = c1.text_input("Staður", value=settings.get("weather_place", "Selfoss"))
            lat = c2.text_input("Breiddargráða", value=settings.get("weather_lat", "63.9331"))
            lon = c3.text_input("Lengdargráða", value=settings.get("weather_lon", "-20.9971"))
            st.markdown("#### Slóð fyrir skjái")
            public_base_url = st.text_input("Opinber grunnslóð", value=settings.get("public_base_url", "http://localhost:8501"), help="Notað í QR-kóða og skjátengingar. Á Render er þetta t.d. https://nafn-a-vef.onrender.com")
            st.markdown("#### Aðgangur")
            new_pw = st.text_input("Nýtt stjórnborðslykilorð", value=settings.get("admin_password", "vallaskoli123"), type="password")
            if st.form_submit_button("Vista stillingar"):
                db.set_setting("school_name", school)
                db.set_setting("subtitle", subtitle)
                db.set_setting("logo_url", logo_url)
                db.set_setting("screen_mode", screen_mode)
                db.set_setting("screen_refresh_seconds", str(refresh))
                db.set_setting("slide_seconds", str(slide))
                db.set_setting("weather_place", place)
                db.set_setting("weather_lat", lat)
                db.set_setting("weather_lon", lon)
                db.set_setting("public_base_url", public_base_url.strip().rstrip("/"))
                db.set_setting("admin_password", new_pw)
                st.success("Stillingar vistaðar.")
                st.rerun()


def main():
    params = st.query_params
    view = params.get("view", "")
    if view == "skjar":
        screen_page()
        return
    if view == "admin":
        admin_page()
        return

    css()
    st.title(f"🏫 Vallaskóli Skjár {VERSION}")
    st.write("Veldu hvort þú vilt opna upplýsingaskjáinn eða stjórnborðið.")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("### 📺 Skjár")
        st.write("Fallegur upplýsingaskjár fyrir sjónvarp, anddyri eða ganga.")
        st.link_button("Opna skjá", "?view=skjar", use_container_width=True)
    with c2:
        st.markdown("### 🍽️ Matsalur")
        st.write("Sérhamur með matseðli stærst og skýrum skilaboðum.")
        st.link_button("Opna matsal", "?view=skjar&mode=Matsalur", use_container_width=True)
    with c3:
        st.markdown("### 🔐 Stjórnborð")
        st.write("Breyttu matseðli, tilkynningum, tengingum og stillingum.")
        st.link_button("Opna stjórnborð", "?view=admin", use_container_width=True)
    st.info("Sjálfgefið lykilorð í stjórnborði er: vallaskoli123 — breyttu því strax í Stillingar.")


if __name__ == "__main__":
    main()
