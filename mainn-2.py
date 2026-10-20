# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════════════╗
# ║  MULTI-SERVER DISCORD BOT  •  Python 3.10+                           ║
# ║  pip install -r requirements.txt                                     ║
# ║  التوكن: متغير البيئة DISCORD_TOKEN أو ملف token.txt (لا تكتبه بالكود) ║
# ║  فعّل Message Content Intent + Server Members Intent                 ║
# ║  البوت بلا اسم ثابت: أونر كل سيرفر يسمّيه بأمر  تعيين_اسم             ║
# ╠══════════════════════════════════════════════════════════════════════╣
# ║  الأقسام: الإعدادات • الرتب • قاعدة البيانات • الصور والبطاقات        ║
# ║  XP واللفلات • الفويس • الأحداث واللوقات • الحماية • المساعدة (بنرات) ║
# ║  البروفايل (R صورة واحدة) • الإدارة • الإعلان • التجهيز والهيكل      ║
# ║  المتجر والجيفات • الفعاليات • الأدوات (تذاكر/اقتراحات/تصويت/تذكير)  ║
# ╚══════════════════════════════════════════════════════════════════════╝

import os
import io
import re
import sys
import json
import math
import time
import random
import asyncio
import colorsys
import zlib
import contextvars
import base64
from collections import defaultdict, deque
from datetime import timedelta, datetime, timezone
from urllib.parse import urlparse, quote

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    ZoneInfo = None

import aiohttp
from aiohttp import web
import discord
from discord.ext import commands, tasks
from discord.ext.commands.view import StringView

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
    PIL_OK = True
except ImportError:  # البوت يشتغل بدون صور البطاقات
    PIL_OK = False

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    AR_OK = True
except ImportError:
    AR_OK = False

# ───────────────────────── الإعدادات ─────────────────────────
PREFIX = "!"
# خزّن البيانات والوسائط بجانب هذا الملف بدل الاعتماد على مجلد التشغيل الحالي؛
# يمكن تغيير المسارات من متغيرات البيئة عند الاستضافة.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.abspath(os.getenv("BOT_DB_FILE") or os.getenv("NEXAR_DB_FILE") or os.path.join(BASE_DIR, "users_stats.json"))
MEDIA_DIR = os.path.abspath(os.getenv("BOT_MEDIA_DIR") or os.getenv("NEXAR_MEDIA_DIR") or os.path.join(BASE_DIR, "media"))
def _load_token():
    tok = (os.getenv("DISCORD_TOKEN") or os.getenv("TOKEN") or "").strip()
    if not tok:
        for p in (os.path.join(BASE_DIR, "token.txt"), "token.txt"):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    tok = f.read().strip()
            except OSError:
                continue
            if tok:
                break
    return tok

TOKEN = _load_token()
FONT_DIR = os.path.abspath(os.getenv("BOT_FONT_DIR") or os.getenv("NEXAR_FONT_DIR") or os.path.join(BASE_DIR, "fonts"))
XP_MIN, XP_MAX = 15, 25          # XP لكل رسالة
XP_COOLDOWN = 45                 # ثواني بين كل XP
VOICE_XP = 6                     # XP لكل دقيقة فويس (لازم يكون معاك أحد)
MAX_LEVEL = 1000
DAILY_COINS = 250
FOOTER_TAIL = "حيث تُصنع الهيبة"
GOLD = 0xFFD700
PURPLE = 0x8A2BE2

LOG_NAMES = ("nexar-logs", "سجل-الأحداث", "logs", "📜・اللوقات", "اللوقات")
WELCOME_NAMES = ("👋-⁞-ترحيب-المقاتلين", "ترحيب-المقاتلين", "welcome", "👋・الترحيب", "الترحيب")
LEVEL_NAMES = ("⟡ 𝐋𝐞𝐯𝐞𝐥 𝐔𝐩 ⟡", "level-up", "levels", "لفلات", "🆙・اللفلات", "اللفلات")
EVENTS_NAMES = ("🎉・الفعاليات", "الفعاليات", "events", "العاب", "🎮・الالعاب", "الالعاب", "games")  # الأسماء القديمة للتوافق
SUGGEST_NAMES = ("💡・الاقتراحات", "الاقتراحات", "اقتراحات", "suggestions")
COLORS_NAMES = ("الوان", "🎨・الالوان", "الالوان", "colors")

# ───────────────────────── الرتب ─────────────────────────
RANKS = []  # لا توجد رتب جاهزة: كل سيرفر ينشئ رتبه بأمر انشاء_رتب_لفل
NEW_MEMBER = "New Member"
NEW_MEMBER_COLORS = (0x95A5A6, 0x5865F2)
MS_PREFIX = "⌬ Level"
MILESTONES = list(range(5, 101, 5))
NONE_RANK = (0, "—", "NONE", NEW_MEMBER_COLORS, "")

def blend(c1, c2):
    if c2 is None or c2 == c1:
        return c1
    r = ((c1 >> 16 & 255) + (c2 >> 16 & 255)) // 2
    g = ((c1 >> 8 & 255) + (c2 >> 8 & 255)) // 2
    b = ((c1 & 255) + (c2 & 255)) // 2
    return (r << 16) | (g << 8) | b

def milestone_colors(n):
    def hsv(h, s, v):
        r, g, b = colorsys.hsv_to_rgb(h % 1.0, s, v)
        return (int(r * 255) << 16) | (int(g * 255) << 8) | int(b * 255)
    h = (n / 100) * 0.82
    return hsv(h, 0.85, 1.0), hsv(h + 0.09, 0.62, 1.0)

# ── إعدادات رتب اللفلات لكل سيرفر (تتخزن في db.cfg(guild)["lv"]) ──
def _lv_cfg(guild=None):
    guild = guild or CUR_GUILD.get()
    if guild is None:
        return {}
    return db.cfg(guild.id).get("lv") or {}

def _lv_edit(guild):
    return db.cfg(guild.id).setdefault("lv", {})

def milestone_name(n, guild=None):
    return f"{_lv_cfg(guild).get('ms_prefix') or MS_PREFIX} {n}"

def milestones_on(guild=None):
    return _lv_cfg(guild).get("milestones", False)

def new_member_spec(guild=None):
    """(الاسم, (لون1, لون2)) أو None إذا حذفها السيرفر."""
    n = _lv_cfg(guild).get("new") or {}
    if not n or n.get("off"):
        return None
    c1 = n.get("c1", NEW_MEMBER_COLORS[0])
    c2 = n.get("c2", c1 if "c1" in n else NEW_MEMBER_COLORS[1])
    return (n.get("name") or NEW_MEMBER), (c1, c2)

def guild_ranks(guild=None):
    """رتب اللفلات الفعلية للسيرفر (الافتراضية + تعديلات السيرفر) من الأعلى للأدنى."""
    tiers = {e[0]: e for e in RANKS}
    for k, v in (_lv_cfg(guild).get("tiers") or {}).items():
        lv = int(k)
        if v is None:
            tiers.pop(lv, None)
            continue
        old = tiers.get(lv)
        c1 = v["c1"]
        tiers[lv] = (lv, v["name"], v.get("en") or (old[2] if old else f"LEVEL {lv}"),
                     (c1, v.get("c2", c1)), v.get("desc") or (old[4] if old else f"رتبة اللفل {lv}."))
    return sorted(tiers.values(), key=lambda e: -e[0])

def layout_snapshot(guild=None, all_milestones=False):
    """كل رتب اللفلات بالسيرفر: المفتاح -> (الاسم, لون1, لون2)."""
    snap = {}
    for e in guild_ranks(guild):
        snap[("t", e[0])] = (e[1], e[3][0], e[3][1])
    if all_milestones or milestones_on(guild):
        for m in MILESTONES:
            c1, c2 = milestone_colors(m)
            snap[("m", m)] = (milestone_name(m, guild), c1, c2)
    nm = new_member_spec(guild)
    if nm:
        snap[("n",)] = (nm[0], nm[1][0], nm[1][1])
    return snap

def guild_role_specs(guild=None):
    return {n: (c1, c2) for n, c1, c2 in layout_snapshot(guild, True).values()}

def level_role_names(guild=None):
    return set(guild_role_specs(guild))

def rank_entry(level, guild=None):
    for entry in guild_ranks(guild):
        if level >= entry[0]:
            return entry
    return NONE_RANK

def rank_for(level, guild=None):
    e = rank_entry(level, guild)
    return e[1], blend(*e[3])

def next_rank(level, guild=None):
    for entry in reversed(guild_ranks(guild)):
        if entry[0] > level:
            return entry
    return None

def wanted_level_names(level, guild=None):
    """أسماء رتب اللفل التي يجب أن يحملها عضو بهذا المستوى."""
    names = []
    entry = rank_entry(level, guild)
    if entry[0] > 0:
        names.append(entry[1])
    if level >= 5:
        if milestones_on(guild):
            names.append(milestone_name(min(100, level // 5 * 5), guild))
    else:
        nm = new_member_spec(guild)
        if nm:
            names.append(nm[0])
    return names

def xp_needed(level):
    return 5 * level * level + 50 * level + 100

# ───────────────────────── الألوان (50) ─────────────────────────
COLOR_NAMES = [
    "أسود ملكي", "أبيض ناصع", "أحمر داكن", "أحمر ناري", "قرمزي", "عنابي", "دموي", "وردي زاهي", "فوشيا", "بنفسجي غامق",
    "برتقالي داكن", "برتقالي مشرق", "أصفر ذهبي", "أصفر ليموني", "ذهبي فاتح", "أخضر حشيشي", "أخضر فسفوري", "أخضر زاهي", "أخضر تفاحي", "أخضر غامق",
    "ربيعي زاهي", "نعناعي", "زمردي", "تركواز فاتح", "تركواز داكن", "أزرق سماوي", "أزرق فيروزي", "أزرق ثلجي", "أزرق ملكي", "أزرق كحلي",
    "كحلي غامق", "ليلي داكن", "نيلي", "أزرق بنفسجي", "لافندر", "أرجواني فاتح", "بنفسجي ملكي", "أرجواني غامق", "بنفسجي صريح", "بنفسجي أحمر",
    "فوشيا غامق", "وردي مائل للبنفسجي", "وردي فاتح", "زهري فاتح", "بني فاتح", "بني دافئ", "بيج خشبي", "بني برونزي", "بني غامق", "شوكولاتي",
]
BASE_COLORS = [
    0x111111, 0xFFFFFF, 0x8B0000, 0xFF0000, 0xDC143C, 0xB22222, 0x4A0000, 0xFF69B4, 0xFF1493, 0xC71585,
    0xFF8C00, 0xFFA500, 0xFFD700, 0xFFFF00, 0xEEEE00, 0xADFF2F, 0x7FFF00, 0x00FF00, 0x32CD32, 0x008000,
    0x00FF7F, 0x00FA9A, 0x2E8B57, 0x3CB371, 0x20B2AA, 0x00FFFF, 0x00CED1, 0x00BFFF, 0x1E90FF, 0x0000FF,
    0x000080, 0x191970, 0x483D8B, 0x6A5ACD, 0x7B68EE, 0x9370DB, 0x8A2BE2, 0x9400D3, 0x9932CC, 0x8B008B,
    0xFF00FF, 0xDA70D6, 0xEE82EE, 0xDDA0DD, 0xBC8F8F, 0xF4A460, 0xD2B48C, 0xCD853F, 0x8B4513, 0x5C4033,
]
COLOR_PALETTE = {str(i): (n, c) for i, (n, c) in enumerate(zip(COLOR_NAMES, BASE_COLORS), 1)}

def is_managed_role(role):
    return role.name.startswith("Color-") or role.name in level_role_names(role.guild)

# ───────────────────────── قاعدة البيانات ─────────────────────────
USER_DEFAULTS = {
    "messages": 0, "xp": 0, "level": 1, "warnings": [], "last_xp": 0,
    "coins": 0, "last_daily": 0, "voice_minutes": 0,
}

class Store:
    def __init__(self, path):
        self.path = path
        self.data = {}
        self.dirty = False
        self.load()

    def load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                d = json.load(f)
            self.data = d if isinstance(d, dict) else {}
        except FileNotFoundError:
            self.data = {}
        except json.JSONDecodeError as e:
            # لا نطمس قاعدة بيانات تالفة بصمت؛ احتفظ بنسخة يمكن استرجاعها.
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            damaged = f"{self.path}.corrupt-{stamp}"
            try:
                os.replace(self.path, damaged)
                print(f"[DB] JSON غير صالح؛ تم حفظ النسخة التالفة في: {damaged} ({e})")
            except OSError as move_error:
                print(f"[DB] تعذر نقل قاعدة البيانات التالفة: {move_error!r}")
            self.data = {}
        except OSError as e:
            print(f"[DB] تعذر قراءة قاعدة البيانات {self.path!r}: {e!r}")
            self.data = {}
        self.data.setdefault("_config", {})
        self.data.setdefault("_media", {})

    def mark(self):
        self.dirty = True

    def user(self, uid):
        key = str(uid)
        u = self.data.get(key)
        if not isinstance(u, dict):
            u = {}
            self.data[key] = u
        for k, v in USER_DEFAULTS.items():
            if k not in u:
                u[k] = [] if isinstance(v, list) else ({} if isinstance(v, dict) else v)
        return u

    def users(self):
        for k, v in self.data.items():
            if k.isdigit() and isinstance(v, dict):
                yield int(k), self.user(k)

    def cfg(self, gid):
        c = self.data["_config"].setdefault(str(gid), {})
        c.setdefault("antilink", False)
        c.setdefault("antispam", False)
        return c

    def _write(self, payload):
        parent = os.path.dirname(self.path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(payload)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, self.path)

    async def flush(self, force=False):
        if not (self.dirty or force):
            return
        self.dirty = False
        try:
            payload = json.dumps(self.data, ensure_ascii=False)
            await asyncio.to_thread(self._write, payload)
        except Exception as e:
            self.dirty = True
            print(f"[DB] save failed: {e!r}")

    def flush_sync(self):
        try:
            self._write(json.dumps(self.data, ensure_ascii=False))
            self.dirty = False
        except Exception as e:
            print(f"[DB] final save failed: {e!r}")

db = Store(DB_FILE)

# ───────────────────────── الصور و GIF ─────────────────────────
RANK_IMAGES = {
    100: "https://cdn.discordapp.com/attachments/1559973324803678329/1560270324988117053/0ae060db7af8111e75054739f1968e7b.jpg",
    75: "https://cdn.discordapp.com/attachments/1559973324803678329/1560270350539948114/259aa6e22d118487f4d6e090e60fc8e7.jpg",
    60: "https://cdn.discordapp.com/attachments/1559973324803678329/1560270364460851321/c35f526e37f906f21dc89e88ad92f493.jpg",
    50: "https://cdn.discordapp.com/attachments/1559973324803678329/1560270373897904178/1ec71e87ff5bc80359dfa1a632a757b6.jpg",
    40: "https://cdn.discordapp.com/attachments/1559973324803678329/1560270380504064090/31d7d86a4795625c41f9f96e15565fd4.jpg",
    30: "https://cdn.discordapp.com/attachments/1559973324803678329/1560270387944751114/fb029eb368614d63f28c207374732ae2.jpg",
    20: "https://cdn.discordapp.com/attachments/1559973324803678329/1560270402201063476/7d195c50cae33883a0d260f8b6a228a9.jpg",
    10: "https://cdn.discordapp.com/attachments/1559973324803678329/1560271971487588363/3086bcb1cac7ea13440d1b530cae17eb.jpg",
    5: "https://cdn.discordapp.com/attachments/1559973324803678329/1560270357670273106/de61d51813a4afc3309ff931ab534270.jpg",
    1: "https://cdn.discordapp.com/attachments/1559973324803678329/1560270324988117053/0ae060db7af8111e75054739f1968e7b.jpg",
}

MEDIA_LABELS = {
    "welcome": "GIF الترحيب (يظهر تحت بطاقة الترحيب)",
    "farewell": "GIF الوداع",
    "levelup": "صورة/GIF رسالة الارتقاء",
    "profile": "صورة/GIF صغيرة بالبروفايل",
    "help": "المساعدة (الرئيسية)", "leaderboard": "المتصدرين",
    "colors": "لوحة الألوان", "setup": "التجهيز",
    "ban": "حظر", "kick": "طرد", "mute": "ميوت", "unmute": "فك ميوت", "warn": "تحذير",
    "pardon": "عفو", "clear": "مسح", "lock": "قفل", "unlock": "فتح",
    "announce": "الإعلان", "emergency": "طوارئ", "calm": "استقرار",
    "daily": "الراتب",
    "log_join": "لوق دخول", "log_leave": "لوق خروج", "log_delete": "لوق حذف", "log_edit": "لوق تعديل",
}
for _n in RANK_IMAGES:
    MEDIA_LABELS[f"rank_{_n}"] = f"صورة رتبة اللفل {_n}"

MEDIA_CACHE = {}

def sniff_ext(b):
    if b[:6] in (b"GIF87a", b"GIF89a"):
        return ".gif"
    if b[:8] == b"\x89PNG\r\n\x1a\n":
        return ".png"
    if b[:3] == b"\xff\xd8\xff":
        return ".jpg"
    if b[:4] == b"RIFF" and b[8:12] == b"WEBP":
        return ".webp"
    return None

async def fetch_bytes(url, limit=8_000_000):
    try:
        async with bot.session.get(url, timeout=aiohttp.ClientTimeout(total=20)) as r:
            if r.status != 200:
                return None
            if r.content_length and r.content_length > limit:
                return None
            data = await r.read()
            return data if len(data) <= limit else None
    except Exception:
        return None

def media_install(key, data):
    ext = sniff_ext(data)
    if not ext:
        return False
    MEDIA_CACHE[key] = (data, f"{key}{ext}")
    try:
        os.makedirs(MEDIA_DIR, exist_ok=True)
        for old in os.listdir(MEDIA_DIR):
            if os.path.splitext(old)[0] == key:
                os.remove(os.path.join(MEDIA_DIR, old))
        with open(os.path.join(MEDIA_DIR, f"{key}{ext}"), "wb") as f:
            f.write(data)
    except OSError:
        pass
    return True

def media_remove(key):
    MEDIA_CACHE.pop(key, None)
    db.data["_media"].pop(key, None)
    db.mark()
    try:
        for old in os.listdir(MEDIA_DIR):
            if os.path.splitext(old)[0] == key:
                os.remove(os.path.join(MEDIA_DIR, old))
    except OSError:
        pass

async def load_media():
    try:
        for fn in os.listdir(MEDIA_DIR):
            key, ext = os.path.splitext(fn)
            if ext.lower() in (".gif", ".png", ".jpg", ".webp"):
                with open(os.path.join(MEDIA_DIR, fn), "rb") as f:
                    MEDIA_CACHE[key] = (f.read(), fn)
    except OSError:
        pass
    urls = {f"rank_{n}": u for n, u in RANK_IMAGES.items()}
    urls.update(db.data["_media"])
    for key, url in urls.items():
        if key in MEDIA_CACHE:
            continue
        data = await fetch_bytes(url)
        if data:
            media_install(key, data)
    print(f"[MEDIA] loaded {len(MEDIA_CACHE)} images")

def attach_media(embed, *keys, thumb=False):
    for key in keys:
        entry = MEDIA_CACHE.get(key)
        if entry:
            data, fn = entry
            (embed.set_thumbnail if thumb else embed.set_image)(url=f"attachment://{fn}")
            return discord.File(io.BytesIO(data), filename=fn)
        url = db.data["_media"].get(key)
        if url:
            (embed.set_thumbnail if thumb else embed.set_image)(url=url)
            return None
    return None

def rank_media_key(level, guild=None):
    lv = rank_entry(level, guild)[0]
    near = [n for n in RANK_IMAGES if n <= max(lv, 1)]
    return f"rank_{max(near) if near else 1}"

def files_of(*fs):
    out = [f for f in fs if f is not None]
    return out or None

# ───────────────────────── الخطوط والبطاقات ─────────────────────────
FONT_CANDIDATES = [
    os.path.join(FONT_DIR, "font.ttf"), os.path.join(FONT_DIR, "Tajawal-Bold.ttf"),
    os.path.join(BASE_DIR, "font.ttf"), "font.ttf", "fonts/font.ttf", "fonts/Tajawal-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/noto/NotoSansArabic-Bold.ttf",
]
FONT_URLS = [
    "https://github.com/google/fonts/raw/main/ofl/tajawal/Tajawal-Bold.ttf",
]
_font_cache = {}

def find_font_file():
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            return p
    return None

def get_font(size):
    if not PIL_OK:
        return None
    if size in _font_cache:
        return _font_cache[size]
    path = find_font_file()
    font = None
    if path:
        try:
            font = ImageFont.truetype(path, size)
        except Exception:
            font = None
    if font is None:
        try:
            font = ImageFont.load_default(size)
        except TypeError:
            font = ImageFont.load_default()
    _font_cache[size] = font
    return font

async def ensure_font():
    if not PIL_OK or find_font_file():
        return
    for url in FONT_URLS:
        data = await fetch_bytes(url, limit=3_000_000)
        if data and len(data) > 10_000:
            try:
                os.makedirs(FONT_DIR, exist_ok=True)
                with open(os.path.join(FONT_DIR, "Tajawal-Bold.ttf"), "wb") as f:
                    f.write(data)
                _font_cache.clear()
                return
            except OSError:
                return

def clean_name(name):
    name = re.sub(r"[^\w\s\-.'!?#@&()]", "", name or "", flags=re.UNICODE).strip()
    return name or "Member"

def ar(text):
    if AR_OK and re.search(r"[\u0600-\u06FF]", text):
        try:
            return get_display(arabic_reshaper.reshape(text))
        except Exception:
            return text
    return text

def _gradient(w, h, c1, c2):
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for x in range(w):
        t = x / max(1, w - 1)
        col = tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))
        d.line([(x, 0), (x, h)], fill=col)
    return img

def _rgb(c):
    return (c >> 16 & 255, c >> 8 & 255, c & 255)

def _circle(img, size):
    img = img.convert("RGBA").resize((size, size), Image.LANCZOS)
    big = Image.new("L", (size * 4, size * 4), 0)
    ImageDraw.Draw(big).ellipse((0, 0, size * 4 - 1, size * 4 - 1), fill=255)
    mask = big.resize((size, size), Image.LANCZOS)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(img, (0, 0), mask)
    return out

def _fit_text(d, text, max_w, start, minimum=18):
    size = start
    while size > minimum:
        if d.textlength(text, font=get_font(size)) <= max_w:
            break
        size -= 2
    return get_font(size)

def render_welcome(avatar_bytes, icon_bytes, name, number, guild_name):
    W, H = 1000, 420
    gold = (255, 215, 0)
    if icon_bytes:
        try:
            base = ImageOps.fit(Image.open(io.BytesIO(icon_bytes)).convert("RGB"), (W, H), Image.LANCZOS)
            base = base.filter(ImageFilter.GaussianBlur(18))
        except Exception:
            base = _gradient(W, H, (40, 12, 80), (10, 10, 30))
    else:
        base = _gradient(W, H, (40, 12, 80), (10, 10, 30))
    base = Image.alpha_composite(base.convert("RGBA"), Image.new("RGBA", (W, H), (8, 6, 22, 178)))
    d = ImageDraw.Draw(base)
    d.rounded_rectangle((14, 14, W - 15, H - 15), radius=30, outline=gold, width=4)
    S = 220
    ax, ay = 70, 52
    d.ellipse((ax - 9, ay - 9, ax + S + 9, ay + S + 9), fill=gold)
    d.ellipse((ax - 4, ay - 4, ax + S + 4, ay + S + 4), fill=(15, 10, 35))
    try:
        av = _circle(Image.open(io.BytesIO(avatar_bytes)), S)
        base.paste(av, (ax, ay), av)
    except Exception:
        pass
    d = ImageDraw.Draw(base)
    x = 340
    d.text((x, 44), "WELCOME", font=get_font(74), fill=gold)
    nm = ar(clean_name(name))
    d.text((x, 142), nm, font=_fit_text(d, nm, W - x - 60, 52), fill=(255, 255, 255))
    d.text((x, 214), f"MEMBER  #{number:,}", font=get_font(36), fill=(190, 160, 255))
    d.line([(x, 268), (W - 60, 268)], fill=(255, 215, 0, 140), width=2)
    d.rounded_rectangle((26, 318, W - 27, H - 27), radius=24, fill=(0, 0, 0, 150))
    if icon_bytes:
        try:
            ic = Image.open(io.BytesIO(icon_bytes)).convert("RGBA").resize((72, 72), Image.LANCZOS)
            m = Image.new("L", (72, 72), 0)
            ImageDraw.Draw(m).rounded_rectangle((0, 0, 71, 71), radius=16, fill=255)
            base.paste(ic, (52, 330), m)
        except Exception:
            pass
    d = ImageDraw.Draw(base)
    gn = ar(clean_name(guild_name))
    d.text((142, 335), gn, font=_fit_text(d, gn, 560, 36), fill=(255, 255, 255))
    d.text((142, 372), "JOINED THE KINGDOM", font=get_font(20), fill=gold)
    out = io.BytesIO()
    base.convert("RGB").save(out, "PNG")
    out.seek(0)
    return out

def _overlay_panel(base, box, radius=24, fill=(0, 0, 0, 120), outline=None, width=2):
    """لوح شبه شفاف فوق الصورة (يرجع الصورة الجديدة)."""
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)
    return Image.alpha_composite(base, layer)

def _progress_bar(base, box, ratio, c1, c2, label=None, font_size=20):
    x0, y0, x1, y1 = box
    bw, bh = x1 - x0, y1 - y0
    base = _overlay_panel(base, box, radius=bh // 2, fill=(0, 0, 0, 175))
    ratio = max(0.0, min(1.0, ratio))
    if ratio > 0:
        fw = max(bh, int(bw * ratio))
        fill = _gradient(fw, bh, c1, c2).convert("RGBA")
        m = Image.new("L", (fw, bh), 0)
        ImageDraw.Draw(m).rounded_rectangle((0, 0, fw - 1, bh - 1), radius=bh // 2, fill=255)
        base.paste(fill, (x0, y0), m)
    if label:
        ImageDraw.Draw(base).text(((x0 + x1) // 2, (y0 + y1) // 2), label, font=get_font(font_size),
                                  fill=(255, 255, 255), anchor="mm")
    return base

def render_profile(avatar_bytes, name, level, xp, need, rank_en, cols, pos, total, msgs, coins, warns,
                   vlevel, vminutes, vpos, vtotal, vratio, vlabel, brand_name=""):
    """بطاقة واحدة فيها كل شي: لفل الكتابة + لفل الفويس + الإحصائيات."""
    W, H = 1000, 540
    c1, c2 = _rgb(cols[0]), _rgb(cols[1])
    v1, v2 = (0, 200, 230), (160, 90, 245)
    gold, white, soft = (255, 215, 0), (255, 255, 255), (200, 200, 235)
    base = _gradient(W, H, tuple(int(v * 0.30) for v in c1), tuple(int(v * 0.30) for v in c2)).convert("RGBA")
    deco = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dd = ImageDraw.Draw(deco)
    dd.ellipse((W - 340, -170, W + 90, 260), fill=c1 + (38,))
    dd.ellipse((-130, H - 190, 300, H + 150), fill=c2 + (32,))
    base = Image.alpha_composite(base, deco)
    d = ImageDraw.Draw(base)
    d.rounded_rectangle((12, 12, W - 13, H - 13), radius=30, outline=c1, width=3)

    # ── الصورة والاسم ──
    S, ax, ay = 170, 48, 38
    d.ellipse((ax - 8, ay - 8, ax + S + 8, ay + S + 8), fill=c2)
    d.ellipse((ax - 4, ay - 4, ax + S + 4, ay + S + 4), fill=(12, 8, 28))
    try:
        av = _circle(Image.open(io.BytesIO(avatar_bytes)), S)
        base.paste(av, (ax, ay), av)
    except Exception:
        pass
    d = ImageDraw.Draw(base)
    x = 250
    nm = ar(clean_name(name))
    d.text((x, 44), nm, font=_fit_text(d, nm, W - x - 60, 52), fill=white)
    d.text((x, 112), rank_en, font=get_font(28), fill=gold)
    if brand_name:
        bn = ar(clean_name(brand_name))
        d.text((x, 156), bn, font=_fit_text(d, bn, W - x - 60, 22, 14), fill=soft)

    # ── لوحة لفل الكتابة + لوحة لفل الفويس ──
    panels = [
        (30, "TEXT LEVEL", level, f"RANK #{pos} / {total}", xp / max(1, need), f"{xp:,} / {need:,} XP",
         ("MAX LEVEL" if level >= MAX_LEVEL else f"{max(0, need - xp):,} XP to LV {level + 1}"), c1, c2),
        (510, "VOICE LEVEL", vlevel, f"RANK #{vpos} / {vtotal}  •  BY HOURS", vratio, vlabel,
         f"TOTAL  {vminutes // 60:,}h {vminutes % 60}m", v1, v2),
    ]
    py0, ph, pw = 228, 200, 460
    for px, title, lv, rank_txt, ratio, bar_txt, foot, a1, a2 in panels:
        base = _overlay_panel(base, (px, py0, px + pw, py0 + ph), radius=26, fill=(0, 0, 0, 120), outline=a1 + (190,), width=2)
        d = ImageDraw.Draw(base)
        d.text((px + 24, py0 + 18), title, font=get_font(22), fill=a1)
        d.text((px + pw - 24, py0 + 8), f"LV {lv}", font=get_font(50), fill=white, anchor="ra")
        d.text((px + 24, py0 + 74), rank_txt, font=get_font(22), fill=soft)
        base = _progress_bar(base, (px + 24, py0 + 116, px + pw - 24, py0 + 152), ratio, a1, a2, bar_txt, 20)
        d = ImageDraw.Draw(base)
        d.text((px + 24, py0 + 162), foot, font=get_font(18), fill=(185, 190, 220))

    # ── شريط الإحصائيات ──
    base = _overlay_panel(base, (30, 446, W - 30, 508), radius=22, fill=(0, 0, 0, 130))
    d = ImageDraw.Draw(base)
    stats = [("MESSAGES", f"{msgs:,}"), ("VOICE TIME", f"{vminutes // 60:,}h {vminutes % 60}m"),
             ("COINS", f"{coins:,}"), ("WARNINGS", str(warns))]
    cw = (W - 60) // len(stats)
    for i, (lab, val) in enumerate(stats):
        cx = 30 + i * cw + cw // 2
        d.text((cx, 468), val, font=get_font(26), fill=white, anchor="mm")
        d.text((cx, 495), lab, font=get_font(14), fill=(180, 185, 220), anchor="mm")
        if i:
            d.line([(30 + i * cw, 458), (30 + i * cw, 498)], fill=(255, 255, 255, 60), width=1)
    out = io.BytesIO()
    base.convert("RGB").save(out, "PNG")
    out.seek(0)
    return out

def render_circle_avatar(avatar_bytes, size=128):
    """صورة دائرية صغيرة بإطار ذهبي رفيع (شفافة الخلفية)."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((0, 0, size - 1, size - 1), fill=(255, 215, 0, 255))
    av = _circle(Image.open(io.BytesIO(avatar_bytes)), size - 8)
    img.paste(av, (4, 4), av)
    out = io.BytesIO()
    img.save(out, "PNG")
    out.seek(0)
    return out

_small_cache = {}

def shrink_media(data, width=240):
    """يصغّر صورة/GIF لعرض محدد ويحافظ على الحركة. يرجع (bytes, ext) أو None."""
    if not PIL_OK:
        return None
    key = (zlib.crc32(data), len(data), width)
    if key in _small_cache:
        return _small_cache[key]
    res = None
    try:
        im = Image.open(io.BytesIO(data))
        animated = getattr(im, "is_animated", False)
        if im.width <= width:
            res = (data, sniff_ext(data) or ".gif")
        elif animated:
            n = im.n_frames
            step = max(1, math.ceil(n / 80))
            frames, durs = [], []
            for i in range(0, n, step):
                im.seek(i)
                fr = im.convert("RGBA")
                h = max(1, int(fr.height * width / fr.width))
                frames.append(fr.resize((width, h), Image.LANCZOS))
                durs.append(max(20, int(im.info.get("duration", 60))) * step)
            out = io.BytesIO()
            frames[0].save(out, "GIF", save_all=True, append_images=frames[1:], duration=durs, loop=0, disposal=2)
            res = (out.getvalue(), ".gif")
        else:
            fr = im.convert("RGBA")
            h = max(1, int(fr.height * width / fr.width))
            out = io.BytesIO()
            fr.resize((width, h), Image.LANCZOS).save(out, "PNG")
            res = (out.getvalue(), ".png")
    except Exception as e:
        print(f"[MEDIA] shrink failed: {e!r}")
    if len(_small_cache) > 20:
        _small_cache.clear()
    _small_cache[key] = res
    return res

# ───────────────────────── البوت ─────────────────────────
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

class CoreBot(commands.Bot):
    session: aiohttp.ClientSession

    async def setup_hook(self):
        self.session = aiohttp.ClientSession()
        self.add_view(ColorView())
        self.add_view(GiveawayView())
        self.add_view(TicketOpenView())
        self.add_view(TicketCloseView())
        flush_loop.start()
        voice_loop.start()
        events_loop.start()
        remind_loop.start()
        asyncio.create_task(startup_assets())
        asyncio.create_task(start_keepalive())

    async def close(self):
        db.flush_sync()
        try:
            await self.session.close()
        except Exception:
            pass
        await super().close()

bot = CoreBot(
    command_prefix=PREFIX, intents=intents, help_command=None, case_insensitive=True,
    max_messages=5000,
    allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, users=True),
)

async def startup_assets():
    await ensure_font()
    await load_media()

async def start_keepalive():
    async def index(_):
        return web.Response(text=f"Bot online | latency {round(bot.latency * 1000)}ms | guilds {len(bot.guilds)}")
    try:
        app = web.Application()
        app.router.add_get("/", index)
        app.router.add_get("/health", index)
        runner = web.AppRunner(app)
        await runner.setup()
        port = int(os.getenv("PORT") or os.getenv("SERVER_PORT") or 8080)
        await web.TCPSite(runner, "0.0.0.0", port).start()
        print(f"[KEEPALIVE] listening on :{port}")
    except Exception as e:
        print(f"[KEEPALIVE] skipped: {e!r}")

@tasks.loop(seconds=30)
async def flush_loop():
    await db.flush()

@tasks.loop(minutes=1)
async def voice_loop():
    # كل سيرفر يُعالج بشكل مستقل؛ خطأ بسيرفر أو عضو واحد لا يوقف بقية السيرفرات.
    for guild in list(bot.guilds):
        try:
            await voice_tick(guild)
        except Exception as e:
            print(f"[VOICE] guild={guild.id}: {e!r}")

@voice_loop.before_loop
async def _before_voice():
    await bot.wait_until_ready()

# ───────────────────────── أدوات عامة ─────────────────────────
QUIET = set()  # سيرفرات تجري فيها عمليات هيكلية: نوقف لوقات الرومات مؤقتاً

class HierarchyError(commands.CheckFailure):
    """منفذ الأمر رتبته أقل من الهدف."""

def staff_cfg(guild):
    return db.cfg(guild.id).get("staff") or {}

def is_admin(member):
    """الإدارة العليا: أونر، أو صلاحية Administrator، أو رتبة صنّفها السيرفر كإدارة عليا."""
    if not isinstance(member, discord.Member):
        return False
    if member.id == member.guild.owner_id or member.guild_permissions.administrator:
        return True
    high = staff_cfg(member.guild).get("high", [])
    return any(r.id in high for r in member.roles)

def is_mod_role(member):
    mod = staff_cfg(member.guild).get("mod", [])
    return any(r.id in mod for r in member.roles)

def staff_perms(**perms):
    """يفحص الصلاحيات المطلوبة؛ رتبة الإدارة العليا تتجاوز الفحص، ورتبة الإشراف
    المخصصة لا تمنح صلاحيات حساسة مثل إدارة الرتب لمجرد أنها رتبة إشراف."""
    mod_role_allowed = {
        "manage_messages", "manage_channels", "kick_members", "ban_members",
        "moderate_members",
    }

    async def predicate(ctx):
        m = ctx.author
        if not isinstance(m, discord.Member):
            raise commands.NoPrivateMessage()
        if is_admin(m):
            return True

        requested = {p for p, required in perms.items() if required}
        if is_mod_role(m) and requested and requested.issubset(mod_role_allowed):
            return True

        gp = m.guild_permissions
        missing = [p for p, required in perms.items()
                   if required and not getattr(gp, p, False)]
        if missing:
            raise commands.MissingPermissions(missing)
        return True
    return commands.check(predicate)

TARGET_CMDS = {"حظر", "طرد", "ميوت", "انهض", "تحذير", "عفو", "اعطاء", "سحب", "لفل", "خصم", "عملات"}
SELF_DENY = {"حظر", "طرد", "ميوت", "تحذير"}
BOT_ACTS = {"حظر", "طرد", "ميوت", "انهض", "اعطاء", "سحب"}

def hierarchy_problem(ctx, target):
    g, a, name = ctx.guild, ctx.author, ctx.command.name
    if target.id == g.owner_id and a.id != g.owner_id:
        return "👑 هذا أونر السيرفر، ما تگدر تنفذ عليه أي أمر إداري."
    if name in SELF_DENY and target.id == a.id:
        return "🤨 ما تگدر تنفذ هذا الأمر على نفسك."
    if a.id != g.owner_id and target.id != a.id and target.top_role >= a.top_role:
        return (f"🚫 ما تگدر تنفذ هذا الأمر على **{target.display_name}**، "
                f"رتبته (**{target.top_role.name}**) أعلى منك أو مساوية لرتبتك.")
    if name in BOT_ACTS and g.me and target.id != g.me.id and target.top_role >= g.me.top_role:
        return f"⚠️ رتبة البوت أقل من رتبة **{target.display_name}** — ارفع رتبة البوت فوقه حتى أنفذ الأمر."
    return None

def admin_only():
    async def predicate(ctx):
        if not is_admin(ctx.author):
            raise commands.CheckFailure("admin_only")
        return True
    return commands.check(predicate)

def find_channel(guild, names):
    for n in names:
        ch = discord.utils.get(guild.text_channels, name=n)
        if ch:
            return ch
    return None

def get_channel(guild, kind, names):
    cid = db.cfg(guild.id).get(kind)
    ch = guild.get_channel(cid) if cid else None
    return ch or find_channel(guild, names)

def target_is_manageable(ctx, member):
    if member.id in (ctx.author.id, ctx.guild.owner_id):
        return False
    if ctx.author.id != ctx.guild.owner_id and member.top_role >= ctx.author.top_role:
        return False
    if ctx.guild.me and member.top_role >= ctx.guild.me.top_role:
        return False
    return True

def norm_ar(text):
    t = re.sub(r"[\u064B-\u0652\u0640]", "", (text or "").lower())
    for a, b in (("أ", "ا"), ("إ", "ا"), ("آ", "ا"), ("ى", "ي"), ("ة", "ه"), ("ؤ", "و"), ("ئ", "ي"), ("گ", "ك"), ("چ", "ج"), ("پ", "ب")):
        t = t.replace(a, b)
    t = re.sub(r"[^\w\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()

# ── هوية البوت لكل سيرفر (الاسم/الأفاتار/البايو) ──
CUR_GUILD = contextvars.ContextVar("cur_guild", default=None)

def bot_name_set(guild=None):
    """الاسم الذي حدده أونر السيرفر بأمر تعيين_اسم، أو None إذا لم يُسمَّ البوت بعد."""
    guild = guild or CUR_GUILD.get()
    if guild is None:
        return None
    return (db.cfg(guild.id).get("bot_name") or "").strip() or None

def brand(guild=None):
    """(الاسم المعروض، الصورة، البايو). البوت ما عنده اسم ثابت: إذا الأونر ما سمّاه نعرض اسم السيرفر."""
    guild = guild or CUR_GUILD.get()
    c = db.cfg(guild.id) if guild else {}
    default = guild.name if guild else (bot.user.name if getattr(bot, "user", None) else "Bot")
    return (c.get("bot_name") or default), c.get("bot_avatar"), c.get("bot_bio")

def footer_text(guild=None):
    return f"{brand(guild)[0]} • {FOOTER_TAIL}"

def welcome_title(guild=None):
    return brand(guild)[0]

def E(title=None, desc=None, color=GOLD, footer=True):
    e = discord.Embed(title=title, description=desc, color=color, timestamp=discord.utils.utcnow())
    if footer:
        e.set_footer(text=footer_text())
    name, avatar, _ = brand()
    if avatar:
        e.set_author(name=name, icon_url=avatar)
    return e

def bar(ratio, n=12, full="🟪", empty="⬛"):
    k = max(0, min(n, int(ratio * n)))
    return full * k + empty * (n - k)

def fmt_dur(minutes):
    return f"{minutes // 60}س {minutes % 60}د"

async def asset_bytes(asset):
    try:
        return await asset.replace(size=256, format="png").read()
    except Exception:
        return None

# ───────────────────────── الرتب ─────────────────────────
async def make_role(guild, name, c1, c2=None, reason="Bot", hoist=False):
    role = discord.utils.get(guild.roles, name=name)
    if role:
        return role
    if c2 == c1:
        c2 = None
    if c2 is not None and "ENHANCED_ROLE_COLORS" in guild.features:
        try:
            data = await guild._state.http.create_role(
                guild.id, reason=reason, name=name, hoist=hoist,
                colors={"primary_color": c1, "secondary_color": c2, "tertiary_color": None},
            )
            role = discord.Role(guild=guild, state=guild._state, data=data)
            guild._add_role(role)
            return role
        except Exception:
            role = discord.utils.get(guild.roles, name=name)
            if role:
                return role
    color = blend(c1, c2) if c2 is not None else c1
    try:
        return await guild.create_role(name=name, color=discord.Color(color), hoist=hoist, reason=reason)
    except discord.HTTPException:
        return None

async def update_rank_role(guild, member, level):
    me = guild.me
    if not me or not me.guild_permissions.manage_roles:
        return
    specs = guild_role_specs(guild)
    roles = []
    for name in wanted_level_names(level, guild):
        role = discord.utils.get(guild.roles, name=name)
        if role is None:
            c1, c2 = specs[name]
            role = await make_role(guild, name, c1, c2, reason="Bot level role")
        if role:
            roles.append(role)
    managed = set(specs)
    old = [r for r in member.roles if r.name in managed and r not in roles]
    try:
        if old:
            await member.remove_roles(*old, reason="Bot level role update")
        add = [r for r in roles if r not in member.roles and r.position < me.top_role.position]
        if add:
            await member.add_roles(*add, reason="Bot level role update")
    except discord.HTTPException:
        pass

async def color_role(guild, number):
    name, value = COLOR_PALETTE[number]
    role = discord.utils.get(guild.roles, name=f"Color-{number}")
    if role is None:
        try:
            role = await guild.create_role(name=f"Color-{number}", color=discord.Color(value), reason="Bot color")
        except discord.HTTPException:
            return None
        try:
            await role.edit(position=max(1, guild.me.top_role.position - 1))
        except discord.HTTPException:
            pass
    return role

# ───────────────────────── XP واللفلات ─────────────────────────
def server_name(guild):
    """اسم السيرفر اللي يطلع برسائل البوت: الاسم اللي ضبطه الأدمن بـ (تعيين_اسم) وإلا اسم السيرفر نفسه."""
    return db.cfg(guild.id).get("bot_name") or guild.name

def xp_mult(guild):
    c = db.cfg(guild.id)
    until = float(c.get("xp_mult_until") or 0)
    if until and until < time.time():
        c.pop("xp_mult", None)
        c.pop("xp_mult_until", None)
        db.mark()
        return 1.0
    return float(c.get("xp_mult") or 1.0)

async def grant_xp(member, amount, channel=None, boost=False):
    """يضيف XP. boost=True يطبّق مضاعف الـ XP (رسائل/فويس فقط). عند كل ارتقاء ترسل تهنئة."""
    if boost:
        amount = int(amount * xp_mult(member.guild))
    u = db.user(member.id)
    before = int(u["level"])
    u["xp"] += max(0, int(amount))
    while u["level"] < MAX_LEVEL and u["xp"] >= xp_needed(u["level"]):
        u["xp"] -= xp_needed(u["level"])
        u["level"] += 1
        u["coins"] += u["level"] * 10
    db.mark()
    if u["level"] > before:
        try:
            await announce_level(member, u["level"], channel, old_level=before)
        except Exception as ex:
            print(f"[LEVEL] announce failed for {member.id}: {ex!r}")

LVL_VARS = {"{mention}": "منشن العضو", "{name}": "اسم العضو", "{level}": "اللفل الجديد",
            "{rank}": "اسم الرتبة", "{server}": "اسم السيرفر", "{congrats}": "جملة تهنئة عشوائية"}
DEFAULT_LVL_MSG = "{congrats} {mention}! 🎉 ارتقيت إلى **اللفل {level}** في **{server}**"

def render_lvl_msg(guild, member, level, title, template=None):
    tpl = template or db.cfg(guild.id).get("lvl_msg") or DEFAULT_LVL_MSG
    rep = {"{mention}": member.mention, "{name}": member.display_name, "{level}": str(level),
           "{rank}": title, "{server}": server_name(guild), "{congrats}": random.choice(CONGRATS)}
    for k, v in rep.items():
        tpl = tpl.replace(k, v)
    return tpl[:1800]

def build_levelup(member, level, old_level=None):
    """يبني رسالة التهنئة (إمبيد + ملف الصورة). النص والاسم يتغيرون حسب السيرفر."""
    guild = member.guild
    CUR_GUILD.set(guild)
    old_level = level - 1 if old_level is None else min(old_level, level - 1)
    title, color = rank_for(level, guild)
    nxt = next_rank(level, guild)
    coins = sum(l * 10 for l in range(old_level + 1, level + 1))
    jump = f"\n⬆️ قفزت من لفل `{old_level}` إلى لفل `{level}`!" if level - old_level > 1 else ""
    e = discord.Embed(
        title="⟡ ━━━━━━ 👑 𝐋𝐄𝐕𝐄𝐋 𝐔𝐏 👑 ━━━━━━ ⟡",
        description=f"{render_lvl_msg(guild, member, level, title)}{jump}",
        color=color, timestamp=discord.utils.utcnow(),
    )
    _, avatar, _ = brand(guild)
    e.set_author(name=f"{server_name(guild)} • ارتقاء جديد", icon_url=avatar or (guild.icon.url if guild.icon else None))
    e.add_field(name="🏆 اللفل", value=f"`{level}`", inline=True)
    e.add_field(name="👑 الرتبة", value=title, inline=True)
    e.add_field(name="🎁 المكافأة", value=f"`{coins:,}` عملة", inline=True)
    e.add_field(name="✨ المطلوب للّفل التالي", value=f"`{xp_needed(level):,}` XP", inline=True)
    e.add_field(name="🚀 الرتبة القادمة",
                value=(f"لفل `{nxt[0]}` — باقي `{nxt[0] - level}`" if nxt else "🏆 أعلى رتبة بالسيرفر!"), inline=True)
    e.set_thumbnail(url=member.display_avatar.url)
    e.set_footer(text=f"LEVEL {level} • {footer_text(guild)}")
    f = attach_media(e, "levelup", rank_media_key(level, guild))
    return e, f

def level_channel_for(guild, fallback=None):
    """روم اللفلات المضبوط، وإذا ماكو أو ما أگدر أكتب فيه: روم الكتابة الحالي، ثم روم النظام."""
    me = guild.me
    if me is None:
        return None
    for ch in (get_channel(guild, "level_channel", LEVEL_NAMES), fallback, guild.system_channel):
        if ch is None:
            continue
        p = ch.permissions_for(me)
        if p.send_messages and p.embed_links:
            return ch
    return None

async def announce_level(member, level, fallback=None, old_level=None):
    guild = member.guild
    CUR_GUILD.set(guild)
    try:
        await update_rank_role(guild, member, level)
    except Exception as ex:
        print(f"[LEVEL] role update failed: {ex!r}")
    ch = level_channel_for(guild, fallback)
    if ch is None:
        print(f"[LEVEL] {guild.name}: ماكو روم أرسل فيه التهنئة. اكتب: ضبط لفل #روم")
        return
    e, f = build_levelup(member, level, old_level)
    try:
        await ch.send(content=member.mention, embed=e, files=files_of(f))
    except discord.HTTPException as ex:
        print(f"[LEVEL] send failed in #{ch}: {ex!r}")

def leaderboard_entries(guild, key="level"):
    rows = []
    for uid, u in db.users():
        m = guild.get_member(uid)
        if m and not m.bot:
            rows.append((m, u))
    if key == "coins":
        rows.sort(key=lambda r: r[1]["coins"], reverse=True)
    else:
        rows.sort(key=lambda r: (r[1]["level"], r[1]["xp"]), reverse=True)
    return rows

# ───────────────────────── اللوقات ─────────────────────────
LOG_COLORS = {"green": 0x2ECC71, "red": 0xE74C3C, "orange": 0xE67E22, "blue": 0x3498DB,
              "purple": PURPLE, "gold": GOLD, "grey": 0x95A5A6}

async def log_event(guild, title, text="", color="purple", fields=None, thumb=None, media=None, user=None):
    channel = get_channel(guild, "log_channel", LOG_NAMES)
    if not channel:
        return
    e = discord.Embed(title=title, description=text[:3900] if text else None,
                      color=LOG_COLORS.get(color, color), timestamp=discord.utils.utcnow())
    for name, value, inline in (fields or []):
        e.add_field(name=name, value=(str(value) or "—")[:1000], inline=inline)
    if thumb:
        e.set_thumbnail(url=thumb)
    if user:
        e.set_author(name=f"{user}", icon_url=user.display_avatar.url)
    e.set_footer(text=f"{brand(guild)[0]} LOGS")
    f = attach_media(e, media) if media else None
    try:
        await channel.send(embed=e, files=files_of(f))
    except discord.HTTPException:
        pass

async def who_did(guild, action, target_id, seconds=15):
    try:
        async for entry in guild.audit_logs(limit=6, action=action):
            if getattr(entry.target, "id", None) == target_id and \
                    (discord.utils.utcnow() - entry.created_at).total_seconds() < seconds:
                return entry.user
    except (discord.Forbidden, discord.HTTPException):
        pass
    return None

# ───────────────────────── الأحداث ─────────────────────────
_synced = False

@bot.event
async def on_ready():
    global _synced
    if not _synced:
        _synced = True
        try:
            synced = await bot.tree.sync()
            print(f"Synced {len(synced)} slash commands.")
        except Exception as e:
            print(f"Slash sync warning: {e}")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="المملكة • مساعدة"))
    print(f"Bot online: {bot.user}")

async def send_welcome_gif(channel):
    """الجيف المضبوط فقط، بدون إطار/إيمبد وبحجم صغير."""
    try:
        entry = MEDIA_CACHE.get("welcome")
        if entry:
            data, fn = entry
            small = await asyncio.to_thread(shrink_media, data, 240)
            if small:
                data, fn = small[0], f"welcome{small[1]}"
            await channel.send(file=discord.File(io.BytesIO(data), filename=fn))
        else:
            url = db.data["_media"].get("welcome")
            if url:
                await channel.send(url)
    except Exception as e:
        print(f"[WELCOME] gif failed: {e!r}")

@bot.event
async def on_member_join(member):
    guild = member.guild
    CUR_GUILD.set(guild)
    u = db.user(member.id)
    await update_rank_role(guild, member, u["level"])
    channel = get_channel(guild, "welcome_channel", WELCOME_NAMES) or guild.system_channel
    if channel:
        num = guild.member_count
        circle = None
        if PIL_OK:
            try:
                av = await asset_bytes(member.display_avatar)
                if av:
                    png = await asyncio.to_thread(render_circle_avatar, av, 128)
                    circle = discord.File(png, filename="avatar.png")
            except Exception as e:
                print(f"[WELCOME] avatar failed: {e!r}")
        e = discord.Embed(
            title=f"⚔️ {welcome_title(guild)} ⚔️",
            description=(f"## يا هلا بـ {member.mention} 🖤\n"
                         f"أشرقت المملكة بقدومك، أنت العضو رقم **#{num:,}**\n"
                         f"📜 اقرأ القوانين • 🎨 اختار لونك • 🏆 تفاعل وارتقِ باللفلات"),
            color=GOLD, timestamp=discord.utils.utcnow(),
        )
        e.set_footer(text=footer_text(guild))
        if guild.icon:
            e.set_author(name=guild.name, icon_url=guild.icon.url)
        e.set_thumbnail(url="attachment://avatar.png" if circle else member.display_avatar.url)
        try:
            await channel.send(content=f"مرحباً بك {member.mention} 👑", embed=e, file=circle)
        except discord.HTTPException:
            pass
        await send_welcome_gif(channel)
    age = discord.utils.format_dt(member.created_at, "R")
    await log_event(guild, "📥 دخول عضو", f"{member.mention} — `{member}`", "green",
                    [("🔢 رقمه", f"#{guild.member_count:,}", True), ("🕰️ عمر الحساب", age, True),
                     ("🆔", member.id, True)], thumb=member.display_avatar.url, media="log_join")

@bot.event
async def on_member_remove(member):
    CUR_GUILD.set(member.guild)
    wch = get_channel(member.guild, "welcome_channel", WELCOME_NAMES)
    if wch:
        fe = E(f"👋 وداعاً من {brand(member.guild)[0]}",
               f"غادر **{member.display_name}** المملكة 💔\nعدد الأعضاء الآن **{member.guild.member_count:,}**", 0xE74C3C)
        fe.set_thumbnail(url=member.display_avatar.url)
        ff = attach_media(fe, "farewell")
        try:
            await wch.send(embed=fe, files=files_of(ff))
        except discord.HTTPException:
            pass
    roles = [r.mention for r in member.roles if r != member.guild.default_role and not is_managed_role(r)]
    joined = discord.utils.format_dt(member.joined_at, "R") if member.joined_at else "—"
    await log_event(member.guild, "📤 مغادرة عضو", f"{member.mention} — `{member}`", "red",
                    [("📅 كان منضم", joined, True), ("🆔", member.id, True),
                     ("🎭 رتبه", " ".join(roles[:15]) or "—", False)],
                    thumb=member.display_avatar.url, media="log_leave")

@bot.event
async def on_raw_message_delete(payload):
    if not payload.guild_id:
        return
    guild = bot.get_guild(payload.guild_id)
    if not guild:
        return
    msg = payload.cached_message
    log_ch = get_channel(guild, "log_channel", LOG_NAMES)
    if log_ch and payload.channel_id == log_ch.id:
        return
    ch = guild.get_channel(payload.channel_id)
    where = ch.mention if ch else f"<#{payload.channel_id}>"
    if msg is None:
        return await log_event(guild, "🗑️ حذف رسالة (غير محفوظة)", f"الروم: {where}\nID: `{payload.message_id}`", "red", media="log_delete")
    if msg.author.bot:
        return
    deleter = await who_did(guild, discord.AuditLogAction.message_delete, msg.author.id)
    fields = [("👤 الكاتب", msg.author.mention, True), ("📍 الروم", where, True),
              ("🗑️ حذفها", deleter.mention if deleter else "الكاتب نفسه / غير معروف", True)]
    if msg.attachments:
        fields.append(("📎 مرفقات", "\n".join(a.filename for a in msg.attachments)[:900], False))
    await log_event(guild, "🗑️ حذف رسالة", f"**المحتوى:**\n{(msg.content or '[بدون نص]')[:2500]}", "red", fields,
                    thumb=msg.author.display_avatar.url, media="log_delete")

@bot.event
async def on_bulk_message_delete(messages):
    if messages and messages[0].guild:
        await log_event(messages[0].guild, "🧹 حذف جماعي", f"تم حذف **{len(messages)}** رسالة في {messages[0].channel.mention}", "orange")

@bot.event
async def on_message_edit(before, after):
    if not before.guild or before.author.bot or before.content == after.content:
        return
    await log_event(before.guild, "✏️ تعديل رسالة", f"[انتقل للرسالة]({after.jump_url})", "blue",
                    [("👤 الكاتب", before.author.mention, True), ("📍 الروم", before.channel.mention, True),
                     ("📝 قبل", (before.content or "—")[:900], False), ("✅ بعد", (after.content or "—")[:900], False)],
                    thumb=before.author.display_avatar.url, media="log_edit")

@bot.event
async def on_member_update(before, after):
    g = after.guild
    if before.roles != after.roles:
        added = [r for r in after.roles if r not in before.roles and not is_managed_role(r)]
        removed = [r for r in before.roles if r not in after.roles and not is_managed_role(r)]
        if added or removed:
            by = await who_did(g, discord.AuditLogAction.member_role_update, after.id)
            fields = []
            if added: fields.append(("➕ أضيفت", " ".join(r.mention for r in added), False))
            if removed: fields.append(("➖ سُحبت", " ".join(r.mention for r in removed), False))
            if by: fields.append(("🛠️ بواسطة", by.mention, True))
            await log_event(g, "🎭 تغيير رتب", after.mention, "blue", fields, thumb=after.display_avatar.url)
    if before.nick != after.nick:
        await log_event(g, "📝 تغيير لقب", after.mention, "blue",
                        [("قبل", before.nick or "—", True), ("بعد", after.nick or "—", True)])
    if before.timed_out_until != after.timed_out_until:
        if after.timed_out_until:
            await log_event(g, "🔇 تايم أوت", f"{after.mention} حتى {discord.utils.format_dt(after.timed_out_until, 'f')}", "orange")
        else:
            await log_event(g, "🔊 فك تايم أوت", after.mention, "green")

@bot.event
async def on_member_ban(guild, user):
    by = await who_did(guild, discord.AuditLogAction.ban, user.id)
    await log_event(guild, "🔨 حظر", f"`{user}` ({user.id})", "red",
                    [("🛠️ بواسطة", by.mention if by else "غير معروف", True)], thumb=user.display_avatar.url)

@bot.event
async def on_member_unban(guild, user):
    await log_event(guild, "🕊️ فك حظر", f"`{user}` ({user.id})", "green")

@bot.event
async def on_guild_role_create(role):
    if role.guild.id not in QUIET and not is_managed_role(role):
        await log_event(role.guild, "➕ إنشاء رتبة", role.mention, "green")

@bot.event
async def on_guild_role_delete(role):
    if role.guild.id not in QUIET and not is_managed_role(role):
        await log_event(role.guild, "➖ حذف رتبة", f"`{role.name}`", "red")

@bot.event
async def on_guild_role_update(before, after):
    if is_managed_role(after):
        return
    ch = []
    if before.name != after.name: ch.append(("الاسم", f"{before.name} ← {after.name}", False))
    if before.color != after.color: ch.append(("اللون", f"{before.color} ← {after.color}", False))
    if before.permissions != after.permissions: ch.append(("الصلاحيات", "تم تغييرها", False))
    if ch:
        await log_event(after.guild, "🛠️ تعديل رتبة", after.mention, "blue", ch)

@bot.event
async def on_guild_channel_create(channel):
    if channel.guild.id in QUIET:
        return
    await log_event(channel.guild, "➕ إنشاء روم", f"{channel.mention} (`{channel.type}`)", "green")

@bot.event
async def on_guild_channel_delete(channel):
    if channel.guild.id in QUIET:
        return
    await log_event(channel.guild, "➖ حذف روم", f"`{channel.name}` (`{channel.type}`)", "red")

@bot.event
async def on_guild_channel_update(before, after):
    if after.guild.id in QUIET:
        return
    ch = []
    if before.name != after.name: ch.append(("الاسم", f"{before.name} ← {after.name}", False))
    if getattr(before, "topic", None) != getattr(after, "topic", None): ch.append(("الوصف", "تم تغييره", False))
    if ch:
        await log_event(after.guild, "🛠️ تعديل روم", after.mention, "blue", ch)

@bot.event
async def on_guild_update(before, after):
    ch = []
    if before.name != after.name: ch.append(("الاسم", f"{before.name} ← {after.name}", False))
    if before.icon != after.icon: ch.append(("الأيقونة", "تم تغييرها", False))
    if ch:
        await log_event(after, "⚙️ تعديل السيرفر", "", "gold", ch)

@bot.event
async def on_invite_create(invite):
    if invite.guild:
        await log_event(invite.guild, "🔗 إنشاء دعوة", f"`{invite.code}` بواسطة {invite.inviter.mention if invite.inviter else '—'}", "blue")

@bot.event
async def on_voice_state_update(member, before, after):
    if before.channel == after.channel:
        return
    if before.channel is None:
        await log_event(member.guild, "🎙️ دخول فويس", f"{member.mention} → {after.channel.mention}", "green")
    elif after.channel is None:
        await log_event(member.guild, "🎙️ خروج فويس", f"{member.mention} ← {before.channel.mention}", "red")
    else:
        await log_event(member.guild, "🎙️ تنقل فويس", f"{member.mention}: {before.channel.mention} ➜ {after.channel.mention}", "blue")

# ───────────────────────── الحماية ─────────────────────────
INVITE_RE = re.compile(r"(discord\.gg|discord(?:app)?\.com/invite)/\w+", re.I)
spam_track = defaultdict(lambda: deque(maxlen=8))
BLOCKED = set()

async def run_protection(message):
    member = message.author
    cfg = db.cfg(message.guild.id)
    if member.guild_permissions.manage_messages or is_admin(member):
        return False
    if len(BLOCKED) > 500:
        BLOCKED.clear()
    if cfg["antilink"] and INVITE_RE.search(message.content or ""):
        BLOCKED.add(message.id)
        try:
            await message.delete()
            await message.channel.send(f"🚫 {member.mention} ممنوع نشر روابط الدعوات هنا.", delete_after=6)
        except discord.HTTPException:
            pass
        await log_event(message.guild, "🚫 حماية: رابط دعوة", f"{member.mention} في {message.channel.mention}", "orange")
        return True
    if cfg["antispam"]:
        q = spam_track[(message.guild.id, member.id)]
        now = time.time()
        q.append(now)
        if len(q) >= 6 and now - q[-6] < 5:
            q.clear()
            BLOCKED.add(message.id)
            timed_out = False
            try:
                await member.timeout(
                    discord.utils.utcnow() + timedelta(minutes=5),
                    reason="Bot anti-spam",
                )
                timed_out = True
                await message.channel.send(
                    f"🛡️ {member.mention} تم إسكاتك 5 دقائق بسبب السبام.", delete_after=8
                )
            except discord.Forbidden:
                print(f"[PROTECTION] لا توجد صلاحية timeout للعضو {member.id} في {message.guild.id}")
            except discord.HTTPException as e:
                print(f"[PROTECTION] فشل timeout للعضو {member.id}: {e!r}")
            status = "تم إسكات العضو 5 دقائق" if timed_out else "تعذر الإسكات؛ تحقق من صلاحيات البوت وترتيب الرتب"
            await log_event(
                message.guild, "🛡️ حماية: سبام",
                f"{member.mention} في {message.channel.mention} — {status}", "orange"
            )
            return True
    return False

RAW_IDS = set()
AR_RE = re.compile(r"[\u0600-\u06FF]")

@bot.before_invoke
async def _set_cur_guild(ctx):
    CUR_GUILD.set(ctx.guild)
    if ctx.guild and ctx.command and ctx.command.name in TARGET_CMDS:
        target = next((v for v in list(ctx.args) + list(ctx.kwargs.values()) if isinstance(v, discord.Member)), None)
        if target is not None:
            msg = hierarchy_problem(ctx, target)
            if msg:
                raise HierarchyError(msg)

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if message.guild and isinstance(message.author, discord.Member):
        if await run_protection(message):
            return
        u = db.user(message.author.id)
        u["messages"] += 1
        db.mark()
        now = time.time()
        if now - float(u["last_xp"]) >= XP_COOLDOWN:
            u["last_xp"] = now
            await grant_xp(message.author, random.randint(XP_MIN, XP_MAX), message.channel, boost=True)
        content = (message.content or "").strip()
        if content and not content.startswith(PREFIX):
            first = content.split(maxsplit=1)[0]
            cmd = bot.get_command(first)
            usable = (cmd is not None and not cmd.hidden
                      and (first.lower() == "r" or AR_RE.search(first))
                      and (cmd.clean_params or content == first))  # أمر بلا وسائط يُنفَّذ فقط إذا كُتب وحده
            if usable:
                if len(RAW_IDS) > 500:
                    RAW_IDS.clear()
                RAW_IDS.add(message.id)
                message.content = PREFIX + content
            else:
                CUR_GUILD.set(message.guild)
                await chat_trigger(message)
    await bot.process_commands(message)

# ───────────────────────── الألوان (لون واحد فقط) ─────────────────────────
async def apply_color(interaction, number):
    if not interaction.guild or not isinstance(interaction.user, discord.Member):
        return await interaction.response.send_message("هذا الخيار داخل السيرفر فقط.", ephemeral=True)
    await interaction.response.defer(ephemeral=True)
    guild, member = interaction.guild, interaction.user
    name, _ = COLOR_PALETTE[number]
    role = await color_role(guild, number)
    if role is None:
        return await interaction.followup.send("تعذر إنشاء رتبة اللون. تأكد من صلاحية Manage Roles.", ephemeral=True)
    if guild.me and role.position >= guild.me.top_role.position:
        return await interaction.followup.send("ارفع رتبة البوت فوق رتب الألوان.", ephemeral=True)
    old = [r for r in member.roles if r.name.startswith("Color-") and r != role]
    try:
        if old:
            await member.remove_roles(*old, reason="Bot color change")
        if role not in member.roles:
            await member.add_roles(role, reason="Bot color change")
        await interaction.followup.send(f"✨ تم تطبيق اللون **{name}** (لون واحد فقط، واللون القديم انشال).", ephemeral=True)
    except discord.HTTPException:
        await interaction.followup.send("تعذر تطبيق اللون.", ephemeral=True)

async def clear_colors(interaction):
    if not isinstance(interaction.user, discord.Member):
        return await interaction.response.send_message("هذا الخيار داخل السيرفر فقط.", ephemeral=True)
    old = [r for r in interaction.user.roles if r.name.startswith("Color-")]
    if not old:
        return await interaction.response.send_message("ما عندك لون حتى ينلغي.", ephemeral=True)
    try:
        await interaction.user.remove_roles(*old, reason="Bot color clear")
        await interaction.response.send_message("🧹 تم إلغاء لونك.", ephemeral=True)
    except discord.HTTPException:
        await interaction.response.send_message("تعذر إلغاء اللون.", ephemeral=True)

class ColorSelect(discord.ui.Select):
    def __init__(self, start, end, cid):
        opts = [discord.SelectOption(label=f"{k} - {v[0]}"[:100], value=k)
                for k, v in list(COLOR_PALETTE.items())[start - 1:end]]
        super().__init__(placeholder=f"🎨 الألوان {start}–{end}", min_values=1, max_values=1,
                         options=opts, custom_id=cid)

    async def callback(self, interaction):
        await apply_color(interaction, self.values[0])

class ClearColorButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="إلغاء ألواني", emoji="❌", style=discord.ButtonStyle.danger,
                         custom_id="nx_color_clear", row=3)

    async def callback(self, interaction):
        await clear_colors(interaction)

class ColorView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ColorSelect(1, 20, "nx_color_a"))
        self.add_item(ColorSelect(21, 40, "nx_color_b"))
        self.add_item(ColorSelect(41, 50, "nx_color_c"))
        self.add_item(ClearColorButton())

def color_panel_embed():
    e = E("🎨 لوحة الألوان الملكية — 50 لوناً",
          "اختر **لوناً واحداً** من القوائم. اختيار لون جديد يلغي القديم تلقائياً.\nوإذا تبي تلغي لونك اضغط **❌ إلغاء ألواني**.")
    f = attach_media(e, "colors")
    return e, f

# ───────────────────────── المساعدة ─────────────────────────
HELP_SECTIONS = {
    "general": ("📘", "الأوامر العامة", "الأوامر الأساسية المتاحة للجميع.", [
        ("مساعدة", "مساعدة", "لوحة تفاعلية بكل الأقسام (قائمة + أزرار تنقّل)."),
        ("R", "R [@العضو]", "بطاقة واحدة فيها كل شي: لفل الكتابة + لفل الفويس + الترتيبين + الرسائل والعملات."),
        ("افتار", "افتار [@العضو]", "يعرض صورة العضو بحجم كبير."),
        ("سيرفر", "سيرفر", "معلومات عن السيرفر (الأعضاء، الرومات، البوست...)."),
        ("هوية", "هوية", "يعرض اسم البوت وبايو وصورة هذا السيرفر."),
        ("الوان", "الوان", "لوحة 50 لوناً، تختار منها لوناً واحداً فقط."),
        ("لون", "لون [1-50]", "يطبق اللون برقمه مباشرة."),
        ("الغاء_لون", "الغاء_لون", "يزيل لونك الحالي."),
        ("تحذيرات", "تحذيرات [@العضو]", "يعرض سجل التحذيرات."),
    ]),
    "levels": ("🏆", "قسم المستويات (Levels)", "نظام الـ XP والرتب والترتيب.", [
        ("R", "R [@العضو]", "بروفايلك بصورة واحدة: لفل الكتابة مع شريط الـ XP، ولفل الفويس مع ساعاتك."),
        ("مستويات", "مستويات", "يعرض رتب المملكة وتقدمك فيها."),
        ("المتصدرين", "المتصدرين [لفل]", "أعلى 10 أعضاء بالمستوى."),
    ]),
    "economy": ("💰", "قسم الكوينز (Economy)", "العملة الافتراضية والتحويل والمتجر.", [
        ("رصيد", "رصيد [@العضو]", "يعرض رصيد المحفظة."),
        ("راتب", "راتب", "راتبك اليومي من العملات (كل 20 ساعة)."),
        ("تحويل", "تحويل @العضو [المبلغ]", "يحوّل جزءاً من رصيدك لعضو آخر."),
        ("المتجر", "المتجر", "يعرض منتجات المتجر (رتب مدفوعة)."),
        ("شراء", "شراء [رقم المنتج]", "يشتري المنتج من رصيدك ويعطيك رتبته."),
        ("المتصدرين", "المتصدرين عملات", "أغنى 10 أعضاء."),
    ]),
    "mod": ("🛡️", "الإدارة العادية", "أوامر المشرفين اليومية.", [
        ("مسح", "مسح [العدد]", "يحذف عدد الرسائل المحدد من الروم (حتى 100)."),
        ("ميوت", "ميوت @العضو [الدقائق] [السبب]", "يسكت العضو (Timeout) للمدة المحددة، ويرسل له السبب على الخاص."),
        ("انهض", "انهض @العضو", "يفك الإسكات عن العضو."),
        ("تحذير", "تحذير @العضو [السبب]", "يسجل تحذيراً، وعند 3 و5 تحذيرات يُسكت تلقائياً."),
        ("عفو", "عفو @العضو", "يمسح كل تحذيرات العضو."),
        ("قفل", "قفل", "يمنع الكتابة في الروم الحالي."),
        ("فتح", "فتح", "يعيد الكتابة في الروم الحالي."),
        ("بطيء", "بطيء [الثواني]", "يضبط الوضع البطيء (0 للإلغاء)."),
    ]),
    "admin": ("👑", "الإدارة العليا", "الأوامر الحساسة (أدمن / أونر).", [
        ("حظر", "حظر @العضو [السبب]", "يحظر العضو نهائياً ويرسل له رسالة تفصيلية على الخاص بالسبب وتحذير رسمي."),
        ("رفع_حظر", "رفع_حظر [ID]", "يفك الحظر عن العضو."),
        ("طرد", "طرد @العضو [السبب]", "يطرد العضو من السيرفر مع إشعاره على الخاص."),
        ("انشاء_رتبة", "انشاء_رتبة [الاسم]", "ينشئ رتبة جديدة."),
        ("اصنع", "اصنع [الاسم] [لون] [لون2] [رابط صورة]", "ينشئ رتبة بلونين وأيقونة."),
        ("حذف_رتبة", "حذف_رتبة @الرتبة", "يحذف الرتبة من السيرفر."),
        ("اعطاء", "اعطاء @العضو @الرتبة", "يعطي العضو رتبة."),
        ("سحب", "سحب @العضو @الرتبة", "يسحب الرتبة من العضو."),
        ("عملات", "عملات @العضو [المبلغ]", "يضيف أو يخصم عملات (بالسالب للخصم)."),
        ("طوارئ", "طوارئ", "يقفل كل الرومات الكتابية فوراً."),
        ("استقرار", "استقرار", "يعيد فتح الرومات بعد الطوارئ."),
        ("إعلان", "إعلان [النص]", "ينشر إعلاناً رسمياً مع منشن مخفي للجميع، وتحته الخط."),
    ]),
    "custom": ("🎖️", "تخصيص الإعلان والرتب", "كل سيرفر يضبط خطه وصوره ورتب لفلاته.", [
        "📢 الإعلان",
        ("تعيين_خط", "تعيين_خط [رابط صورة/GIF]", "يضبط الخط الذي يظهر تحت الإعلان (أو تغير_خط؛ `حذف` لإزالته)."),
        ("خط", "خط", "يرسل الخط المضبوط بالروم."),
        ("تعيين_صورة_الاعلان", "تعيين_صورة_الاعلان [رابط]", "الصورة الرئيسية (السوداء) أسفل نص الإعلان، صورة أو GIF."),
        ("تعيين_صورة_الجانب", "تعيين_صورة_الجانب [رابط]", "الصورة الجانبية (الحمراء) على يمين الإعلان، صورة أو GIF."),
        ("اعدادات_الاعلان", "اعدادات_الاعلان", "يعرض ما هو مضبوط للإعلان."),
        "🎖️ رتب اللفلات",
        ("انشاء_رتب_لفل", "انشاء_رتب_لفل + سطر لكل رتبة: [اللفل] [الاسم] [لون] [لون2]", "ينشئ كل رتب اللفلات دفعة واحدة برسالة واحدة ويعتمدها البوت لهذا السيرفر."),
        ("حذف_رتب_لفل", "حذف_رتب_لفل", "يحذف كل رتب اللفلات من السيرفر بعد تأكيد (مستويات الأعضاء تبقى)."),
        ("تعيين_الفلات", "تعيين_الفلات [اللفل] [الاسم] [لون] [لون2] [رابط]", "يضيف أو يعدّل رتبة لفل (بدون وسائط يعرض الرتب)."),
        ("حذف_فلات", "حذف_فلات [اللفل]", "يحذف رتبة لفل من السيرفر."),
        ("تعيين_نيو_مبر", "تعيين_نيو_مبر [الاسم] [لون] [لون2]", "يغيّر شكل/اسم رتبة العضو الجديد، أو `حذف`."),
        ("رتب_كل_5", "رتب_كل_5 [تشغيل|ايقاف|اسم]", "يتحكم برتب كل 5 لفلات."),
        ("ثيم_الفلات", "ثيم_الفلات [ناري|جليدي|نيون|كوني|ملكي]", "يطبّق ستايل جاهز بتدرجات لونية."),
        ("اعادة_الفلات", "اعادة_الفلات", "يمسح إعدادات اللفلات (بدون حذف الرتب من السيرفر)."),
        ("مزامنة_الرتب", "مزامنة_الرتب", "يحدّث رتب كل الأعضاء حسب الإعدادات."),
    ]),
    "setup": ("⚙️", "الإعداد والتخصيص", "تجهيز السيرفر وهوية البوت والجيفات.", [
        ("تجهيز", "تجهيز [رتب|رومات|لوغات|حماية]", "تجهيز اختياري للرتب والرومات ولوقات كل أمر إداري والحماية."),
        ("ضبط", "ضبط", "يفتح لوحة تفاعلية لضبط كل الرومات بالقوائم (التفاصيل بقسم 📍 ضبط الرومات)."),
        ("حماية", "حماية [رابط|سبام]", "يعرض أو يبدل حالة الحماية."),
        ("تعيين_اسم", "تعيين_اسم [الاسم]", "يغيّر اسم البوت في هذا السيرفر فقط (اللقب + كل الرسائل التلقائية)."),
        ("تعيين_بايو", "تعيين_بايو [النص]", "يضبط بايو البوت لهذا السيرفر."),
        ("تعيين_افتار", "تعيين_افتار [رابط أو أرفق صورة]", "يضبط صورة البوت لهذا السيرفر."),
        ("اعادة_هوية", "اعادة_هوية", "يرجع هوية البوت للافتراضية."),
        ("اضافة_جيف", "اضافة_جيف [ترحيب|لفل|وداع] [الرابط]", "يضبط جيف الترحيب أو اللفل أو الوداع."),
        ("اضافة_جيف شات", "اضافة_جيف شات [الكلمة] [الرابط]", "عند كتابة الكلمة بالشات يرسل البوت الجيف تلقائياً."),
        ("حذف_جيف", "حذف_جيف [شات الكلمة | ترحيب | لفل | وداع]", "يحذف جيفاً."),
        ("الجيفات", "الجيفات", "يعرض الجيفات والردود التلقائية."),
        ("اضافة_منتج", "اضافة_منتج [السعر] @الرتبة [الاسم]", "يضيف منتجاً للمتجر."),
        ("حذف_منتج", "حذف_منتج [رقم]", "يحذف منتجاً من المتجر."),
        ("صور", "صور", "يعرض مفاتيح الصور المتاحة."),
        ("صورة", "صورة [المفتاح] [الرابط]", "يضبط صورة أي رسالة، وبنر أي قسم بالمساعدة: `صورة help_mod رابط` (بدونها يتولّد بنر تلقائي)."),
    ]),
}


HELP_SECTIONS["xpadmin"] = ("⚡", "إدارة الـ XP واللفلات", "إعطاء XP، مضاعفات، وتخصيص رسالة التهنئة.", [
    "⚡ إدارة الـ XP",
    ("اكس_بي", "اكس_بي @العضو [المبلغ]", "يعطي العضو XP، ولو ارتقى تجي تهنئة اللفل تلقائياً."),
    ("ازالة_اكس_بي", "ازالة_اكس_بي @العضو [المبلغ]", "ينقص XP من العضو (وينزّل لفله إذا لزم)."),
    ("لفل", "لفل @العضو [المستوى]", "يضبط مستوى العضو مباشرة."),
    ("خصم", "خصم @العضو [عدد]", "ينقص لفلات من العضو."),
    "🔥 مضاعف الـ XP",
    ("مضاعف_اكس_بي", "مضاعف_اكس_بي [المضاعف] [الدقائق]", "حدث XP مضاعف، مثال: `مضاعف_اكس_بي 2 60` (بدون وسائط يعرض الحالة)."),
    ("ايقاف_المضاعف", "ايقاف_المضاعف", "يوقف المضاعف فوراً."),
    "🎉 تهنئة اللفل",
    ("ضبط لفل", "ضبط لفل #روم", "الروم اللي تنرسل فيه تهنئة كل ارتقاء."),
    ("رسالة_لفل", "رسالة_لفل [نص]", "يخصص نص التهنئة لهذا السيرفر (متغيرات: {mention} {level} {rank} {server})."),
    ("تجربة_لفل", "تجربة_لفل [@العضو] [المستوى]", "يعرض شكل التهنئة بدون ما يغيّر شي بمستوى أحد."),
    ("فحص_اللفل", "فحص_اللفل", "فحص سريع: الروم، الصلاحيات، رتبة البوت، وإعدادات الـ XP."),
])
HELP_SECTIONS["rooms"] = ("📍", "ضبط الرومات", "تحديد روم الترحيب واللفل واللوقات وغيرها.", [
    "🖱️ بالقوائم (الأسهل)",
    ("ضبط", "ضبط", "يفتح لوحة تفاعلية: اختر الخدمة ثم الروم، أو أنشئ روماً جديداً بزر."),
    ("سجلات", "سجلات", "يعرض حالة لوقات الأوامر الإدارية."),
    "⌨️ بالكتابة",
    ("ضبط ترحيب", "ضبط ترحيب #روم", "روم بطاقة الترحيب ورسالة الوداع."),
    ("ضبط لفل", "ضبط لفل #روم", "روم تهنئة الارتقاء بالمستويات."),
    ("ضبط لوق", "ضبط لوق #روم", "روم لوقات السيرفر العامة."),
    ("ضبط فعاليات / اقتراحات / الوان", "ضبط فعاليات #روم  |  ضبط اقتراحات #روم  |  ضبط الوان #روم", "روم الجيفاواي والفعاليات، روم الاقتراحات، وروم لوحة الألوان."),
    ("ضبط_حظر ...", "ضبط_حظر #روم  (أو طرد، ميوت، تحذير...)", "لوق مستقل لكل أمر إداري."),
    ("انشاء / حذف", "ضبط لفل انشاء  |  ضبط لفل حذف", "ينشئ روماً جديداً ويربطه، أو يلغي الربط."),
])

# ألوان وأشكال كل قسم بالمساعدة: (الاسم الإنجليزي، لون 1، لون 2، الزخرفة)
HELP_META = {
    "home":      ("HELP CENTER",   (88, 101, 242), (155, 89, 245), "rings"),
    "general":   ("GENERAL",       (52, 152, 219), (0, 200, 220),  "dots"),
    "levels":    ("LEVELS",        (241, 196, 15), (230, 126, 34), "rings"),
    "voice":     ("VOICE",         (0, 190, 220),  (150, 80, 235), "waves"),
    "economy":   ("ECONOMY",       (46, 204, 113), (241, 196, 15), "dots"),
    "tools":     ("TOOLS",         (26, 188, 156), (52, 152, 219), "stripes"),
    "events":    ("EVENTS",        (233, 30, 99),  (255, 152, 0),  "rings"),
    "mod":       ("MODERATION",    (52, 120, 246), (99, 102, 241), "stripes"),
    "admin":     ("ADMIN",         (231, 76, 60),  (150, 30, 60),  "stripes"),
    "xpadmin":   ("XP CONTROL",    (155, 89, 182), (233, 30, 140), "waves"),
    "rooms":     ("CHANNELS",      (22, 160, 133), (39, 174, 96),  "dots"),
    "structure": ("STRUCTURE",     (93, 109, 126), (52, 152, 219), "stripes"),
    "custom":    ("CUSTOMIZE",     (214, 51, 132), (255, 140, 0),  "waves"),
    "setup":     ("SETUP",         (96, 125, 139), (0, 150, 200),  "rings"),
}

def _help_meta(key):
    return HELP_META.get(key) or (key.upper(), (88, 101, 242), (155, 89, 245), "rings")

def render_help_banner(key, title_ar, count, brand_name=""):
    """بنر القسم: تدرج لوني + زخرفة + اسم القسم + عدد الأوامر (يتولّد برمجياً بدون إنترنت)."""
    W, H = 1000, 260
    en, c1, c2, motif = _help_meta(key)
    base = _gradient(W, H, tuple(int(v * 0.62) for v in c1), tuple(int(v * 0.40) for v in c2)).convert("RGBA")
    deco = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dd = ImageDraw.Draw(deco)
    white_a = lambda a: (255, 255, 255, a)
    if motif == "rings":
        for i, r in enumerate(range(90, 520, 70)):
            dd.ellipse((W - 150 - r, 40 - r, W - 150 + r, 40 + r), outline=white_a(34 - i * 3), width=3)
    elif motif == "stripes":
        for x in range(-H, W, 46):
            dd.polygon([(x, H), (x + 22, H), (x + 22 + H, 0), (x + H, 0)], fill=white_a(14))
    elif motif == "dots":
        for gx in range(30, W, 34):
            for gy in range(24, H, 34):
                dd.ellipse((gx, gy, gx + 5, gy + 5), fill=white_a(30))
    else:  # waves
        for k in range(6):
            pts = [(x, 150 + k * 18 + int(math.sin((x + k * 40) / 55.0) * 26)) for x in range(0, W + 1, 10)]
            dd.line(pts, fill=white_a(34 - k * 4), width=3)
    dd.ellipse((-120, H - 120, 220, H + 150), fill=c2 + (60,))
    base = Image.alpha_composite(base, deco)
    d = ImageDraw.Draw(base)
    d.rounded_rectangle((10, 10, W - 11, H - 11), radius=28, outline=white_a(90), width=2)

    # شارة عدد الأوامر (يسار)
    cx, cy, R = 150, H // 2, 78
    badge = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(badge)
    bd.ellipse((cx - R, cy - R, cx + R, cy + R), fill=(0, 0, 0, 110), outline=white_a(200), width=4)
    base = Image.alpha_composite(base, badge)
    d = ImageDraw.Draw(base)
    d.text((cx, cy - 10), str(count), font=get_font(64), fill=(255, 255, 255), anchor="mm")
    d.text((cx, cy + 40), "COMMANDS", font=get_font(15), fill=(235, 235, 255), anchor="mm")

    # العنوان (يمين)
    tx = W - 56
    t = ar(title_ar)
    d.text((tx, 52), t, font=_fit_text(d, t, W - 330, 70, 30), fill=(255, 255, 255), anchor="ra")
    d.text((tx, 160), "  ".join(en), font=get_font(30), fill=(255, 255, 255, 235), anchor="ra")
    d.line([(tx - 170, 146), (tx, 146)], fill=white_a(170), width=3)
    if brand_name:
        bn = ar(clean_name(brand_name))
        d.text((tx, 212), bn, font=_fit_text(d, bn, 420, 22, 14), fill=(235, 235, 255), anchor="ra")
    out = io.BytesIO()
    base.convert("RGB").save(out, "PNG")
    return out.getvalue()

HELP_ORDER = ["general", "levels", "voice", "economy", "tools", "events", "mod", "admin", "xpadmin", "rooms", "structure", "custom", "setup"]
HELP_LOCKED = {"events", "mod", "admin", "xpadmin", "rooms", "structure", "custom", "setup"}   # أقسام الإدارة

def help_is_staff(member):
    """الأعضاء العاديون ما يشوفون أقسام الإدارة بقائمة المساعدة."""
    if not isinstance(member, discord.Member):
        return False
    perms = member.guild_permissions
    return bool(is_admin(member) or is_mod_role(member) or perms.manage_messages or perms.manage_guild)

def help_keys(staff=True):
    keys = [k for k in HELP_ORDER if k in HELP_SECTIONS]
    keys += [k for k in HELP_SECTIONS if k not in keys]
    return keys if staff else [k for k in keys if k not in HELP_LOCKED]

def help_count(key):
    return sum(1 for it in HELP_SECTIONS[key][3] if not isinstance(it, str))

def help_title(key):
    return HELP_SECTIONS[key][1].split("(")[0].strip()

def help_color(key):
    c = _help_meta(key)[1]
    return (c[0] << 16) | (c[1] << 8) | c[2]

def help_search(query, staff=True):
    """بحث نصي في كل الأوامر (الاسم/الاستخدام/الشرح)."""
    q = norm_ar(query)
    if len(q) < 2:
        return []
    hits = []
    for k in help_keys(staff):
        icon, nm, _intro, items = HELP_SECTIONS[k]
        for it in items:
            if not isinstance(it, str) and q in norm_ar(" ".join(str(x) for x in it)):
                hits.append((icon, nm, it))
    return hits

_help_banner_cache = {}

async def help_banner(e, key, guild, staff=True):
    """يحط صورة القسم بالـ embed: صورتك المخصصة (`صورة help_<القسم> رابط`) أو بنر يتولّد تلقائياً.
    يرجع discord.File أو None."""
    f = attach_media(e, "help_home", "help") if key == "home" else attach_media(e, f"help_{key}")
    if f is not None or (e.image and e.image.url):
        return f
    if not PIL_OK:
        return None
    if key == "home":
        title = "مركز المساعدة"
        count = len({it[0] for k in help_keys(staff) for it in HELP_SECTIONS[k][3] if not isinstance(it, str)})
    else:
        title, count = help_title(key), help_count(key)
    brand_name = brand(guild)[0]
    ck = (key, title, count, brand_name)
    data = _help_banner_cache.get(ck)
    if data is None:
        try:
            data = await asyncio.to_thread(render_help_banner, key, title, count, brand_name)
        except Exception as ex:
            print(f"[HELP] banner failed: {ex!r}")
            return None
        if len(_help_banner_cache) > 80:
            _help_banner_cache.clear()
        _help_banner_cache[ck] = data
    fn = f"help_{key}.png"
    e.set_image(url=f"attachment://{fn}")
    return discord.File(io.BytesIO(data), filename=fn)

def help_home(guild=None, staff=True):
    guild = guild or CUR_GUILD.get()
    name = brand(guild)[0]
    e = E(f"📚 مركز مساعدة {name}",
          "> اختر القسم من **القائمة** 👇 أو تنقّل بالأزرار\n"
          "> ✦ الأوامر تُكتب **بدون** `!` — مثال: `حظر @عضو السبب`\n"
          "> 🔎 ما لقيت أمرك؟ اضغط **بحث**", 0x5865F2)
    pub, locked = [], []
    for k in help_keys(staff):
        icon = HELP_SECTIONS[k][0]
        (locked if k in HELP_LOCKED else pub).append(f"{icon} **{help_title(k)}** ‹`{help_count(k)}`›")
    e.add_field(name="👥 للجميع", value="\n".join(pub) or "—", inline=True)
    if staff and locked:
        e.add_field(name="🔒 للإدارة فقط", value="\n".join(locked), inline=True)
    e.add_field(name="✨ ابدأ من هنا", inline=False,
                value="`R` بروفايلك كامل (لفل الكتابة + الفويس) • `توب_فويس` ترتيب الساعات • `مستويات` رتبك\n"
                      "`الوان` لونك • `راتب` عملاتك اليومية • `معلومات` عن أي عضو")
    e.add_field(name="🆕 أدوات جديدة", inline=False,
                value="🎫 `تذكرة_لوحة` • 💡 `اقتراح` • 📊 `تصويت` • ⏰ `ذكرني` • 🏓 `بنق`")
    return e

def help_embed(key, staff=True):
    icon, name, intro, items = HELP_SECTIONS[key]
    keys = help_keys(staff)
    pos = keys.index(key) + 1 if key in keys else 1
    lock = "  🔒 *للإدارة فقط*" if key in HELP_LOCKED else ""
    e = E(f"{icon}  {help_title(key)}",
          f"> {intro}{lock}\n> ✦ الأوامر تُكتب **بدون** `!` — مثال: `حظر @عضو السبب`", help_color(key))
    groups, cur = [], None
    for it in items:
        if isinstance(it, str):
            cur = [it, []]
            groups.append(cur)
        else:
            if cur is None:
                cur = ["📌 الأوامر", []]
                groups.append(cur)
            cur[1].append(it)
    for title, cmds in groups:
        chunk, first = "", True
        for c in cmds:
            line = f"▸ `{c[1]}`\n　↳ {c[2]}\n"
            if chunk and len(chunk) + len(line) > 1000:
                e.add_field(name=f"〔 {title} 〕" if first else f"〔 {title} — تابع 〕", value=chunk, inline=False)
                chunk, first = "", False
            chunk += line
        if chunk:
            e.add_field(name=f"〔 {title} 〕" if first else f"〔 {title} — تابع 〕", value=chunk, inline=False)
        if len(e) > 5400:
            e.add_field(name="…", value="القسم طويل — استخدم 🔎 **بحث** للوصول لأي أمر.", inline=False)
            break
    e.set_footer(text=f"{footer_text()} • القسم {pos}/{len(keys)} • {help_count(key)} أمر")
    return e

async def help_payload(guild, key, staff):
    """(embed + صورة القسم) جاهزة لـ send أو edit_message."""
    CUR_GUILD.set(guild)
    e = help_home(guild, staff) if key is None else help_embed(key, staff)
    f = await help_banner(e, key or "home", guild, staff)
    return {"embed": e, "attachments": [f] if f else []}

class HelpSelect(discord.ui.Select):
    def __init__(self, staff=True):
        opts = [discord.SelectOption(
                    label=(("🔒 " if k in HELP_LOCKED else "") + help_title(k))[:90], value=k,
                    emoji=HELP_SECTIONS[k][0], description=HELP_SECTIONS[k][2][:90]) for k in help_keys(staff)][:25]
        super().__init__(placeholder="📂 اختر القسم", options=opts, row=0)

    async def callback(self, interaction):
        v = self.view
        v.key = self.values[0]
        await interaction.response.edit_message(view=v, **await help_payload(interaction.guild, v.key, v.staff))

class HelpSearchModal(discord.ui.Modal, title="🔎 البحث في الأوامر"):
    query = discord.ui.TextInput(label="اكتب كلمة أو اسم أمر", placeholder="مثال: فويس • حظر • تذكرة • جيفاواي",
                                 min_length=2, max_length=40)

    def __init__(self, staff=True):
        super().__init__()
        self.staff = staff

    async def on_submit(self, interaction):
        CUR_GUILD.set(interaction.guild)
        text = str(self.query.value)
        hits = help_search(text, self.staff)
        if not hits:
            return await interaction.response.send_message(f"🔎 ما لقيت أوامر تطابق **{text[:40]}**.", ephemeral=True)
        lines, size = [], 0
        for icon, nm, it in hits[:10]:
            line = f"{icon} **{it[0]}** — `{it[1]}`\n　↳ {it[2]}"
            if size + len(line) > 3500:
                break
            lines.append(line)
            size += len(line)
        e = E(f"🔎 نتائج «{text[:40]}»", "\n\n".join(lines), PURPLE)
        if len(hits) > len(lines):
            e.set_footer(text=f"عرض {len(lines)} من {len(hits)} — دقّق كلمة البحث")
        await interaction.response.send_message(embed=e, ephemeral=True)

class HelpView(discord.ui.View):
    def __init__(self, author_id=None, staff=True):
        super().__init__(timeout=300)
        self.author_id, self.key, self.message, self.staff = author_id, None, None, staff
        self.add_item(HelpSelect(staff))

    async def interaction_check(self, interaction):
        CUR_GUILD.set(interaction.guild)
        if self.author_id is None or interaction.user.id == self.author_id:
            return True
        await interaction.response.send_message("❌ هذي اللوحة مو إلك، اكتب `مساعدة` لتفتح لوحتك.", ephemeral=True)
        return False

    async def _go(self, interaction, step):
        keys = help_keys(self.staff)
        i = keys.index(self.key) if self.key in keys else (-1 if step > 0 else 0)
        self.key = keys[(i + step) % len(keys)]
        await interaction.response.edit_message(view=self, **await help_payload(interaction.guild, self.key, self.staff))

    @discord.ui.button(label="السابق", emoji="◀️", style=discord.ButtonStyle.secondary, row=1)
    async def prev(self, interaction, button):
        await self._go(interaction, -1)

    @discord.ui.button(label="الرئيسية", emoji="🏠", style=discord.ButtonStyle.primary, row=1)
    async def home(self, interaction, button):
        self.key = None
        await interaction.response.edit_message(view=self, **await help_payload(interaction.guild, None, self.staff))

    @discord.ui.button(label="التالي", emoji="▶️", style=discord.ButtonStyle.secondary, row=1)
    async def nxt(self, interaction, button):
        await self._go(interaction, 1)

    @discord.ui.button(label="بحث", emoji="🔎", style=discord.ButtonStyle.success, row=1)
    async def search_btn(self, interaction, button):
        await interaction.response.send_modal(HelpSearchModal(self.staff))

    @discord.ui.button(label="إغلاق", emoji="✖️", style=discord.ButtonStyle.danger, row=1)
    async def close(self, interaction, button):
        self.stop()
        await interaction.response.edit_message(view=None)

    async def on_timeout(self):
        if self.message:
            try:
                await self.message.edit(view=None)
            except discord.HTTPException:
                pass

@bot.command(name="مساعدة", aliases=["help", "اوامر"])
async def help_command(ctx):
    staff = help_is_staff(ctx.author)
    payload = await help_payload(ctx.guild, None, staff)
    view = HelpView(ctx.author.id, staff)
    view.message = await ctx.send(embed=payload["embed"], files=payload["attachments"] or None, view=view)

# ═════════════════════════ نظام الفويس (لفل + ساعات) ═════════════════════════
# • لفل الفويس مستقل تماماً عن لفل الكتابة، ويُحسب فقط من عدد ساعات الجلسات بالفويس.
# • الأمر  R  يعرض بطاقة واحدة فيها لفل الكتابة + لفل الفويس (الساعات والترتيب).
# • ترتيب الفويس حسب الساعات فقط (وليس حسب الـ XP أو لفل الكتابة).
# • الساعات تُحفظ لكل سيرفر على حدة داخل u["vc"][guild_id].
VC_MAX_LEVEL = 100

def vc_need(level):
    """الدقائق المجمّعة المطلوبة للوصول للفل فويس معيّن (1س → لفل 1، 3س → لفل 2، 6س → لفل 3 ...)."""
    return 30 * level * (level + 1)

def vc_level_of(minutes):
    minutes = max(0, int(minutes))
    lvl = int((math.sqrt(1 + 8 * minutes / 60) - 1) / 2)
    while lvl < VC_MAX_LEVEL and vc_need(lvl + 1) <= minutes:
        lvl += 1
    while lvl > 0 and vc_need(lvl) > minutes:
        lvl -= 1
    return min(lvl, VC_MAX_LEVEL)

def vc_cfg(guild):
    return db.cfg(guild.id).setdefault("vc", {})

def vc_min_humans(guild):
    try:
        return max(1, min(10, int(vc_cfg(guild).get("min", 2))))
    except (TypeError, ValueError):
        return 2

def vc_minutes(guild, uid):
    """دقائق الفويس لهذا العضو في هذا السيرفر."""
    u = db.user(uid)
    vc = u.get("vc")
    if isinstance(vc, dict) and str(guild.id) in vc:
        return int(vc[str(guild.id)])
    # بيانات قديمة (قبل التتبع لكل سيرفر): نعتبرها لهذا السيرفر فقط إذا كان البوت بسيرفر واحد
    if not vc and len(bot.guilds) <= 1:
        return int(u.get("voice_minutes", 0))
    return 0

def vc_set(guild, uid, minutes):
    u = db.user(uid)
    if not isinstance(u.get("vc"), dict):
        u["vc"] = {}
    u["vc"][str(guild.id)] = max(0, int(minutes))
    db.mark()

def vc_add(guild, uid, minutes=1):
    vc_set(guild, uid, vc_minutes(guild, uid) + minutes)

def vc_entries(guild):
    """[(member, minutes)] مرتبة حسب الساعات فقط."""
    rows = []
    for uid, _u in db.users():
        m = guild.get_member(uid)
        if m and not m.bot:
            mins = vc_minutes(guild, uid)
            if mins > 0:
                rows.append((m, mins))
    rows.sort(key=lambda r: r[1], reverse=True)
    return rows

def vc_rank_of(guild, member):
    rows = vc_entries(guild)
    pos = next((i for i, (m, _) in enumerate(rows, 1) if m.id == member.id), len(rows) + 1)
    return pos, max(len(rows), pos)

def fmt_hours(minutes):
    return f"{minutes // 60:,}س {minutes % 60}د"

def render_voice_card(avatar_bytes, name, vlevel, minutes, pos, total):
    W, H = 940, 270
    c1, c2 = (0, 190, 220), (150, 70, 230)
    base = _gradient(W, H, (6, 30, 52), (30, 10, 56)).convert("RGBA")
    d = ImageDraw.Draw(base)
    d.rounded_rectangle((12, 12, W - 13, H - 13), radius=26, outline=c1, width=3)
    S = 150
    ax, ay = 40, 45
    d.ellipse((ax - 7, ay - 7, ax + S + 7, ay + S + 7), fill=c2)
    d.ellipse((ax - 3, ay - 3, ax + S + 3, ay + S + 3), fill=(12, 8, 28))
    try:
        av = _circle(Image.open(io.BytesIO(avatar_bytes)), S)
        base.paste(av, (ax, ay), av)
    except Exception:
        pass
    d = ImageDraw.Draw(base)
    x = 230
    nm = ar(clean_name(name))
    d.text((x, 28), nm, font=_fit_text(d, nm, W - x - 250, 44), fill=(255, 255, 255))
    d.text((x, 88), "VOICE RANK", font=get_font(26), fill=(120, 230, 255))
    d.text((W - 40, 30), f"VOICE LV {vlevel}", font=get_font(40), fill=(255, 255, 255), anchor="ra")
    d.text((W - 40, 82), f"#{pos}/{total} BY HOURS", font=get_font(24), fill=(210, 210, 255), anchor="ra")
    base_min = vc_need(vlevel) if vlevel > 0 else 0
    if vlevel >= VC_MAX_LEVEL:
        ratio, label = 1.0, "MAX LEVEL"
    else:
        nxt = vc_need(vlevel + 1)
        ratio = (minutes - base_min) / max(1, nxt - base_min)
        label = f"{max(0, nxt - minutes) // 60}h {max(0, nxt - minutes) % 60}m to LV {vlevel + 1}"
    bx, by, bw, bh = x, 135, W - x - 40, 34
    d.rounded_rectangle((bx, by, bx + bw, by + bh), radius=17, fill=(0, 0, 0, 170))
    ratio = max(0.0, min(1.0, ratio))
    if ratio > 0:
        fw = max(bh, int(bw * ratio))
        bar_img = _gradient(fw, bh, c1, c2).convert("RGBA")
        m = Image.new("L", (fw, bh), 0)
        ImageDraw.Draw(m).rounded_rectangle((0, 0, fw - 1, bh - 1), radius=17, fill=255)
        base.paste(bar_img, (bx, by), m)
    d = ImageDraw.Draw(base)
    d.text((bx + bw // 2, by + bh // 2), label, font=get_font(20), fill=(255, 255, 255), anchor="mm")
    d.text((x, 195), f"{minutes // 60:,}h {minutes % 60}m", font=get_font(36), fill=(255, 255, 255))
    d.text((x, 240), "TOTAL VOICE TIME", font=get_font(16), fill=(170, 200, 230))
    out = io.BytesIO()
    base.convert("RGB").save(out, "PNG")
    out.seek(0)
    return out

async def build_voice(member):
    """(embed, file|None) لبطاقة الفويس."""
    guild = member.guild
    mins = vc_minutes(guild, member.id)
    lvl = vc_level_of(mins)
    pos, total = vc_rank_of(guild, member)
    card = None
    if PIL_OK:
        try:
            av = await asset_bytes(member.display_avatar)
            if av:
                png = await asyncio.to_thread(render_voice_card, av, member.display_name, lvl, mins, pos, total)
                card = discord.File(png, filename="voice.png")
        except Exception as ex:
            print(f"[VOICE-CARD] {ex!r}")
    nxt = vc_need(lvl + 1) if lvl < VC_MAX_LEVEL else None
    ratio = 1.0 if nxt is None else (mins - (vc_need(lvl) if lvl else 0)) / max(1, nxt - (vc_need(lvl) if lvl else 0))
    e = E(f"🎙️ فويس {member.display_name}", color=0x00BEDC)
    e.add_field(name="🏅 لفل الفويس", value=f"`{lvl}`", inline=True)
    e.add_field(name="⏱️ الساعات", value=f"`{fmt_hours(mins)}`", inline=True)
    e.add_field(name="🥇 الترتيب (بالساعات)", value=f"`#{pos}` من {total}", inline=True)
    e.add_field(name="📈 للفل التالي",
                value=("🏆 وصلت أعلى لفل!" if nxt is None else f"{bar(ratio, 12, '🟦', '⬛')} باقي `{fmt_hours(nxt - mins)}`"),
                inline=False)
    e.set_thumbnail(url=member.display_avatar.url)
    if card:
        e.set_image(url="attachment://voice.png")
    return e, card

async def announce_voice_level(member, level):
    guild = member.guild
    ch = level_channel_for(guild)
    if ch is None:
        return
    mins = vc_minutes(guild, member.id)
    e = E("🎙️ ارتقاء فويس", f"{member.mention} وصل **لفل فويس {level}** 🎧\n⏱️ مجموع ساعاته: `{fmt_hours(mins)}`", 0x00BEDC)
    e.set_thumbnail(url=member.display_avatar.url)
    try:
        await ch.send(content=member.mention, embed=e)
    except discord.HTTPException as ex:
        print(f"[VOICE] announce failed: {ex!r}")

async def voice_tick(guild):
    """دقيقة فويس واحدة لكل عضو مؤهل بهذا السيرفر."""
    need = vc_min_humans(guild)
    for vc in guild.voice_channels:
        if vc == guild.afk_channel:
            continue
        humans = [m for m in vc.members if not m.bot]
        if len(humans) < need:
            continue
        for m in humans:
            try:
                if m.voice and (m.voice.self_deaf or m.voice.deaf):
                    continue
                CUR_GUILD.set(guild)
                before = vc_level_of(vc_minutes(guild, m.id))
                db.user(m.id)["voice_minutes"] += 1
                vc_add(guild, m.id, 1)
                after = vc_level_of(vc_minutes(guild, m.id))
                await grant_xp(m, VOICE_XP, None, boost=True)
                if after > before:
                    await announce_voice_level(m, after)
            except Exception as e:
                print(f"[VOICE] guild={guild.id} member={m.id}: {e!r}")

@bot.command(name="فويس", aliases=["ساعاتي", "vc", "voice"])
@commands.guild_only()
async def voice_card_command(ctx, member: discord.Member = None):
    member = member or ctx.author
    async with ctx.typing():
        e, card = await build_voice(member)
    if card:
        await ctx.send(file=card)
    else:
        await ctx.send(embed=e)

@bot.command(name="توب_فويس", aliases=["متصدرين_الفويس", "vtop", "ساعات"])
@commands.guild_only()
async def voice_top_command(ctx):
    rows = vc_entries(ctx.guild)[:10]
    medals = ["🥇", "🥈", "🥉"] + ["🔹"] * 7
    lines = [f"{medals[i]} **{i + 1}.** {m.mention} — ⏱️ `{fmt_hours(mins)}` • 🎙️ لفل `{vc_level_of(mins)}`"
             for i, (m, mins) in enumerate(rows)]
    e = E("🎙️ متصدرين الفويس — حسب الساعات", "\n".join(lines) or "ماكو أحد بالفويس بعد 🎧", 0x00BEDC)
    e.add_field(name="ℹ️ طريقة الحساب",
                value=f"الترتيب بعدد الساعات فقط. تُحسب الدقيقة إذا كنتم `{vc_min_humans(ctx.guild)}` أشخاص أو أكثر بالروم وبدون ديفن.",
                inline=False)
    await ctx.send(embed=e)

@bot.command(name="اعدادات_فويس")
@commands.guild_only()
@admin_only()
async def voice_settings_command(ctx, min_members: int = None):
    if min_members is None:
        return await ctx.send(embed=E("⚙️ إعدادات الفويس",
                                      f"أقل عدد أشخاص بالروم حتى تُحسب الساعات: `{vc_min_humans(ctx.guild)}`\n"
                                      "التغيير: `اعدادات_فويس 1` (1 = تُحسب حتى لو لوحدك)"))
    if not 1 <= min_members <= 10:
        return await ctx.reply("❌ اختر رقم من 1 إلى 10.")
    vc_cfg(ctx.guild)["min"] = min_members
    db.mark()
    await ctx.send(embed=E("✅ تم الحفظ", f"صارت الساعات تُحسب عند وجود `{min_members}` أشخاص أو أكثر بالروم."))

@bot.command(name="تعيين_ساعات")
@commands.guild_only()
@admin_only()
async def set_voice_hours_command(ctx, member: discord.Member, hours: float):
    if member.bot or not 0 <= hours <= 100000:
        return await ctx.reply("❌ الاستخدام: `تعيين_ساعات @العضو 12.5`")
    vc_set(ctx.guild, member.id, int(hours * 60))
    lvl = vc_level_of(vc_minutes(ctx.guild, member.id))
    await ctx.send(embed=E("✅ تم ضبط ساعات الفويس", f"{member.mention}: `{hours:g}` ساعة • لفل فويس `{lvl}`"))

HELP_SECTIONS["voice"] = ("🎙️", "نظام الفويس", "لفل خاص بالفويس يُحسب من الساعات فقط، مع ترتيب بالساعات.", [
    "🎧 للجميع",
    ("R", "R [@العضو]", "بروفايل كامل بصورة واحدة (لفل الكتابة + لفل الفويس + ترتيبك بالساعات)."),
    ("فويس", "فويس [@العضو]", "بطاقة الفويس فقط."),
    ("توب_فويس", "توب_فويس", "متصدرين الفويس مرتبين بعدد الساعات فقط."),
    "🛠️ للإدارة",
    ("اعدادات_فويس", "اعدادات_فويس [أقل_عدد]", "أقل عدد أشخاص بالروم حتى تُحسب الساعات (الافتراضي 2)."),
    ("تعيين_ساعات", "تعيين_ساعات @العضو 12.5", "يضبط ساعات الفويس لعضو (تصحيح يدوي)."),
])


# ───────────────────────── البروفايل والمستويات ─────────────────────────
async def build_profile(member, card_only=False):
    guild = member.guild
    u = db.user(member.id)
    lvl, xp = int(u["level"]), int(u["xp"])
    need = xp_needed(lvl)
    entries = leaderboard_entries(guild)
    pos = next((i for i, (m, _) in enumerate(entries, 1) if m.id == member.id), len(entries) + 1)
    entry = rank_entry(lvl, guild)
    title, color = rank_for(lvl, guild)
    warns = u["warnings"]
    vmin = vc_minutes(guild, member.id)
    vlvl = vc_level_of(vmin)
    vpos, vtotal = vc_rank_of(guild, member)
    if vlvl >= VC_MAX_LEVEL:
        vratio, vlabel = 1.0, "MAX LEVEL"
    else:
        vbase, vnext = vc_need(vlvl), vc_need(vlvl + 1)
        vratio = (vmin - vbase) / max(1, vnext - vbase)
        vleft = max(0, vnext - vmin)
        vlabel = f"{vleft // 60}h {vleft % 60}m to LV {vlvl + 1}"
    card = None
    if PIL_OK:
        try:
            av = await asset_bytes(member.display_avatar)
            if av:
                png = await asyncio.to_thread(
                    render_profile, av, member.display_name, lvl, xp, need, entry[2], entry[3],
                    pos, max(len(entries), pos), u["messages"], u["coins"], len(warns),
                    vlvl, vmin, vpos, vtotal, vratio, vlabel, brand(guild)[0])
                card = discord.File(png, filename="profile.png")
        except Exception as ex:
            print(f"[PROFILE] card failed: {ex!r}")
            card = None
    if card_only and card:
        return None, [card]
    e = discord.Embed(title=f"♛ {brand(guild)[0]} PROFILE | {member.display_name}", color=color, timestamp=discord.utils.utcnow())
    e.add_field(name="👑 الرتبة", value=title, inline=False)
    if lvl >= 5:
        e.add_field(name="🎖️ رتبة اللفل", value=f"✅ واصل **Level {min(100, lvl // 5 * 5)}**", inline=True)
    e.add_field(name="🏆 لفل الكتابة", value=f"`{lvl}`", inline=True)
    e.add_field(name="🥇 الترتيب", value=f"`#{pos}` من {len(entries)}", inline=True)
    e.add_field(name="✨ XP", value=f"`{xp:,}/{need:,}`", inline=True)
    e.add_field(name="🎙️ لفل الفويس", value=f"`{vlvl}` • `{fmt_hours(vmin)}` • ترتيب `#{vpos}` من {vtotal}", inline=False)
    e.add_field(name="💬 الرسائل", value=f"`{u['messages']:,}`", inline=True)
    e.add_field(name="💰 العملات", value=f"`{u['coins']:,}`", inline=True)
    last = warns[-1] if warns else None
    if last is None:
        wtxt = "`0` ✅"
    else:
        reason = last.get("reason", "مخالفة") if isinstance(last, dict) else str(last)
        wtxt = f"`{len(warns)}` ⚠️ — آخرها: {reason[:60]}"
    e.add_field(name="⚠️ التحذيرات", value=wtxt, inline=False)
    if member.joined_at:
        e.add_field(name="📅 انضم", value=discord.utils.format_dt(member.joined_at, "R"), inline=True)
    e.add_field(name="🕰️ الحساب", value=discord.utils.format_dt(member.created_at, "R"), inline=True)
    e.add_field(name="📈 التقدم", value=f"{bar(xp / need)} {int(xp / need * 100)}%", inline=False)
    e.set_footer(text=footer_text(guild))
    if card:
        e.set_image(url="attachment://profile.png")
        gf = attach_media(e, "profile", rank_media_key(lvl, guild), thumb=True)
    else:
        e.set_thumbnail(url=member.display_avatar.url)
        gf = attach_media(e, "profile", rank_media_key(lvl, guild))
    return e, files_of(card, gf)

@bot.command(name="R", aliases=["بروفايل", "ملفي"])
@commands.guild_only()
async def profile_command(ctx, member: discord.Member = None):
    member = member or ctx.author
    async with ctx.typing():
        e, files = await build_profile(member, card_only=True)
    if e is None:
        # صورة واحدة فقط فيها كل شي: لفل الكتابة + لفل الفويس + الإحصائيات
        return await ctx.send(files=files)
    await ctx.send(embed=e, files=files)

@bot.command(name="مستويات")
@commands.guild_only()
async def levels_command(ctx):
    u = db.user(ctx.author.id)
    lvl = u["level"]
    e = E("♛ رتب ومستويات المملكة", f"مستواك الحالي: **{lvl}** • XP: `{u['xp']:,}/{xp_needed(lvl):,}`\n"
          + (f"كل **5 لفلات** تحصل رتبة جديدة `{milestone_name('N', ctx.guild)}`." if milestones_on(ctx.guild) else ""))
    if not guild_ranks(ctx.guild):
        e.add_field(name="🎖️ رتب اللفلات", value="ما في رتب لفلات بعد. الإدارة تسوّيها بأمر `انشاء_رتب_لفل`.", inline=False)
    for l, title, en, cols, desc in guild_ranks(ctx.guild)[:24]:
        mark = "✅" if lvl >= l else "🔒"
        e.add_field(name=f"{mark} LEVEL {l} — {en}", value=f"{title}\n{desc}", inline=False)
    f = attach_media(e, "leaderboard")
    await ctx.send(embed=e, files=files_of(f))

@bot.command(name="المتصدرين", aliases=["توب", "top"])
@commands.guild_only()
async def leaderboard_command(ctx, kind: str = "لفل"):
    key = "coins" if kind in ("عملات", "coins", "فلوس") else "level"
    rows = leaderboard_entries(ctx.guild, key)[:10]
    medals = ["🥇", "🥈", "🥉"] + ["🔹"] * 7
    lines = []
    for i, (m, u) in enumerate(rows):
        val = f"💰 `{u['coins']:,}`" if key == "coins" else f"LEVEL `{u['level']}` • XP `{u['xp']:,}`"
        lines.append(f"{medals[i]} **{i + 1}.** {m.mention} — {val}")
    e = E("🏆 المتصدرين — " + ("الأغنياء" if key == "coins" else "اللفلات"), "\n".join(lines) or "ماكو بيانات بعد.")
    f = attach_media(e, "leaderboard")
    await ctx.send(embed=e, files=files_of(f))

@bot.command(name="رصيد")
@commands.guild_only()
async def balance_command(ctx, member: discord.Member = None):
    member = member or ctx.author
    u = db.user(member.id)
    await ctx.send(embed=E("💰 المحفظة", f"{member.mention}\nالرصيد: **{u['coins']:,}** عملة"))

@bot.command(name="راتب", aliases=["يومي"])
@commands.guild_only()
async def daily_command(ctx):
    u = db.user(ctx.author.id)
    left = 20 * 3600 - (time.time() - u["last_daily"])
    if left > 0:
        return await ctx.reply(f"⏳ راتبك الجاي بعد **{int(left // 3600)}س {int(left % 3600 // 60)}د**.")
    amount = DAILY_COINS + min(u["level"], 100) * 5
    u["coins"] += amount
    u["last_daily"] = time.time()
    db.mark()
    e = E("💰 الراتب الملكي", f"استلمت **{amount:,}** عملة 👑\nرصيدك: `{u['coins']:,}`")
    f = attach_media(e, "daily")
    await ctx.send(embed=e, files=files_of(f))

@bot.command(name="تحويل")
@commands.guild_only()
async def transfer_command(ctx, member: discord.Member, amount: int):
    if member.bot or member.id == ctx.author.id:
        return await ctx.reply("❌ ما تگدر تحول لهذا الشخص.")
    u = db.user(ctx.author.id)
    if amount <= 0 or amount > u["coins"]:
        return await ctx.reply("❌ المبلغ غير صحيح أو رصيدك ما يكفي.")
    u["coins"] -= amount
    db.user(member.id)["coins"] += amount
    db.mark()
    await ctx.send(embed=E("💸 تحويل ناجح", f"{ctx.author.mention} ➜ {member.mention}\nالمبلغ: **{amount:,}** عملة"))

@bot.command(name="افتار", aliases=["avatar"])
@commands.guild_only()
async def avatar_command(ctx, member: discord.Member = None):
    member = member or ctx.author
    e = E(f"🖼️ {member.display_name}", color=PURPLE)
    e.set_image(url=member.display_avatar.url)
    await ctx.send(embed=e)

@bot.command(name="سيرفر", aliases=["server"])
@commands.guild_only()
async def server_command(ctx):
    g = ctx.guild
    e = E(f"👑 {g.name}", color=PURPLE)
    if g.icon:
        e.set_thumbnail(url=g.icon.url)
    e.add_field(name="👥 الأعضاء", value=f"`{g.member_count:,}`", inline=True)
    e.add_field(name="💬 الرومات", value=f"`{len(g.text_channels)}` كتابي • `{len(g.voice_channels)}` صوتي", inline=True)
    e.add_field(name="🎭 الرتب", value=f"`{len(g.roles)}`", inline=True)
    e.add_field(name="🚀 البوست", value=f"لفل `{g.premium_tier}` • `{g.premium_subscription_count}`", inline=True)
    e.add_field(name="📅 الإنشاء", value=discord.utils.format_dt(g.created_at, "D"), inline=True)
    e.add_field(name="👑 الأونر", value=f"<@{g.owner_id}>", inline=True)
    await ctx.send(embed=e)

@bot.command(name="الوان", aliases=["ألوان"])
@commands.guild_only()
async def colors_command(ctx):
    e, f = color_panel_embed()
    await ctx.send(embed=e, view=ColorView(), files=files_of(f))

@bot.command(name="لون")
@commands.guild_only()
async def color_number(ctx, number: int):
    key = str(number)
    if key not in COLOR_PALETTE:
        return await ctx.reply("اختار رقم من 1 إلى 50، أو اكتب `!الوان`.")
    role = await color_role(ctx.guild, key)
    if role is None:
        return await ctx.reply("تعذر إنشاء رتبة اللون.")
    if ctx.guild.me and role.position >= ctx.guild.me.top_role.position:
        return await ctx.reply("رتبة البوت لازم تكون أعلى من رتبة اللون.")
    old = [r for r in ctx.author.roles if r.name.startswith("Color-") and r != role]
    try:
        if old:
            await ctx.author.remove_roles(*old)
        if role not in ctx.author.roles:
            await ctx.author.add_roles(role)
        await ctx.reply(f"✨ تم تطبيق اللون **{COLOR_PALETTE[key][0]}**.")
    except discord.HTTPException:
        await ctx.reply("تعذر تطبيق اللون.")

@bot.command(name="الغاء_لون", aliases=["إلغاء_لون", "الغاء_الوان"])
@commands.guild_only()
async def clear_color_cmd(ctx):
    old = [r for r in ctx.author.roles if r.name.startswith("Color-")]
    if not old:
        return await ctx.reply("ما عندك لون.")
    try:
        await ctx.author.remove_roles(*old)
        await ctx.reply("🧹 تم إلغاء لونك.")
    except discord.HTTPException:
        await ctx.reply("تعذر إلغاء اللون.")

# ───────────────────────── الإدارة ─────────────────────────
def mod_embed(title, desc, color, media, member=None):
    e = E(title, desc, color)
    if member is not None:
        e.set_thumbnail(url=member.display_avatar.url)
    f = attach_media(e, media)
    return e, f

@bot.command(name="مسح")
@commands.guild_only()
@staff_perms(manage_messages=True)
async def clear_messages(ctx, amount: int = 10):
    amount = max(1, min(amount, 100))
    deleted = await ctx.channel.purge(limit=amount + 1)
    e, f = mod_embed("🧹 تنظيف", f"تم حذف **{max(0, len(deleted) - 1)}** رسالة بواسطة {ctx.author.mention}", 0x3498DB, "clear")
    await ctx.send(embed=e, files=files_of(f), delete_after=6)

@bot.command(name="قفل")
@commands.guild_only()
@staff_perms(manage_channels=True)
async def lock_channel(ctx):
    ow = ctx.channel.overwrites_for(ctx.guild.default_role)
    ow.send_messages = False
    await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=ow)
    e, f = mod_embed("🔒 تم قفل الروم", f"بواسطة {ctx.author.mention}", 0xE74C3C, "lock")
    await ctx.send(embed=e, files=files_of(f))

@bot.command(name="فتح")
@commands.guild_only()
@staff_perms(manage_channels=True)
async def unlock_channel(ctx):
    ow = ctx.channel.overwrites_for(ctx.guild.default_role)
    ow.send_messages = None
    await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=ow)
    e, f = mod_embed("🔓 تم فتح الروم", f"بواسطة {ctx.author.mention}", 0x2ECC71, "unlock")
    await ctx.send(embed=e, files=files_of(f))

@bot.command(name="بطيء")
@commands.guild_only()
@staff_perms(manage_channels=True)
async def slowmode(ctx, seconds: int = 0):
    seconds = max(0, min(seconds, 21600))
    await ctx.channel.edit(slowmode_delay=seconds)
    await ctx.send(f"🐢 الوضع البطيء: **{seconds}** ثانية." if seconds else "⚡ تم إلغاء الوضع البطيء.")

@bot.command(name="طرد")
@commands.guild_only()
@staff_perms(kick_members=True)
async def kick_member(ctx, member: discord.Member, *, reason="بدون سبب"):
    if not target_is_manageable(ctx, member):
        return await ctx.reply("❌ ما تگدر تطرد عضو أعلى منك أو مساوي إلك.")
    dm = await dm_notice(member, f"👢 تم طردك من {ctx.guild.name}",
                         f"📌 **السبب:** {reason}\n👮 **بواسطة:** {ctx.author}\n\nيمكنك العودة بدعوة جديدة مع الالتزام بالقوانين.", 0xE67E22)
    await member.kick(reason=f"{ctx.author}: {reason}")
    e, f = mod_embed("👢 تم الطرد", f"`{member}`\nالسبب: {reason}\nبواسطة {ctx.author.mention}\n{'📩 أُرسل إشعار للخاص' if dm else '📪 الخاص مغلق'}", 0xE67E22, "kick", member)
    await ctx.send(embed=e, files=files_of(f))

@bot.command(name="حظر")
@commands.guild_only()
@staff_perms(ban_members=True)
async def ban_member(ctx, member: discord.Member, *, reason="بدون سبب"):
    if not target_is_manageable(ctx, member):
        return await ctx.reply("❌ ما تگدر تحظر عضو أعلى منك أو مساوي إلك.")
    dm = await dm_notice(member, f"🔨 تم حظرك من {ctx.guild.name}",
                         f"تم **حظرك نهائياً** من سيرفر **{ctx.guild.name}**.\n\n"
                         f"📌 **السبب:** {reason}\n👮 **بواسطة:** {ctx.author}\n\n"
                         f"⚠️ **تحذير رسمي:** هذا القرار صادر عن إدارة السيرفر، ومحاولة الالتفاف عليه بحساب آخر "
                         f"تعرّضك لحظر دائم من جديد. للاعتراض تواصل مع الإدارة.", 0xE74C3C)
    await member.ban(reason=f"{ctx.author}: {reason}")
    e, f = mod_embed("🔨 تم الحظر", f"`{member}`\nالسبب: {reason}\nبواسطة {ctx.author.mention}\n{'📩 أُرسلت رسالة للخاص' if dm else '📪 الخاص مغلق'}", 0xE74C3C, "ban", member)
    await ctx.send(embed=e, files=files_of(f))

@bot.command(name="رفع_حظر", aliases=["فك_حظر"])
@commands.guild_only()
@staff_perms(ban_members=True)
async def unban_member(ctx, user_id: int):
    try:
        await ctx.guild.unban(discord.Object(id=user_id), reason=f"بواسطة {ctx.author}")
        await ctx.send(f"🕊️ تم فك الحظر عن `{user_id}`.")
    except discord.NotFound:
        await ctx.reply("❌ هذا الشخص مو محظور.")

@bot.command(name="ميوت")
@commands.guild_only()
@staff_perms(moderate_members=True)
async def mute_member(ctx, member: discord.Member, minutes: int = 10, *, reason="بدون سبب"):
    if not 1 <= minutes <= 40320:
        return await ctx.reply("المدة من 1 دقيقة إلى 28 يوم.")
    if not target_is_manageable(ctx, member):
        return await ctx.reply("❌ ما تگدر تسكت عضو أعلى منك أو مساوي إلك.")
    await member.timeout(discord.utils.utcnow() + timedelta(minutes=minutes), reason=f"{ctx.author}: {reason}")
    await dm_notice(member, f"🔇 تم إسكاتك في {ctx.guild.name}",
                    f"⏱️ **المدة:** {minutes} دقيقة\n📌 **السبب:** {reason}\n👮 **بواسطة:** {ctx.author}\n\n"
                    f"🚫 خلال هذه المدة لا يمكنك إرسال الرسائل أو التحدث في الرومات الصوتية.", 0x95A5A6)
    e, f = mod_embed("🔇 تم الإسكات", f"{member.mention} لمدة **{minutes}** دقيقة\nالسبب: {reason}", 0x95A5A6, "mute", member)
    await ctx.send(embed=e, files=files_of(f))

@bot.command(name="انهض")
@commands.guild_only()
@staff_perms(moderate_members=True)
async def unmute_member(ctx, member: discord.Member):
    if not target_is_manageable(ctx, member):
        return await ctx.reply("❌ ما تگدر تفك إسكات عضو أعلى منك أو مساوي إلك.")
    await member.timeout(None, reason=f"فك الإسكات بواسطة {ctx.author}")
    e, f = mod_embed("🔊 فك الإسكات", f"{member.mention} رجع يحچي 🎙️", 0x2ECC71, "unmute", member)
    await ctx.send(embed=e, files=files_of(f))

@bot.command(name="تحذير")
@commands.guild_only()
@staff_perms(moderate_members=True)
async def warn_member(ctx, member: discord.Member, *, reason="مخالفة"):
    u = db.user(member.id)
    u["warnings"].append({"reason": reason[:500], "by": str(ctx.author), "by_id": ctx.author.id,
                          "at": discord.utils.utcnow().isoformat()})
    db.mark()
    n = len(u["warnings"])
    await dm_notice(member, f"⚠️ تحذير في {ctx.guild.name}", f"📌 **السبب:** {reason}\n🔢 مجموع تحذيراتك: **{n}**", 0xE67E22)
    extra = ""
    if n in (3, 5) and target_is_manageable(ctx, member):
        mins = 60 if n == 3 else 1440
        try:
            await member.timeout(discord.utils.utcnow() + timedelta(minutes=mins), reason=f"{n} تحذيرات")
            extra = f"\n🔇 **عقوبة تلقائية:** إسكات {mins // 60} ساعة (وصل {n} تحذيرات)"
        except discord.HTTPException:
            pass
    e, f = mod_embed("⚠️ تحذير", f"{member.mention}\nالسبب: {reason}\nعدد التحذيرات: **{n}**{extra}", 0xE67E22, "warn", member)
    await ctx.send(embed=e, files=files_of(f))
    await log_event(ctx.guild, "⚠️ تحذير", f"{member.mention} بواسطة {ctx.author.mention}", "orange",
                    [("السبب", reason, False), ("المجموع", n, True)], thumb=member.display_avatar.url)

@bot.command(name="تحذيرات")
@commands.guild_only()
async def warnings_command(ctx, member: discord.Member = None):
    member = member or ctx.author
    if member != ctx.author and not ctx.author.guild_permissions.moderate_members:
        return await ctx.reply("❌ تحتاج صلاحية Moderate Members.")
    u = db.user(member.id)
    lines = []
    for i, item in enumerate(u["warnings"][-15:], 1):
        if isinstance(item, dict):
            try:
                ts = int(datetime.fromisoformat(item["at"]).timestamp())
                when = f"<t:{ts}:R>"
            except (KeyError, ValueError):
                when = ""
            lines.append(f"**{i}.** {item.get('reason', 'مخالفة')} — `{item.get('by', 'غير معروف')}` {when}")
        else:
            lines.append(f"**{i}.** {item}")
    e = E(f"📋 تحذيرات {member.display_name}", "\n".join(lines)[:4000] or "لا توجد تحذيرات ✅", 0xFF8C00)
    e.set_thumbnail(url=member.display_avatar.url)
    e.add_field(name="المجموع", value=f"`{len(u['warnings'])}`")
    await ctx.send(embed=e)

@bot.command(name="عفو")
@commands.guild_only()
@staff_perms(moderate_members=True)
async def pardon_warnings(ctx, member: discord.Member):
    db.user(member.id)["warnings"] = []
    db.mark()
    e, f = mod_embed("🕊️ عفو ملكي", f"تم مسح تحذيرات {member.mention}", 0x2ECC71, "pardon", member)
    await ctx.send(embed=e, files=files_of(f))
    await log_event(ctx.guild, "🕊️ عفو", f"{ctx.author.mention} مسح تحذيرات {member.mention}", "green")

@bot.command(name="اعطاء")
@commands.guild_only()
@staff_perms(manage_roles=True)
async def give_role(ctx, member: discord.Member, *, role: discord.Role):
    if ctx.author.id != ctx.guild.owner_id and role >= ctx.author.top_role:
        return await ctx.reply("❌ الرتبة أعلى من رتبتك أو مساوية.")
    if ctx.guild.me and role >= ctx.guild.me.top_role:
        return await ctx.reply("❌ رتبة البوت لازم تكون أعلى من الرتبة المطلوبة.")
    await member.add_roles(role, reason=f"منح بواسطة {ctx.author}")
    await ctx.send(f"👑 تم إعطاء {role.mention} إلى {member.mention}.")
    await log_event(ctx.guild, "🎭 منح رتبة", f"{ctx.author.mention} → {role.mention} → {member.mention}", "blue")

@bot.command(name="سحب")
@commands.guild_only()
@staff_perms(manage_roles=True)
async def remove_role(ctx, member: discord.Member, *, role: discord.Role):
    if ctx.author.id != ctx.guild.owner_id and role >= ctx.author.top_role:
        return await ctx.reply("❌ الرتبة أعلى من رتبتك أو مساوية.")
    if ctx.guild.me and role >= ctx.guild.me.top_role:
        return await ctx.reply("❌ رتبة البوت لازم تكون أعلى من الرتبة المطلوبة.")
    await member.remove_roles(role, reason=f"سحب بواسطة {ctx.author}")
    await ctx.send(f"🛡️ تم سحب {role.mention} من {member.mention}.")
    await log_event(ctx.guild, "🎭 سحب رتبة", f"{ctx.author.mention} ← {role.mention} ← {member.mention}", "blue")

@bot.command(name="انشاء_رتبة", aliases=["انشاء_رتبه"])
@commands.guild_only()
@staff_perms(manage_roles=True)
async def create_role_cmd(ctx, *, name: str):
    name = name.strip()
    if not name or len(name) > 100:
        return await ctx.reply("اسم الرتبة من 1 إلى 100 حرف.")
    role = await ctx.guild.create_role(name=name, reason=f"إنشاء بواسطة {ctx.author}")
    await ctx.send(f"✨ تم إنشاء الرتبة {role.mention}.")

HEX_RE = re.compile(r"^(0x|#)?[0-9a-fA-F]{6}$")

def parse_hex(tok):
    return int(tok.lower().removeprefix("0x").removeprefix("#"), 16)

async def shrink_icon(data):
    if len(data) <= 250_000:
        return data
    if not PIL_OK:
        return None
    def work():
        im = Image.open(io.BytesIO(data)).convert("RGBA").resize((128, 128), Image.LANCZOS)
        out = io.BytesIO()
        im.save(out, "PNG", optimize=True)
        return out.getvalue()
    try:
        out = await asyncio.to_thread(work)
        return out if len(out) <= 250_000 else None
    except Exception:
        return None

@bot.command(name="اصنع")
@commands.guild_only()
@admin_only()
async def make_custom_role(ctx, *, args=""):
    parts = args.split()
    att = ctx.message.attachments[0] if ctx.message.attachments else None
    url = None
    if parts and urlparse(parts[-1]).scheme in ("http", "https"):
        url = parts.pop()
    cols = []
    while parts and HEX_RE.match(parts[-1]) and len(cols) < 2:
        cols.insert(0, parse_hex(parts.pop()))
    name = " ".join(parts).strip()
    if not name or not cols:
        return await ctx.reply("الاستخدام: `!اصنع اسم الرتبة 0xFFD700 [0x1E90FF] https://رابط_الصورة.png`")
    if discord.utils.get(ctx.guild.roles, name=name):
        return await ctx.reply("هذه الرتبة موجودة مسبقاً.")
    img = None
    if att:
        img = await att.read()
    elif url:
        img = await fetch_bytes(url)
    icon_note = ""
    c1 = cols[0]
    c2 = cols[1] if len(cols) > 1 else None
    role = await make_role(ctx.guild, name, c1, c2, reason=f"Custom role by {ctx.author}")
    if role is None:
        return await ctx.reply("تعذر إنشاء الرتبة.")
    if img and sniff_ext(img):
        if "ROLE_ICONS" in ctx.guild.features:
            icon = await shrink_icon(img)
            if icon is None:
                icon_note = "\n⚠️ الصورة كبيرة جداً للأيقونة."
            else:
                try:
                    await role.edit(display_icon=icon)
                    icon_note = "\n🖼️ تم وضع الصورة كأيقونة للرتبة."
                except (discord.HTTPException, TypeError):
                    icon_note = "\n⚠️ فشل وضع الأيقونة."
        else:
            icon_note = "\n⚠️ أيقونات الرتب تحتاج **بوست لفل 2** بالسيرفر."
    e = E("✨ تم إنشاء الرتبة", f"{role.mention}\nاللون: `#{c1:06X}`" + (f" ➜ `#{c2:06X}`" if c2 is not None else "") + icon_note, c1)
    f = None
    if img and sniff_ext(img):
        ext = sniff_ext(img)
        e.set_thumbnail(url=f"attachment://role{ext}")
        f = discord.File(io.BytesIO(img), filename=f"role{ext}")
    await ctx.send(embed=e, files=files_of(f))

@bot.command(name="لفل")
@commands.guild_only()
@admin_only()
async def set_level(ctx, member: discord.Member, level: int):
    if not 1 <= level <= MAX_LEVEL:
        return await ctx.reply(f"حدد مستوى من 1 إلى {MAX_LEVEL}.")
    u = db.user(member.id)
    u["level"], u["xp"] = level, 0
    db.mark()
    await update_rank_role(ctx.guild, member, level)
    title, _ = rank_for(level, ctx.guild)
    await ctx.send(f"✅ تم تعديل مستوى {member.mention} إلى **{level}** — {title}")

@bot.command(name="خصم")
@commands.guild_only()
@admin_only()
async def deduct_level(ctx, member: discord.Member, amount: int):
    u = db.user(member.id)
    u["level"] = max(1, int(u["level"]) - amount)
    u["xp"] = 0
    db.mark()
    await update_rank_role(ctx.guild, member, u["level"])
    title, _ = rank_for(u["level"], ctx.guild)
    await ctx.send(f"⚠️ مستوى {member.mention} صار **{u['level']}** — {title}")

@bot.command(name="عملات")
@commands.guild_only()
@admin_only()
async def give_coins(ctx, member: discord.Member, amount: int):
    u = db.user(member.id)
    u["coins"] = max(0, u["coins"] + amount)
    db.mark()
    await ctx.send(f"💰 رصيد {member.mention} صار **{u['coins']:,}**.")

# ───────────────────────── إدارة الـ XP واللفلات ─────────────────────────
async def remove_xp(member, amount):
    u = db.user(member.id)
    u["xp"] -= amount
    while u["xp"] < 0 and u["level"] > 1:
        u["level"] -= 1
        u["xp"] += xp_needed(u["level"])
    u["xp"] = max(0, u["xp"])
    db.mark()
    await update_rank_role(member.guild, member, u["level"])

async def apply_xp_change(ctx, member, amount):
    if member.bot:
        return await ctx.reply("❌ ما أقدر أتعامل مع XP بوت.")
    if amount == 0 or abs(amount) > 10_000_000:
        return await ctx.reply("❌ اكتب مبلغ صحيح. مثال: `اكس_بي @عضو 500`")
    before = db.user(member.id)["level"]
    if amount > 0:
        await grant_xp(member, amount, ctx.channel)
        verb, color = f"➕ تم إعطاء **{amount:,}** XP إلى", 0x2ECC71
    else:
        await remove_xp(member, -amount)
        verb, color = f"➖ تم خصم **{-amount:,}** XP من", 0xE67E22
    u = db.user(member.id)
    lvl, need = u["level"], xp_needed(u["level"])
    e = E("⚡ إدارة الـ XP", f"{verb} {member.mention}", color)
    e.add_field(name="🏆 اللفل", value=(f"`{before}` ➜ `{lvl}`" if before != lvl else f"`{lvl}`"), inline=True)
    e.add_field(name="✨ XP", value=f"`{u['xp']:,}/{need:,}`", inline=True)
    e.add_field(name="📈 التقدم", value=f"{bar(u['xp'] / need)} {int(u['xp'] / need * 100)}%", inline=False)
    e.set_thumbnail(url=member.display_avatar.url)
    await ctx.send(embed=e)

@bot.command(name="اكس_بي", aliases=["اكسبي", "xp", "اعطاء_اكس_بي", "اضافة_اكس_بي"])
@commands.guild_only()
@admin_only()
async def xp_give_cmd(ctx, member: discord.Member, amount: int):
    await apply_xp_change(ctx, member, abs(amount))

@bot.command(name="ازالة_اكس_بي", aliases=["خصم_اكس_بي", "سحب_اكس_بي"])
@commands.guild_only()
@admin_only()
async def xp_take_cmd(ctx, member: discord.Member, amount: int):
    await apply_xp_change(ctx, member, -abs(amount))

@bot.command(name="مضاعف_اكس_بي", aliases=["مضاعف_xp", "حدث_اكس_بي"])
@commands.guild_only()
@admin_only()
async def xp_boost_cmd(ctx, multiplier: float = None, minutes: int = 60):
    c = db.cfg(ctx.guild.id)
    if multiplier is None:
        m = xp_mult(ctx.guild)
        if m == 1.0:
            return await ctx.send(embed=E("🔥 مضاعف الـ XP", "ماكو مضاعف شغال حالياً.\n"
                                          "**الاستخدام:** `مضاعف_اكس_بي 2 60` = ضعف الـ XP لمدة 60 دقيقة.", PURPLE))
        left = max(0, int((float(c["xp_mult_until"]) - time.time()) / 60))
        return await ctx.send(embed=E("🔥 مضاعف الـ XP", f"شغّال الآن: **x{m:g}** — متبقي نحو **{left}** دقيقة.", GOLD))
    if not 1.0 < multiplier <= 10 or not 1 <= minutes <= 10080:
        return await ctx.reply("❌ المضاعف من 1.1 إلى 10 والمدة من 1 إلى 10080 دقيقة (أسبوع).")
    c["xp_mult"], c["xp_mult_until"] = multiplier, time.time() + minutes * 60
    db.mark()
    e = E("🔥 حدث XP مضاعف!", f"كل رسالة وفويس تعطي **x{multiplier:g}** XP لمدة **{minutes}** دقيقة 🚀\nيلا تفاعلوا!", GOLD)
    await ctx.send(embed=e)

@bot.command(name="ايقاف_المضاعف", aliases=["الغاء_المضاعف"])
@commands.guild_only()
@admin_only()
async def xp_boost_off(ctx):
    c = db.cfg(ctx.guild.id)
    c.pop("xp_mult", None)
    c.pop("xp_mult_until", None)
    db.mark()
    await ctx.send("🛑 تم إيقاف مضاعف الـ XP.")

@bot.command(name="رسالة_لفل", aliases=["رسالة_اللفل", "نص_لفل"])
@commands.guild_only()
@admin_only()
async def lvl_msg_cmd(ctx, *, text: str = ""):
    c = db.cfg(ctx.guild.id)
    t = text.strip()
    if not t:
        vars_txt = "\n".join(f"`{k}` — {v}" for k, v in LVL_VARS.items())
        return await ctx.send(embed=E("💬 رسالة تهنئة اللفل",
            f"**الحالية:**\n{c.get('lvl_msg') or DEFAULT_LVL_MSG}\n\n**المتغيرات:**\n{vars_txt}\n\n"
            "✏️ **تعديل:** `رسالة_لفل نصك هنا`\n♻️ **رجوع للافتراضي:** `رسالة_لفل حذف`\n🧪 **تجربة:** `تجربة_لفل`", PURPLE))
    if t in OFF_SET:
        c.pop("lvl_msg", None)
        db.mark()
        return await ctx.send("♻️ رجعت رسالة اللفل للافتراضية.")
    c["lvl_msg"] = t[:1500]
    db.mark()
    await ctx.send("✅ انحفظت الرسالة. جرّبها بـ `تجربة_لفل`")

@bot.command(name="تجربة_لفل", aliases=["تجربة_اللفل", "تست_لفل"])
@commands.guild_only()
@admin_only()
async def lvl_test_cmd(ctx, member: discord.Member = None, level: int = None):
    member = member or ctx.author
    level = max(2, min(MAX_LEVEL, level or db.user(member.id)["level"] + 1))
    e, f = build_levelup(member, level, level - 1)
    await ctx.send(content="🧪 **تجربة فقط** — ما تغيّر شي بمستوى أحد:", embed=e, files=files_of(f))
    real = level_channel_for(ctx.guild, ctx.channel)
    configured = get_channel(ctx.guild, "level_channel", LEVEL_NAMES)
    note = (f"✅ التهاني الحقيقية تنرسل إلى {real.mention}" if configured and real == configured
            else f"⚠️ روم اللفلات غير مضبوط/غير صالح — حالياً تنرسل إلى {real.mention if real else 'لا مكان'}. اضبطه: `ضبط لفل #روم`")
    await ctx.send(note)

@bot.command(name="فحص_اللفل", aliases=["فحص_لفل", "حالة_اللفل"])
@commands.guild_only()
@admin_only()
async def lvl_check_cmd(ctx):
    g, me = ctx.guild, ctx.guild.me
    ok = lambda v: "✅" if v else "❌"
    rows = []
    ch = get_channel(g, "level_channel", LEVEL_NAMES)
    if ch:
        p = ch.permissions_for(me)
        rows.append(f"{ok(p.send_messages and p.embed_links)} روم اللفلات: {ch.mention} — إرسال {ok(p.send_messages)} • إمبيد {ok(p.embed_links)} • ملفات {ok(p.attach_files)}")
    else:
        rows.append("⚠️ روم اللفلات **غير مضبوط** — التهاني تنرسل بنفس روم الكتابة. اضبطه: `ضبط لفل #روم`")
    rows.append(f"{ok(me.guild_permissions.manage_roles)} صلاحية Manage Roles (لإعطاء رتب اللفل)")
    above = [r for r in g.roles if r.name in level_role_names(g) and r.position >= me.top_role.position]
    rows.append(f"{ok(not above)} رتبة البوت أعلى من رتب اللفلات" + (f" — **{len(above)}** رتبة أعلى منه" if above else ""))
    rows.append(f"⚙️ XP لكل رسالة: `{XP_MIN}-{XP_MAX}` كل `{XP_COOLDOWN}` ثانية • مضاعف: `x{xp_mult(g):g}`")
    u = db.user(ctx.author.id)
    need = xp_needed(u["level"])
    msgs = math.ceil(max(0, need - u["xp"]) / ((XP_MIN + XP_MAX) / 2))
    rows.append(f"📊 مستواك: `{u['level']}` — `{u['xp']:,}/{need:,}` XP (تقريباً `{msgs}` رسالة للّفل التالي)")
    rows.append("ℹ️ تأكد أن **Message Content Intent** و **Server Members Intent** شغّالة من Developer Portal.")
    await ctx.send(embed=E("🩺 فحص نظام اللفلات", "\n".join(rows), PURPLE))

@bot.command(name="طوارئ")
@commands.guild_only()
@admin_only()
async def emergency(ctx):
    count = 0
    for ch in ctx.guild.text_channels:
        try:
            ow = ch.overwrites_for(ctx.guild.default_role)
            ow.send_messages = False
            await ch.set_permissions(ctx.guild.default_role, overwrite=ow, reason=f"Emergency by {ctx.author}")
            count += 1
        except discord.HTTPException:
            pass
    e, f = mod_embed("🚨 طوارئ", f"تم قفل **{count}** روم بواسطة {ctx.author.mention}", 0xE74C3C, "emergency")
    await ctx.send(embed=e, files=files_of(f))
    await log_event(ctx.guild, "🚨 طوارئ", f"فعّل {ctx.author.mention} قفل الطوارئ.", "red")

@bot.command(name="استقرار")
@commands.guild_only()
@admin_only()
async def stability(ctx):
    count = 0
    for ch in ctx.guild.text_channels:
        try:
            ow = ch.overwrites_for(ctx.guild.default_role)
            ow.send_messages = None
            await ch.set_permissions(ctx.guild.default_role, overwrite=ow, reason=f"Restore by {ctx.author}")
            count += 1
        except discord.HTTPException:
            pass
    e, f = mod_embed("🛡️ استقرار", f"تمت إعادة الكتابة الافتراضية في **{count}** روم.", 0x2ECC71, "calm")
    await ctx.send(embed=e, files=files_of(f))
    await log_event(ctx.guild, "🛡️ استقرار", f"أعاد {ctx.author.mention} الإعدادات.", "green")

# ───────────────────────── الإعلان (خط + صورتين لكل سيرفر + منشن مخفي) ─────────────────────────
ANN_SLOTS = {
    "line": ("ann_line", "الخط"),
    "main": ("ann_main", "الصورة الرئيسية (السوداء)"),
    "side": ("ann_side", "الصورة الجانبية (الحمراء)"),
}

def gkey(guild, slot):
    """مفتاح صورة خاص بالسيرفر حتى لا تتداخل السيرفرات."""
    return f"g{guild.id}_{ANN_SLOTS[slot][0]}"

def has_gmedia(guild, slot):
    k = gkey(guild, slot)
    return k in MEDIA_CACHE or k in db.data["_media"]

def gmedia_file(guild, slot):
    entry = MEDIA_CACHE.get(gkey(guild, slot))
    return discord.File(io.BytesIO(entry[0]), filename=entry[1]) if entry else None

async def send_line(channel, guild):
    """يرسل الخط (صورة/GIF) الخاص بالسيرفر. يرجع True إذا انرسل."""
    f = gmedia_file(guild, "line")
    try:
        if f:
            await channel.send(file=f)
            return True
        url = db.data["_media"].get(gkey(guild, "line"))
        if url:
            await channel.send(url)
            return True
    except discord.HTTPException:
        pass
    return False

async def set_guild_media(ctx, slot, url):
    key, label = gkey(ctx.guild, slot), ANN_SLOTS[slot][1]
    if url and url.lower() in ("حذف", "delete", "ازالة", "إزالة"):
        media_remove(key)
        return await ctx.send(embed=E("🗑️ تم الحذف", f"تم حذف **{label}** لهذا السيرفر."))
    att = ctx.message.attachments[0] if ctx.message.attachments else None
    if att:
        data, src = await att.read(), None
    elif url and urlparse(url).scheme in ("http", "https"):
        data, src = await fetch_bytes(url), url
    else:
        cur = "✅ مضبوطة" if has_gmedia(ctx.guild, slot) else "❌ غير مضبوطة"
        return await ctx.reply(f"الحالة: {cur}\nالاستخدام: ضع **رابط مباشر** (صورة أو GIF) بعد الأمر، أو أرفق الملف، أو اكتب `حذف`.")
    if not data or not media_install(key, data):
        return await ctx.reply("❌ رابط غير صالح أو صيغة غير مدعومة (GIF / PNG / JPG / WEBP).")
    if src:
        db.data["_media"][key] = src
    else:
        db.data["_media"].pop(key, None)
    db.mark()
    e = E(f"✅ تم ضبط {label}", "هذا الإعداد خاص بهذا السيرفر فقط.")
    f = attach_media(e, key)
    await ctx.send(embed=e, files=files_of(f))

@bot.command(name="تعيين_خط", aliases=["تغير_خط", "تغيير_خط", "تعيين_الخط", "تغيير_الخط", "تغير_الخط"])
@commands.guild_only()
@admin_only()
async def set_line_cmd(ctx, url: str = None):
    await set_guild_media(ctx, "line", url)

@bot.command(name="خط")
@commands.guild_only()
@admin_only()
async def line_cmd(ctx):
    try:
        await ctx.message.delete()
    except discord.HTTPException:
        pass
    if not await send_line(ctx.channel, ctx.guild):
        await ctx.send("⚠️ ما في خط مضبوط. استخدم `تعيين_خط رابط_الصورة`.", delete_after=8)

@bot.command(name="تعيين_صورة_الاعلان", aliases=["تغير_صورة_الاعلان", "تغيير_صورة_الاعلان", "تعيين_صورة_الإعلان",
                                                  "تعيين_الصورة_السوداء", "تعيين_صورة_رئيسية"])
@commands.guild_only()
@admin_only()
async def set_ann_main_cmd(ctx, url: str = None):
    await set_guild_media(ctx, "main", url)

@bot.command(name="تعيين_صورة_الجانب", aliases=["تغير_صورة_الجانب", "تغيير_صورة_الجانب",
                                                "تعيين_الصورة_الحمراء", "تعيين_صورة_جانبية"])
@commands.guild_only()
@admin_only()
async def set_ann_side_cmd(ctx, url: str = None):
    await set_guild_media(ctx, "side", url)

@bot.command(name="اعدادات_الاعلان", aliases=["إعدادات_الإعلان", "اعدادات_الإعلان"])
@commands.guild_only()
@admin_only()
async def ann_settings_cmd(ctx):
    rows = [f"{'🟢' if has_gmedia(ctx.guild, s) else '⚪'} **{lbl}**" for s, (_, lbl) in ANN_SLOTS.items()]
    e = E("📢 إعدادات الإعلان لهذا السيرفر", "\n".join(rows) + "\n\n"
          "• `تعيين_خط [رابط]` — الخط الذي يظهر تحت الإعلان\n"
          "• `تعيين_صورة_الاعلان [رابط]` — الصورة الرئيسية (السوداء) أسفل نص الإعلان\n"
          "• `تعيين_صورة_الجانب [رابط]` — الصورة الجانبية (الحمراء) على اليمين\n"
          "• أضف `حذف` بدل الرابط لإزالة أي واحدة (صورة أو GIF).", PURPLE)
    await ctx.send(embed=e)

@bot.command(name="إعلان", aliases=["اعلان"])
@commands.guild_only()
@admin_only()
async def announcement(ctx, *, text=""):
    if not text.strip():
        return await ctx.reply("اكتب نص الإعلان.")
    guild = ctx.guild
    e = E(f"👑 مملكة {brand(guild)[0]} | إعلان رسمي", text[:4000], PURPLE)
    e.set_footer(text=f"بواسطة {ctx.author.display_name}")
    files = []
    side = attach_media(e, gkey(guild, "side"), thumb=True)      # الحمراء: يمين الإعلان
    if side:
        files.append(side)
    if not e.thumbnail.url and guild.icon:
        e.set_thumbnail(url=guild.icon.url)
    main = attach_media(e, gkey(guild, "main"), "announce")      # السوداء: تحت النص بعرض الإيمبد
    if main:
        files.append(main)
    try:
        await ctx.message.delete()
    except discord.HTTPException:
        pass
    can_ping = ctx.channel.permissions_for(guild.me).mention_everyone
    try:
        # المنشن للجميع: نرسله ثم نمسح النص فيبقى التنبيه ويختفي "@everyone" من الرسالة
        msg = await ctx.send(content="@everyone" if can_ping else None, embed=e, files=files or None,
                             allowed_mentions=discord.AllowedMentions(everyone=True))
    except discord.HTTPException:
        return await ctx.send("❌ تعذر إرسال الإعلان.", delete_after=8)
    if can_ping:
        try:
            await msg.edit(content=None)
        except discord.HTTPException:
            pass
    else:
        await ctx.send("⚠️ المنشن المخفي ما اشتغل: أعطني صلاحية **Mention Everyone**.", delete_after=10)
    await send_line(ctx.channel, guild)
    await log_event(guild, "📢 إعلان", f"{ctx.author.mention} نشر إعلاناً.", "gold")

# ───────────────────────── تخصيص رتب اللفلات لكل سيرفر ─────────────────────────
_SYNCING = set()

def role_usable(guild, role):
    me = guild.me
    return bool(role and me and me.guild_permissions.manage_roles
                and not role.managed and not role.is_default() and role.position < me.top_role.position)

async def edit_role_style(guild, role, name, c1, c2, reason="Bot level roles"):
    """يعدّل اسم/لون رتبة موجودة (تدرّج لونين إن كان السيرفر يدعمه)."""
    if c2 is not None and c2 != c1 and "ENHANCED_ROLE_COLORS" in guild.features:
        try:
            await guild._state.http.edit_role(
                guild.id, role.id, reason=reason, name=name,
                colors={"primary_color": c1, "secondary_color": c2, "tertiary_color": None})
            return True
        except Exception:
            pass
    try:
        await role.edit(name=name, colour=discord.Colour(blend(c1, c2)), reason=reason)
        return True
    except discord.HTTPException:
        return False

async def set_role_icon(guild, role, img):
    if not img or not sniff_ext(img):
        return ""
    if "ROLE_ICONS" not in guild.features:
        return "\n⚠️ أيقونات الرتب تحتاج **بوست لفل 2** بالسيرفر."
    icon = await shrink_icon(img)
    if icon is None:
        return "\n⚠️ الصورة كبيرة جداً للأيقونة."
    try:
        await role.edit(display_icon=icon)
        return "\n🖼️ تم وضع الصورة كأيقونة للرتبة."
    except (discord.HTTPException, TypeError):
        return "\n⚠️ فشل وضع الأيقونة."

async def apply_layout_diff(guild, before, after, create=()):
    """يطبّق فرق التعديلات على رتب ديسكورد: تعديل الاسم/اللون، حذف المحذوف، إنشاء المطلوب."""
    res = {"edited": 0, "deleted": 0, "created": 0, "failed": 0}
    for key, (name, c1, c2) in before.items():
        role = discord.utils.get(guild.roles, name=name)
        if not role_usable(guild, role):
            continue
        if key in after:
            n2, d1, d2 = after[key]
            if (n2, d1, d2) != (name, c1, c2):
                res["edited" if await edit_role_style(guild, role, n2, d1, d2) else "failed"] += 1
                await asyncio.sleep(0.5)
        else:
            try:
                await role.delete(reason="Bot level roles")
                res["deleted"] += 1
            except discord.HTTPException:
                res["failed"] += 1
            await asyncio.sleep(0.5)
    for key in create:
        if key in after and guild.me.guild_permissions.manage_roles:
            name, c1, c2 = after[key]
            if discord.utils.get(guild.roles, name=name) is None:
                if await make_role(guild, name, c1, c2, reason="Bot level roles"):
                    res["created"] += 1
                else:
                    res["failed"] += 1
                await asyncio.sleep(0.4)
    return res

async def arrange_level_roles(guild):
    """يرتّب رتب اللفلات بين بعضها (الأعلى لفل = الأعلى بالقائمة) داخل نفس مواضعها بدون لمس رتب الإدارة."""
    snap = layout_snapshot(guild, True)
    order = sorted([k for k in snap if k[0] == "t"], key=lambda k: -k[1]) \
        + sorted([k for k in snap if k[0] == "m"], key=lambda k: -k[1]) \
        + [k for k in snap if k[0] == "n"]
    roles = []
    for k in order:
        r = discord.utils.get(guild.roles, name=snap[k][0])
        if role_usable(guild, r) and r not in roles:
            roles.append(r)
    if len(roles) < 2:
        return
    slots = sorted((r.position for r in roles), reverse=True)
    mapping = {r: p for r, p in zip(roles, slots) if r.position != p}
    if mapping:
        try:
            await guild.edit_role_positions(mapping, reason="Bot level roles order")
        except (AttributeError, TypeError, discord.HTTPException):
            pass

async def sync_level_roles(guild):
    """يطابق رتب كل الأعضاء مع إعدادات السيرفر الحالية (بالخلفية)."""
    if guild.id in _SYNCING:
        return
    _SYNCING.add(guild.id)
    try:
        managed = level_role_names(guild)
        for m in list(guild.members):
            if m.bot:
                continue
            u = db.data.get(str(m.id))
            lvl = int(u.get("level", 1)) if isinstance(u, dict) else 1
            have = {r.name for r in m.roles if r.name in managed}
            if have == set(wanted_level_names(lvl, guild)):
                continue
            await update_rank_role(guild, m, lvl)
            await asyncio.sleep(0.7)
    except Exception as ex:
        print(f"[SYNC] {ex!r}")
    finally:
        _SYNCING.discard(guild.id)

async def finish_layout_change(guild, before, create=()):
    after = layout_snapshot(guild)
    res = await apply_layout_diff(guild, before, after, create)
    await arrange_level_roles(guild)
    asyncio.create_task(sync_level_roles(guild))
    return res

def res_text(res):
    return " • ".join(f"{lbl} **{n}**" for lbl, n in (
        ("🎨 تعديل", res["edited"]), ("🗑️ حذف", res["deleted"]),
        ("✨ إنشاء", res["created"]), ("⚠️ فشل", res["failed"])) if n)

def name_conflict(guild, name, keep_key=None):
    if name.lower() in ("@everyone", "@here"):
        return "اسم غير مسموح."
    snap = layout_snapshot(guild, True)
    for k, (n, _, _) in snap.items():
        if n == name and k != keep_key:
            return "هذا الاسم مستخدم لرتبة فلات أخرى."
    if discord.utils.get(guild.roles, name=name) and name not in {v[0] for v in snap.values()}:
        return "عندك رتبة عادية بنفس الاسم، اختر اسماً مختلفاً حتى لا أعدّل رتب الإدارة."
    return None

def parse_role_args(ctx, args):
    """يفكك: [اسم] [لون] [لون2] [رابط صورة] ← (الاسم, الألوان, رابط)."""
    parts = args.split()
    url = None
    if parts and urlparse(parts[-1]).scheme in ("http", "https"):
        url = parts.pop()
    cols = []
    while parts and HEX_RE.match(parts[-1]) and len(cols) < 2:
        cols.insert(0, parse_hex(parts.pop()))
    return " ".join(parts).strip(), cols, url

async def read_icon(ctx, url):
    att = ctx.message.attachments[0] if ctx.message.attachments else None
    if att:
        return await att.read()
    return await fetch_bytes(url) if url else None

def fmt_hex(c1, c2):
    return f"`#{c1:06X}`" + (f" ➜ `#{c2:06X}`" if c2 != c1 else "")

def tiers_embed(guild):
    lines = []
    for lv, name, en, cols, desc in guild_ranks(guild):
        r = discord.utils.get(guild.roles, name=name)
        lines.append(f"`LV {lv:>3}` {r.mention if r else name} {fmt_hex(*cols)}")
    nm = new_member_spec(guild)
    ms = f"🟢 `{milestone_name('N', guild)}` كل 5 لفلات" if milestones_on(guild) else "🔴 مطفية"
    nmt = (discord.utils.get(guild.roles, name=nm[0]).mention if discord.utils.get(guild.roles, name=nm[0]) else nm[0]) \
        + " " + fmt_hex(*nm[1]) if nm else "🔴 محذوفة"
    e = E("🎖️ رتب اللفلات لهذا السيرفر", "\n".join(lines) or "لا توجد رتب.", PURPLE)
    e.add_field(name="🆕 رتبة العضو الجديد", value=nmt, inline=False)
    e.add_field(name="⌬ رتب كل 5 لفلات", value=ms, inline=False)
    e.add_field(name="🛠️ الأوامر", inline=False, value=(
        "• `تعيين_الفلات [اللفل] [الاسم] [لون] [لون2] [رابط صورة]` — إضافة/تعديل رتبة\n"
        "• `حذف_فلات [اللفل]` — حذف رتبة\n"
        "• `تعيين_نيو_مبر [الاسم] [لون] [لون2]` — رتبة العضو الجديد (`حذف` لإلغائها)\n"
        "• `رتب_كل_5 [تشغيل|ايقاف|اسم بادئة]`\n"
        "• `ثيم_الفلات [ناري|جليدي|نيون|كوني|ملكي]` — ستايل جاهز خرافي\n"
        "• `اعادة_الفلات` — الرجوع للافتراضي • `مزامنة_الرتب` — تحديث رتب الكل"))
    return e

@bot.command(name="تعيين_الفلات", aliases=["تعيين_فلات", "تعيين_رتبة_لفل", "تعيين_لفل"])
@commands.guild_only()
@admin_only()
async def set_tier_cmd(ctx, level: int = None, *, args: str = ""):
    guild = ctx.guild
    if level is None:
        return await ctx.send(embed=tiers_embed(guild))
    if not 1 <= level <= MAX_LEVEL:
        return await ctx.reply(f"اللفل من 1 إلى {MAX_LEVEL}.")
    if not guild.me.guild_permissions.manage_roles:
        return await ctx.reply("❌ أحتاج صلاحية **Manage Roles**.")
    name, cols, url = parse_role_args(ctx, args)
    icon = await read_icon(ctx, url)
    key = ("t", level)
    before = layout_snapshot(guild)
    cur = before.get(key)
    if not name and not cols:
        return await ctx.reply("الاستخدام: `تعيين_الفلات 25 اسم الرتبة 0xFF0000 0x00FF00 [رابط صورة]`")
    name = name or (cur[0] if cur else "")
    if not name or len(name) > 100:
        return await ctx.reply("اكتب اسم الرتبة (حتى 100 حرف).")
    bad = name_conflict(guild, name, key)
    if bad:
        return await ctx.reply(f"❌ {bad}")
    if cols:
        c1, c2 = cols[0], (cols[1] if len(cols) > 1 else cols[0])
    elif cur:
        c1, c2 = cur[1], cur[2]
    else:
        c1, c2 = milestone_colors(level)
    _lv_edit(guild).setdefault("tiers", {})[str(level)] = {"name": name, "c1": c1, "c2": c2}
    db.mark()
    res = await finish_layout_change(guild, before, create=[key])
    role = discord.utils.get(guild.roles, name=name)
    note = await set_role_icon(guild, role, icon) if role else ""
    e = E("✅ تم ضبط رتبة اللفل", f"**LV {level}** → {role.mention if role else name}\nاللون: {fmt_hex(c1, c2)}{note}\n"
          f"{res_text(res)}\n⏳ جاري تحديث رتب الأعضاء بالخلفية.", c1)
    await ctx.send(embed=e)
    await log_event(guild, "🎖️ تعديل رتب اللفلات", f"{ctx.author.mention} ضبط LV {level} ← `{name}`", "purple")

@bot.command(name="حذف_فلات", aliases=["حذف_رتبة_لفل", "حذف_لفل", "حذف_الفلات"])
@commands.guild_only()
@admin_only()
async def delete_tier_cmd(ctx, level: int):
    guild = ctx.guild
    key = ("t", level)
    before = layout_snapshot(guild)
    if key not in before:
        return await ctx.reply("ما في رتبة فلات بهذا اللفل. اكتب `تعيين_الفلات` لعرض الرتب.")
    tiers = _lv_edit(guild).setdefault("tiers", {})
    if any(e[0] == level for e in RANKS):
        tiers[str(level)] = None
    else:
        tiers.pop(str(level), None)
    db.mark()
    res = await finish_layout_change(guild, before)
    await ctx.send(embed=E("🗑️ تم حذف رتبة اللفل", f"حُذفت رتبة **LV {level}** `{before[key][0]}`.\n{res_text(res)}", 0xE74C3C))
    await log_event(guild, "🎖️ حذف رتبة لفل", f"{ctx.author.mention} حذف LV {level}", "red")

@bot.command(name="تعيين_نيو_مبر", aliases=["تعيين_نيو", "تعيين_العضو_الجديد", "تعيين_نيو_ميمبر", "نيو_مبر"])
@commands.guild_only()
@admin_only()
async def set_new_member_cmd(ctx, *, args: str = ""):
    guild = ctx.guild
    before = layout_snapshot(guild)
    key = ("n",)
    word = args.strip().lower()
    if word in ("حذف", "delete", "ازالة", "إزالة"):
        _lv_edit(guild)["new"] = {"off": True}
        db.mark()
        res = await finish_layout_change(guild, before)
        return await ctx.send(embed=E("🗑️ تم حذف رتبة العضو الجديد", res_text(res) or "تم.", 0xE74C3C))
    if word in ("اعادة", "reset", "إعادة"):
        _lv_edit(guild).pop("new", None)
        db.mark()
        res = await finish_layout_change(guild, before, create=[key])
        return await ctx.send(embed=E("♻️ رجعت رتبة العضو الجديد للافتراضية", res_text(res) or "تم."))
    name, cols, url = parse_role_args(ctx, args)
    icon = await read_icon(ctx, url)
    if not name and not cols and not icon:
        return await ctx.reply("الاستخدام: `تعيين_نيو_مبر اسم الرتبة 0x95A5A6 0x5865F2 [رابط صورة]` • `تعيين_نيو_مبر حذف` • `تعيين_نيو_مبر اعادة`")
    cur = before.get(key) or (NEW_MEMBER, *NEW_MEMBER_COLORS)
    name = name or cur[0]
    if len(name) > 100:
        return await ctx.reply("الاسم طويل (حد أقصى 100).")
    bad = name_conflict(guild, name, key)
    if bad:
        return await ctx.reply(f"❌ {bad}")
    c1, c2 = (cols[0], cols[1] if len(cols) > 1 else cols[0]) if cols else (cur[1], cur[2])
    _lv_edit(guild)["new"] = {"name": name, "c1": c1, "c2": c2}
    db.mark()
    res = await finish_layout_change(guild, before, create=[key])
    role = discord.utils.get(guild.roles, name=name)
    note = await set_role_icon(guild, role, icon) if role else ""
    await ctx.send(embed=E("✅ تم ضبط رتبة العضو الجديد",
                           f"{role.mention if role else name}\nاللون: {fmt_hex(c1, c2)}{note}\n{res_text(res)}", c1))

@bot.command(name="رتب_كل_5", aliases=["رتب_الخمسات", "رتب_5"])
@commands.guild_only()
@admin_only()
async def milestones_cmd(ctx, action: str = None, *, value: str = ""):
    guild = ctx.guild
    before = layout_snapshot(guild)
    lv = _lv_edit(guild)
    if action in ("ايقاف", "إيقاف", "off", "اطفاء"):
        lv["milestones"] = False
    elif action in ("تشغيل", "on", "تفعيل"):
        lv["milestones"] = True
    elif action in ("اسم", "name") and value.strip():
        lv["ms_prefix"] = value.strip()[:60]
    elif action in ("اعادة", "reset", "إعادة"):
        lv.pop("ms_prefix", None)
    else:
        state = "🟢 شغّالة" if milestones_on(guild) else "🔴 مطفية"
        return await ctx.send(embed=E("⌬ رتب كل 5 لفلات", f"الحالة: {state}\nالشكل الحالي: `{milestone_name(5, guild)}`\n\n"
                                      "`رتب_كل_5 تشغيل` • `رتب_كل_5 ايقاف` (تحذف الرتب)\n"
                                      "`رتب_كل_5 اسم ✦ Rank` ← تصير `✦ Rank 5`, `✦ Rank 10`...\n`رتب_كل_5 اعادة`", PURPLE))
    db.mark()
    res = await finish_layout_change(guild, before)
    await ctx.send(embed=E("✅ تم التحديث", f"رتب كل 5 لفلات: {'🟢' if milestones_on(guild) else '🔴'} • الشكل: `{milestone_name(5, guild)}`\n{res_text(res)}"))

LEVEL_THEMES = {
    "ناري": [
        (100, "🔥 ☄️ إمبراطور اللهب ☄️ 🔥", 0xFF0000, 0xFFD700), (75, "🌋 سيد البراكين", 0xFF3300, 0xFF9900),
        (60, "⚔️ فارس الجحيم", 0xCC0000, 0xFF4500), (50, "🔥 ساحر النار", 0xFF4500, 0xFFA500),
        (40, "💥 قائد الشرارة", 0xFF6600, 0xFFCC00), (30, "🌟 حارس اللهب", 0xFF8C00, 0xFFE066),
        (20, "🕯️ حامل الشعلة", 0xE25822, 0xFFB347), (10, "✨ شرارة", 0xB5451B, 0xFF9F43),
        (5, "🪵 جمرة", 0x8B3A1A, 0xD2691E), (1, "🌑 رماد", 0x4A3B35, 0x8B7D77)],
    "جليدي": [
        (100, "❄️ ملك الجليد الأبدي ❄️", 0xE0FFFF, 0x00BFFF), (75, "🧊 سيد الصقيع", 0xB0E0FF, 0x4169E1),
        (60, "🌨️ حاكم العاصفة", 0x87CEFA, 0x6A5ACD), (50, "🏔️ حارس القمة", 0x5DADE2, 0xAED6F1),
        (40, "💎 أمير البلّور", 0x48C9B0, 0x85E3FF), (30, "🌬️ فارس الشتاء", 0x2E86C1, 0x85C1E9),
        (20, "⛄ نبيل الثلج", 0x76D7C4, 0xD6EAF8), (10, "🧣 مسافر الصقيع", 0x5499C7, 0xA9CCE3),
        (5, "💧 قطرة ندى", 0x7FB3D5, 0xD4E6F1), (1, "🌫️ ضباب", 0x909497, 0xD5D8DC)],
    "نيون": [
        (100, "⚡ أسطورة النيون ⚡", 0xFF00FF, 0x00FFFF), (75, "🌐 سيد الشبكة", 0x00FFEA, 0xFF00C8),
        (60, "🧬 مهندس الكود", 0x39FF14, 0x00E5FF), (50, "🎮 بطل الأركيد", 0xFF1493, 0x7DF9FF),
        (40, "🛸 قائد الفضاء", 0xB026FF, 0x00F0FF), (30, "💠 صائد الإشارات", 0x00F5FF, 0x7B2FFF),
        (20, "🔆 مشغّل النظام", 0xFFE600, 0x39FF14), (10, "🔌 متصل", 0x00FF9C, 0x00B8FF),
        (5, "📡 إشارة", 0x7CFFCB, 0x74F2FF), (1, "💤 وضع الخمول", 0x6C7A89, 0x9AA5B1)],
    "كوني": [
        (100, "🌌 خالق المجرات 🌌", 0xFFD700, 0x8A2BE2), (75, "🪐 سيد الكواكب", 0x9B59B6, 0xFFB6FF),
        (60, "☄️ مُطارد المذنبات", 0x5B2C83, 0xFF6EC7), (50, "🌠 حارس النجوم", 0x4B0082, 0x00BFFF),
        (40, "🛰️ قائد المدار", 0x1F3A93, 0xB388FF), (30, "🚀 رائد الفضاء", 0x3F51B5, 0x00E5FF),
        (20, "🔭 راصد السماء", 0x283593, 0x7986CB), (10, "🌙 ساكن القمر", 0x5C6BC0, 0xE8EAF6),
        (5, "⭐ شهاب", 0x7E57C2, 0xD1C4E9), (1, "🌑 غبار كوني", 0x37474F, 0x90A4AE)],
}

@bot.command(name="ثيم_الفلات", aliases=["ثيم_فلات", "ستايل_الفلات"])
@commands.guild_only()
@admin_only()
async def theme_cmd(ctx, *, theme: str = ""):
    guild = ctx.guild
    theme = theme.strip()
    if theme in ("ملكي", "افتراضي", "الافتراضي"):
        return await reset_tiers_cmd(ctx)
    if theme not in LEVEL_THEMES:
        names = "، ".join(["ملكي (الافتراضي)"] + list(LEVEL_THEMES))
        return await ctx.send(embed=E("🎨 ثيمات رتب اللفلات", f"اختر ثيماً: `ثيم_الفلات ناري`\nالمتاح: **{names}**\n"
                                      "الثيم يغيّر أسماء وألوان رتب اللفلات الرئيسية (10 رتب بتدرّج لونين) ويعدّل الرتب الموجودة.", PURPLE))
    if not guild.me.guild_permissions.manage_roles:
        return await ctx.reply("❌ أحتاج صلاحية **Manage Roles**.")
    before = layout_snapshot(guild)
    tiers = {str(lv): {"name": n, "c1": c1, "c2": c2} for lv, n, c1, c2 in LEVEL_THEMES[theme]}
    for e0 in RANKS:
        tiers.setdefault(str(e0[0]), None)
    _lv_edit(guild)["tiers"] = tiers
    db.mark()
    msg = await ctx.send(embed=E("🎨 جاري تطبيق الثيم...", f"**{theme}** — قد ياخذ دقيقة."))
    res = await finish_layout_change(guild, before, create=[("t", lv) for lv, *_ in LEVEL_THEMES[theme]])
    await msg.edit(embed=E(f"✅ تم تطبيق ثيم {theme}", res_text(res) or "تم.", LEVEL_THEMES[theme][0][2]))
    await ctx.send(embed=tiers_embed(guild))

@bot.command(name="اعادة_الفلات", aliases=["إعادة_الفلات", "ريست_الفلات"])
@commands.guild_only()
@admin_only()
async def reset_tiers_cmd(ctx):
    guild = ctx.guild
    before = layout_snapshot(guild)
    db.cfg(guild.id).pop("lv", None)
    db.mark()
    res = await finish_layout_change(guild, before)
    await ctx.send(embed=E("♻️ رجعت رتب اللفلات للافتراضي", res_text(res) or "تم."))

@bot.command(name="مزامنة_الرتب", aliases=["تحديث_الرتب"])
@commands.guild_only()
@admin_only()
async def sync_cmd(ctx):
    if ctx.guild.id in _SYNCING:
        return await ctx.reply("⏳ المزامنة شغّالة حاليًا.")
    asyncio.create_task(sync_level_roles(ctx.guild))
    await ctx.send(embed=E("🔄 بدأت المزامنة", "أطابق رتب كل الأعضاء مع إعدادات الفلات الحالية بالخلفية."))

# ───────────────────────── إنشاء / حذف رتب اللفلات دفعة واحدة ─────────────────────────
LV_LINE_RE = re.compile(r"^(?:lv|lvl|level|لفل|ليفل)?\s*(\d{1,4})\s*[:：|・\-]?\s*(.*)$", re.I)
NEW_LINE_RE = re.compile(r"^(?:جديد|نيو|new)\s*[:：|・\-]?\s*(.*)$", re.I)
LV_USAGE = ("اكتب رتب اللفلات **برسالة واحدة**، سطر لكل رتبة: `اللفل` ثم `الاسم` ثم لون أو لونين (اختياري):\n"
            "```انشاء_رتب_لفل\n"
            "جديد ✧ New Soul 0x95A5A6\n"
            "5 ☁ Dreamer 0xC4B5FD\n"
            "10 ☾ Moon Walker 0x8B5CF6 0xC4B5FD\n"
            "50 𖤐 Eclipse 0x4C1D95\n"
            "100 ♛ Luna Legend 0xE9A8D4 0x8B5CF6```\n"
            "• السطر اللي يبدأ بـ `جديد` = رتبة العضو الجديد (قبل أول رتبة)\n"
            "• بدون لون يختار البوت لوناً تلقائياً • الزخرفة مسموحة بالأسماء\n"
            "• البوت ينشئ الرتب ويعتمدها لهذا السيرفر ويوزعها على الأعضاء حسب لفلهم\n"
            "• أعد الأمر لإضافة أو تعديل رتب، و`حذف_رتب_لفل` يحذفها كلها.")

def parse_level_lines(text):
    tiers, new, errors = {}, None, []
    for raw in (text or "").replace("\r", "").split("\n"):
        line = raw.strip()
        if not line:
            continue
        m = NEW_LINE_RE.match(line)
        is_new = bool(m)
        if is_new:
            level, rest = None, m.group(1)
        else:
            m = LV_LINE_RE.match(line)
            if not m:
                errors.append(f"سطر غير مفهوم: `{line[:40]}`")
                continue
            level, rest = int(m.group(1)), m.group(2)
            if not 1 <= level <= MAX_LEVEL:
                errors.append(f"اللفل `{level}` خارج المدى (1 إلى {MAX_LEVEL}).")
                continue
            if level in tiers:
                errors.append(f"اللفل `{level}` مكرر.")
                continue
        parts = rest.split()
        cols = []
        while parts and HEX_RE.match(parts[-1]) and len(cols) < 2:
            cols.insert(0, parse_hex(parts.pop()))
        name = " ".join(parts).strip() or (NEW_MEMBER if is_new else f"Level {level}")
        if len(name) > 100 or name.lower() in ("@everyone", "@here"):
            errors.append(f"اسم غير صالح: `{name[:40]}`")
            continue
        if cols:
            c1, c2 = cols[0], (cols[1] if len(cols) > 1 else cols[0])
        elif is_new:
            c1, c2 = NEW_MEMBER_COLORS
        else:
            c1, c2 = milestone_colors(level)
        spec = {"name": name, "c1": c1, "c2": c2}
        if is_new:
            new = spec
        else:
            tiers[level] = spec
    return tiers, new, errors

@bot.command(name="انشاء_رتب_لفل", aliases=["انشاء_رتب_الفل", "انشاء_رتب_اللفل", "انشاء_رتب_فلات", "انشاء_رتب_اللفلات"])
@commands.guild_only()
@admin_only()
async def build_level_roles(ctx, *, text: str = ""):
    guild = ctx.guild
    tiers, new, errors = parse_level_lines(text)
    if not tiers and not new and not errors:
        return await ctx.send(embed=E("🎖️ إنشاء رتب اللفلات", LV_USAGE, PURPLE))
    if errors:
        return await ctx.reply("❌ " + "\n".join(errors[:8]))
    if not guild.me.guild_permissions.manage_roles:
        return await ctx.reply("❌ أحتاج صلاحية **Manage Roles**.")
    names = [v["name"] for v in tiers.values()] + ([new["name"]] if new else [])
    if len(set(names)) != len(names):
        return await ctx.reply("❌ في أسماء مكررة بين الرتب، كل رتبة لازم اسمها يكون مختلف.")
    if len(guild.roles) + len(names) > 245:
        return await ctx.reply("❌ عدد رتب السيرفر راح يتجاوز الحد الأقصى (250).")
    for lv, v in tiers.items():
        bad = name_conflict(guild, v["name"], ("t", lv))
        if bad:
            return await ctx.reply(f"❌ `{v['name']}`: {bad}")
    if new:
        bad = name_conflict(guild, new["name"], ("n",))
        if bad:
            return await ctx.reply(f"❌ `{new['name']}`: {bad}")
    before = layout_snapshot(guild)
    lvcfg = _lv_edit(guild)
    td = lvcfg.setdefault("tiers", {})
    for lv, v in tiers.items():
        td[str(lv)] = v
    if new:
        lvcfg["new"] = new
    db.mark()
    msg = await ctx.send(embed=E("🎖️ جاري إنشاء رتب اللفلات...", f"عدد الرتب: **{len(names)}**", PURPLE))
    QUIET.add(guild.id)
    try:
        keys = [("t", lv) for lv in tiers] + ([("n",)] if new else [])
        res = await finish_layout_change(guild, before, create=keys)
    finally:
        QUIET.discard(guild.id)
    lines = []
    if new:
        r = discord.utils.get(guild.roles, name=new["name"])
        lines.append(f"`NEW` {r.mention if r else new['name']}")
    for lv in sorted(tiers):
        r = discord.utils.get(guild.roles, name=tiers[lv]["name"])
        lines.append(f"`LV {lv:>3}` {r.mention if r else tiers[lv]['name']}")
    body = "\n".join(lines[:25]) + (f"\n… و{len(lines) - 25} أخرى" if len(lines) > 25 else "")
    await msg.edit(embed=E("✅ تم إنشاء رتب اللفلات واعتمادها",
                           f"{body}\n\n{res_text(res)}\n⏳ جاري توزيعها على الأعضاء حسب لفلهم بالخلفية.", 0x2ECC71))

@bot.command(name="حذف_رتب_لفل", aliases=["حذف_رتب_الفل", "حذف_رتب_اللفل", "حذف_رتب_اللفلات", "حذف_كل_رتب_الفل"])
@commands.guild_only()
@admin_only()
async def wipe_level_roles(ctx):
    guild = ctx.guild
    if not guild.me.guild_permissions.manage_roles:
        return await ctx.reply("❌ أحتاج صلاحية **Manage Roles**.")
    roles = []
    for name, _, _ in layout_snapshot(guild, True).values():
        r = discord.utils.get(guild.roles, name=name)
        if r and r not in roles:
            roles.append(r)
    if not roles and not db.cfg(guild.id).get("lv"):
        return await ctx.reply("ما في رتب لفلات بهذا السيرفر.")
    view = ConfirmView(ctx.author.id)
    msg = await ctx.send(embed=E("⚠️ تأكيد حذف رتب اللفلات",
                                 f"راح أحذف **{len(roles)}** رتبة لفل من السيرفر وأمسح إعداداتها.\n"
                                 "مستويات الأعضاء والـ XP تبقى، وتقدر تسوي الرتب من جديد بـ `انشاء_رتب_لفل`.\n"
                                 "عندك 30 ثانية.", 0xE74C3C), view=view)
    await view.wait()
    for c in view.children:
        c.disabled = True
    if not view.ok:
        return await msg.edit(embed=E("✖️ انلغى الحذف", "ما انحذف شي.", 0x95A5A6), view=view)
    await msg.edit(embed=E("💥 جاري حذف رتب اللفلات...", "لحظات.", 0xE74C3C), view=view)
    deleted = failed = 0
    QUIET.add(guild.id)
    try:
        for r in roles:
            if not role_usable(guild, r):
                failed += 1
                continue
            try:
                await r.delete(reason=f"Bot level roles wipe by {ctx.author}")
                deleted += 1
            except discord.HTTPException:
                failed += 1
            await asyncio.sleep(0.5)
        db.cfg(guild.id).pop("lv", None)
        db.mark()
        await asyncio.sleep(2)
    finally:
        QUIET.discard(guild.id)
    note = "\n⚠️ الرتب اللي فشل حذفها (أعلى من رتبة البوت) انحذف اعتمادها وصارت رتب عادية." if failed else ""
    await msg.edit(embed=E("✅ تم حذف رتب اللفلات", f"🗑️ انحذف **{deleted}** • ⚠️ فشل **{failed}**{note}", 0x2ECC71), view=view)

# ───────────────────────── التجهيز + الضبط + الحماية + الصور ─────────────────────────
# ───────────────────────── التجهيز + الضبط + اللوقات ─────────────────────────
CHANNEL_KINDS = {
    "ترحيب": "welcome_channel", "وداع": "welcome_channel", "لفل": "level_channel", "لفلات": "level_channel", "مستويات": "level_channel",
    "لوق": "log_channel", "لوغ": "log_channel", "لوقات": "log_channel", "لوغات": "log_channel",
    "فعاليات": "events_channel", "فعالية": "events_channel", "اقتراحات": "suggest_channel", "اقتراح": "suggest_channel",
    "الوان": "colors_channel", "ألوان": "colors_channel",
}
NAMES_BY_KEY = {"welcome_channel": WELCOME_NAMES, "level_channel": LEVEL_NAMES, "log_channel": LOG_NAMES,
                "events_channel": EVENTS_NAMES, "suggest_channel": SUGGEST_NAMES, "colors_channel": COLORS_NAMES}
DEFAULT_CH = {
    "welcome_channel": ("👋・الترحيب", "ro"), "level_channel": ("🆙・اللفلات", "ro"),
    "log_channel": ("📜・اللوقات", "private"), "events_channel": ("🎉・الفعاليات", "ro"),
    "suggest_channel": ("💡・الاقتراحات", "vote"),
    "colors_channel": ("🎨・الالوان", "ro"),
}
LOGS_CAT = "📜・سجلات الإدارة"

# لكل مجموعة أوامر إدارية لوق خاص بها (ضبط_<الاسم> #روم)
_SETTINGS_CMDS = ["ضبط", "حماية", "تجهيز", "تعيين_اسم", "تعيين_بايو", "تعيين_افتار", "اعادة_هوية", "اضافة_جيف", "حذف_جيف",
                  "اضافة_منتج", "حذف_منتج", "صورة", "تعيين_خط", "تعيين_صورة_الاعلان", "تعيين_صورة_الجانب",
                  "تعيين_الفلات", "حذف_فلات", "انشاء_رتب_لفل", "حذف_رتب_لفل", "تعيين_نيو_مبر", "رتب_كل_5", "ثيم_الفلات", "اعادة_الفلات",
                  "مزامنة_الرتب", "اعدادات_فويس", "تعيين_ساعات", "فعاليات", "تلقائي", "صلاة", "جيفاواي", "جيفاواي_جديد", "جيفاواي_جائزة", "تذكرة_لوحة",
                  "تعيين_ادارة", "حذف_ادارة", "رسالة_لفل"]
ADMIN_LOGS = [
    {"key": "ban", "name": "حظر", "label": "الحظر", "emoji": "🔨", "color": 0xE74C3C, "cmds": ["حظر", "رفع_حظر"]},
    {"key": "kick", "name": "طرد", "label": "الطرد", "emoji": "👢", "color": 0xE67E22, "cmds": ["طرد"]},
    {"key": "mute", "name": "ميوت", "label": "الميوت", "emoji": "🔇", "color": 0x95A5A6, "cmds": ["ميوت", "انهض"]},
    {"key": "warn", "name": "تحذير", "label": "التحذيرات", "emoji": "⚠️", "color": 0xE67E22, "cmds": ["تحذير", "عفو"]},
    {"key": "clear", "name": "مسح", "label": "المسح", "emoji": "🧹", "color": 0x3498DB, "cmds": ["مسح"]},
    {"key": "lock", "name": "قفل", "label": "القفل", "emoji": "🔒", "color": 0xE74C3C, "cmds": ["قفل", "فتح", "بطيء"]},
    {"key": "roles", "name": "رتب", "label": "الرتب", "emoji": "🎭", "color": 0x3498DB,
     "cmds": ["اعطاء", "سحب", "انشاء_رتبة", "اصنع", "حذف_رتبة", "انشاء_رتب_لفل", "حذف_رتب_لفل"]},
    {"key": "stats", "name": "مستوى", "label": "المستويات", "emoji": "📈", "color": PURPLE, "cmds": ["لفل", "خصم", "عملات", "اكس_بي", "ازالة_اكس_بي", "مضاعف_اكس_بي", "ايقاف_المضاعف"]},
    {"key": "emergency", "name": "طوارئ", "label": "الطوارئ", "emoji": "🚨", "color": 0xE74C3C, "cmds": ["طوارئ", "استقرار"]},
    {"key": "announce", "name": "اعلان", "label": "الاعلانات", "emoji": "📢", "color": GOLD, "cmds": ["إعلان"]},
    {"key": "structure", "name": "هيكل", "label": "الهيكل", "emoji": "🏗️", "color": PURPLE,
     "cmds": ["اسماء_الاقسام", "اسماء_الرومات", "تسمية_الهيكل", "انشاء_هيكل", "حذف_الهيكل"]},
    {"key": "settings", "name": "اعدادات", "label": "الاعدادات", "emoji": "⚙️", "color": PURPLE, "cmds": _SETTINGS_CMDS},
]
ALOG_BY_NAME = {e["name"]: e for e in ADMIN_LOGS}
ALOG_BY_KEY = {e["key"]: e for e in ADMIN_LOGS}
ADMIN_CMD_KIND = {c: e["key"] for e in ADMIN_LOGS for c in e["cmds"]}
OFF_SET = ("حذف", "ايقاف", "إيقاف", "ازالة", "إزالة", "الغاء", "إلغاء", "off", "delete")
CREATE_SET = ("انشاء", "إنشاء", "جديد", "create", "new")

def alog_channel(guild, key):
    cid = db.cfg(guild.id).get(f"alog_{key}")
    return guild.get_channel(cid) if cid else None

def room_ow(guild, mode):
    me_ow = discord.PermissionOverwrite(view_channel=True, send_messages=True, embed_links=True, attach_files=True)
    if mode == "private":
        return {guild.default_role: discord.PermissionOverwrite(view_channel=False), guild.me: me_ow}
    if mode == "ro":
        return {guild.default_role: discord.PermissionOverwrite(send_messages=False, add_reactions=False), guild.me: me_ow}
    if mode == "vote":  # الأعضاء يصوّتون بالتفاعلات بس ما يكتبون
        return {guild.default_role: discord.PermissionOverwrite(send_messages=False, add_reactions=True), guild.me: me_ow}
    return {}

async def logs_category(guild):
    cat = discord.utils.get(guild.categories, name=LOGS_CAT)
    if cat is None:
        cat = await guild.create_category(LOGS_CAT, overwrites=room_ow(guild, "private"), reason="Bot logs")
    return cat

async def create_log_channel(guild, entry, name=None):
    cat = await logs_category(guild)
    nm = (name or f"{entry['emoji']}・لوق-{entry['label']}")[:100]
    ch = await guild.create_text_channel(nm, category=cat, overwrites=room_ow(guild, "private"), reason="Bot admin log")
    db.cfg(guild.id)[f"alog_{entry['key']}"] = ch.id
    db.mark()
    return ch

async def main_category(guild):
    """قسم الرومات الأساسية: يحمل اسم البوت الذي اختاره الأونر (ويُحفظ بالـ id حتى لو تغيّر الاسم)."""
    cfg = db.cfg(guild.id)
    cat = guild.get_channel(cfg.get("main_cat") or 0)
    if isinstance(cat, discord.CategoryChannel):
        return cat
    nm = f"👑・{brand(guild)[0]}"[:100]
    cat = discord.utils.get(guild.categories, name=nm) or await guild.create_category(nm, reason="Bot setup")
    cfg["main_cat"] = cat.id
    db.mark()
    return cat

async def create_plain_channel(guild, key, name=None):
    dname, mode = DEFAULT_CH[key]
    cat = await main_category(guild)
    ch = await guild.create_text_channel((name or dname)[:100], category=cat, overwrites=room_ow(guild, mode), reason="Bot setup")
    if key == "colors_channel":
        pe, pf = color_panel_embed()
        await ch.send(embed=pe, view=ColorView(), files=files_of(pf))
    return ch

SETUP_PARTS = {"رتب": "roles", "رومات": "channels", "لوغات": "logs", "لوقات": "logs", "حماية": "protect", "الكل": "all"}

@bot.command(name="تجهيز")
@commands.guild_only()
@admin_only()
async def setup_cmd(ctx, *, parts: str = ""):
    guild = ctx.guild
    wanted = {SETUP_PARTS[p] for p in parts.split() if p in SETUP_PARTS}
    if not wanted or "all" in wanted:
        wanted = {"roles", "channels", "logs", "protect"}
    gp = guild.me.guild_permissions
    if ("roles" in wanted and not gp.manage_roles) or (wanted & {"channels", "logs"} and not gp.manage_channels):
        return await ctx.reply("❌ أحتاج صلاحيتي **Manage Roles** و **Manage Channels**.")
    msg = await ctx.send(embed=E("⚙️ جاري التجهيز...", "⏳ قد ياخذ دقيقة."))
    cfg = db.cfg(guild.id)
    made, created = 0, []
    QUIET.add(guild.id)
    try:
        if "roles" in wanted:
            for name, c1, c2 in layout_snapshot(guild).values():
                if discord.utils.get(guild.roles, name=name) is None:
                    if await make_role(guild, name, c1, c2, reason="Bot setup"):
                        made += 1
                        await asyncio.sleep(0.4)
        if "channels" in wanted:
            for key in DEFAULT_CH:
                ch = get_channel(guild, key, NAMES_BY_KEY[key])
                if ch is None:
                    ch = await create_plain_channel(guild, key)
                    created.append(ch.mention)
                    await asyncio.sleep(0.4)
                cfg[key] = ch.id
        if "logs" in wanted:
            for entry in ADMIN_LOGS:
                if alog_channel(guild, entry["key"]) is None:
                    ch = await create_log_channel(guild, entry)
                    created.append(ch.mention)
                    await asyncio.sleep(0.4)
    except discord.Forbidden:
        QUIET.discard(guild.id)
        return await msg.edit(embed=E("❌ صلاحيات ناقصة", "ما قدرت أنشئ الرومات/الرتب."))
    finally:
        QUIET.discard(guild.id)
    if "protect" in wanted:
        cfg["antilink"] = True
        cfg["antispam"] = True
    db.mark()
    e = E("✅ تم التجهيز", f"الأجزاء: {' • '.join(sorted(wanted))}", color=0x2ECC71)
    if "roles" in wanted:
        e.add_field(name="🎭 الرتب", value=f"جديدة: **{made}**", inline=False)
    if wanted & {"channels", "logs"}:
        e.add_field(name="💬 الرومات", value=(" ".join(created) or "كلها موجودة مسبقاً ✅")[:1000], inline=False)
    if "protect" in wanted:
        e.add_field(name="🛡️ الحماية", value="مفعّلة", inline=False)
    f = attach_media(e, "setup")
    await msg.edit(embed=e, attachments=files_of(f) or [])

async def apply_channel_setting(ctx, kind, rest):
    guild = ctx.guild
    kind = norm_kind(kind)
    entry = ALOG_BY_NAME.get(kind or "")
    key = f"alog_{entry['key']}" if entry else CHANNEL_KINDS.get(kind or "")
    if not key and kind:
        await ctx.reply(f"❓ ما أعرف الخدمة **{kind}** — هذي لوحة الخيارات:")
        return await send_rooms_panel(ctx)
    if not key:
        return await send_rooms_panel(ctx)
    cfg = db.cfg(guild.id)
    rest = rest.strip()
    word = rest.split(maxsplit=1)[0] if rest else ""
    if word in OFF_SET:
        cfg.pop(key, None)
        db.mark()
        return await ctx.send(f"🗑️ تم إلغاء ربط **{kind}** (الروم نفسه ما انحذف).")
    create = word in CREATE_SET or (not word and entry is not None)
    if create:
        if not guild.me.guild_permissions.manage_channels:
            return await ctx.reply("❌ أحتاج صلاحية **Manage Channels**.")
        nm = rest.split(maxsplit=1)[1].strip() if len(rest.split(maxsplit=1)) > 1 else None
        try:
            channel = await create_log_channel(guild, entry, nm) if entry else await create_plain_channel(guild, key, nm)
        except discord.HTTPException:
            return await ctx.reply("❌ تعذر إنشاء الروم.")
    elif word:
        try:
            channel = await commands.TextChannelConverter().convert(ctx, rest)
        except commands.BadArgument:
            return await ctx.reply("❌ ما لقيت هذا الروم. منشنه `#روم` أو اكتب `انشاء`.")
    else:
        channel = ctx.channel
    cfg[key] = channel.id
    db.mark()
    await ctx.send(f"✅ تم ضبط **{kind}** على {channel.mention}.")

def norm_kind(kind):
    k = (kind or "").strip()
    if k in CHANNEL_KINDS or k in ALOG_BY_NAME:
        return k
    if k.startswith("ال") and (k[2:] in CHANNEL_KINDS or k[2:] in ALOG_BY_NAME):
        return k[2:]
    return k

ROOM_SERVICES = [
    ("welcome_channel", "👋", "الترحيب والوداع", "بطاقة الترحيب + رسالة الوداع"),
    ("level_channel", "🆙", "تهنئة اللفلات", "رسالة التهنئة عند كل ارتقاء"),
    ("log_channel", "📜", "لوقات السيرفر", "دخول/خروج/حذف/تعديل الرسائل والرتب"),
    ("events_channel", "🎉", "روم الفعاليات", "الجيفاواي والرسائل التلقائية وتذكير الصلاة"),
    ("suggest_channel", "💡", "روم الاقتراحات", "الاقتراحات اللي يرسلها الأعضاء بأمر اقتراح"),
    ("colors_channel", "🎨", "روم الألوان", "لوحة اختيار اللون"),
]

def room_entries():
    rows = [(k, emo, label, desc, False) for k, emo, label, desc in ROOM_SERVICES]
    for a_ in ADMIN_LOGS:
        rows.append((f"alog_{a_['key']}", a_["emoji"], f"لوق {a_['label']}", f"لوق أوامر {a_['label']} الإدارية", True))
    return rows

def room_current(guild, key):
    if key.startswith("alog_"):
        return alog_channel(guild, key[5:])
    if key == "events_channel":
        return events_channel(guild)
    return get_channel(guild, key, NAMES_BY_KEY[key])

def rooms_embed(guild, selected=None, note=None):
    CUR_GUILD.set(guild)
    head = ("حدد وين ينرسل كل شي بالسيرفر 👇\n"
            "**①** اختر الخدمة من القائمة الأولى\n**②** اختر الروم من القائمة الثانية (أو زر ➕ لإنشاء روم جديد)")
    if selected:
        lab = next((f"{emo} {label}" for k, emo, label, d, adm in room_entries() if k == selected), selected)
        head += f"\n\n🎯 **الخدمة المختارة:** {lab}"
    if note:
        head += f"\n{note}"
    e = E("📍 لوحة ضبط الرومات", head, PURPLE)
    main, logs = [], []
    for key, emo, label, desc, adm in room_entries():
        ch = room_current(guild, key)
        line = f"{'▶️' if key == selected else '▫️'} {emo} **{label}** — {ch.mention if ch else '❌ غير مضبوط'}"
        (logs if adm else main).append(line)
    e.add_field(name="📌 الخدمات الأساسية", value="\n".join(main), inline=False)
    e.add_field(name="🛡️ لوقات الإدارة (لكل أمر لوق مستقل)", value="\n".join(logs)[:1024], inline=False)
    if get_channel(guild, "level_channel", LEVEL_NAMES) is None:
        e.add_field(name="⚠️ تنبيه", value="روم اللفلات غير مضبوط — تهنئة الارتقاء تنرسل بنفس روم الكتابة.", inline=False)
    e.add_field(name="⌨️ بالكتابة", value="`ضبط ترحيب #روم` • `ضبط لفل #روم` • `ضبط لوق انشاء` • `ضبط لفل حذف`", inline=False)
    return e

class RoomServiceSelect(discord.ui.Select):
    def __init__(self):
        opts = [discord.SelectOption(label=label[:100], value=key, emoji=emo, description=desc[:100])
                for key, emo, label, desc, adm in room_entries()][:25]
        super().__init__(placeholder="① اختر الخدمة", options=opts, row=0)

    async def callback(self, interaction):
        self.view.selected = self.values[0]
        await interaction.response.edit_message(embed=rooms_embed(interaction.guild, self.view.selected), view=self.view)

class RoomChannelSelect(discord.ui.ChannelSelect):
    def __init__(self):
        super().__init__(placeholder="② اختر الروم", channel_types=[discord.ChannelType.text],
                         min_values=1, max_values=1, row=1)

    async def callback(self, interaction):
        v = self.view
        if not v.selected:
            return await interaction.response.send_message("☝️ اختر الخدمة أولاً من القائمة الأولى.", ephemeral=True)
        ch = interaction.guild.get_channel(self.values[0].id)
        if ch is None:
            return await interaction.response.send_message("❌ ما قدرت أوصل لهذا الروم.", ephemeral=True)
        db.cfg(interaction.guild.id)[v.selected] = ch.id
        db.mark()
        await interaction.response.edit_message(embed=rooms_embed(interaction.guild, v.selected, f"✅ تم الربط على {ch.mention}"), view=v)

class RoomsView(discord.ui.View):
    def __init__(self, author_id):
        super().__init__(timeout=300)
        self.author_id, self.selected, self.message = author_id, None, None
        self.add_item(RoomServiceSelect())
        self.add_item(RoomChannelSelect())

    async def interaction_check(self, interaction):
        CUR_GUILD.set(interaction.guild)
        if interaction.user.id == self.author_id and is_admin(interaction.user):
            return True
        await interaction.response.send_message("❌ هذي اللوحة للأدمن اللي فتحها، اكتب `ضبط` لتفتح لوحتك.", ephemeral=True)
        return False

    @discord.ui.button(label="إنشاء روم جديد", emoji="➕", style=discord.ButtonStyle.success, row=2)
    async def create_room(self, interaction, button):
        guild = interaction.guild
        if not self.selected:
            return await interaction.response.send_message("☝️ اختر الخدمة أولاً.", ephemeral=True)
        if not guild.me.guild_permissions.manage_channels:
            return await interaction.response.send_message("❌ أحتاج صلاحية **Manage Channels**.", ephemeral=True)
        await interaction.response.defer()
        entry = ALOG_BY_KEY.get(self.selected[5:]) if self.selected.startswith("alog_") else None
        try:
            ch = await create_log_channel(guild, entry) if entry else await create_plain_channel(guild, self.selected)
        except discord.HTTPException:
            return await interaction.followup.send("❌ تعذر إنشاء الروم.", ephemeral=True)
        db.cfg(guild.id)[self.selected] = ch.id
        db.mark()
        await interaction.edit_original_response(embed=rooms_embed(guild, self.selected, f"✅ تم إنشاء وربط {ch.mention}"), view=self)

    @discord.ui.button(label="إلغاء الربط", emoji="🗑️", style=discord.ButtonStyle.danger, row=2)
    async def unlink_room(self, interaction, button):
        if not self.selected:
            return await interaction.response.send_message("☝️ اختر الخدمة أولاً.", ephemeral=True)
        db.cfg(interaction.guild.id).pop(self.selected, None)
        db.mark()
        await interaction.response.edit_message(embed=rooms_embed(interaction.guild, self.selected, "🗑️ تم إلغاء الربط (الروم نفسه ما انحذف)."), view=self)

    @discord.ui.button(label="إغلاق", emoji="✖️", style=discord.ButtonStyle.secondary, row=2)
    async def close_panel(self, interaction, button):
        self.stop()
        await interaction.response.edit_message(view=None)

    async def on_timeout(self):
        if self.message:
            try:
                await self.message.edit(view=None)
            except discord.HTTPException:
                pass

async def send_rooms_panel(ctx):
    view = RoomsView(ctx.author.id)
    view.message = await ctx.send(embed=rooms_embed(ctx.guild), view=view)

@bot.command(name="ضبط")
@commands.guild_only()
@admin_only()
async def set_channel(ctx, kind: str = None, *, rest: str = ""):
    if kind is None:
        return await send_rooms_panel(ctx)
    await apply_channel_setting(ctx, kind, rest)

def _make_setter(kind):
    @bot.command(name=f"ضبط_{kind}")
    @commands.guild_only()
    @admin_only()
    async def _setter(ctx, *, rest: str = ""):
        await apply_channel_setting(ctx, kind, rest)
    return _setter

for _k in list(CHANNEL_KINDS) + list(ALOG_BY_NAME):
    _make_setter(_k)

@bot.command(name="سجلات", aliases=["لوقات_الادارة", "حالة_اللوقات"])
@commands.guild_only()
@admin_only()
async def logs_status(ctx):
    rows = []
    for e0 in ADMIN_LOGS:
        ch = alog_channel(ctx.guild, e0["key"])
        rows.append(f"{e0['emoji']} **{e0['label']}** (`ضبط_{e0['name']}`) — {ch.mention if ch else '❌ غير مضبوط'}")
    await ctx.send(embed=E("📜 لوقات أوامر الإدارة", "\n".join(rows) + "\n\n`تجهيز لوغات` ينشئها كلها • `ضبط_حظر #روم` يربط روماً موجوداً • `ضبط_حظر انشاء` ينشئ جديداً • `ضبط_حظر حذف` يلغي الربط", PURPLE))

@bot.after_invoke
async def _admin_log_hook(ctx):
    """يسجل كل أمر إداري ناجح بلوقه الخاص (إن كان مضبوطاً)."""
    try:
        if ctx.guild is None or ctx.command is None or getattr(ctx, "command_failed", False):
            return
        name = ctx.command.name
        kind = ADMIN_CMD_KIND.get(name) or ("settings" if name.startswith("ضبط") else None)
        if not kind:
            return
        ch = alog_channel(ctx.guild, kind)
        if ch is None:
            return
        entry = ALOG_BY_KEY[kind]
        e = discord.Embed(title=f"{entry['emoji']} {entry['label']} — {name}", color=entry["color"], timestamp=discord.utils.utcnow())
        e.add_field(name="👮 المنفذ", value=f"{ctx.author.mention}\n`{ctx.author.id}`", inline=True)
        e.add_field(name="📍 الروم", value=f"<#{ctx.channel.id}>", inline=True)
        targets = [m.mention for m in ctx.message.mentions] + [r.mention for r in ctx.message.role_mentions]
        if targets:
            e.add_field(name="🎯 الهدف", value=" ".join(targets)[:1000], inline=False)
        e.add_field(name="⌨️ الأمر", value=f"```{(ctx.message.content or '').replace('`', chr(39))[:900]}```", inline=False)
        e.set_author(name=str(ctx.author), icon_url=ctx.author.display_avatar.url)
        e.set_footer(text=f"{brand(ctx.guild)[0]} ADMIN LOGS")
        await ch.send(embed=e, allowed_mentions=discord.AllowedMentions.none())
    except Exception as ex:
        print(f"[ALOG] {ex!r}")

# ───────────────────────── التعرف على رتب الإدارة (حسب الصلاحيات لا الأسماء) ─────────────────────────
STAFF_PERMS = ("ban_members", "kick_members", "manage_messages", "moderate_members", "manage_roles", "manage_channels", "manage_guild")

def detect_staff(guild):
    cfg = staff_cfg(guild)
    high, mod = [], []
    for r in sorted(guild.roles, key=lambda r: -r.position):
        if r.is_default() or r.managed:
            continue
        p = r.permissions
        if p.administrator or r.id in cfg.get("high", []):
            high.append(r)
        elif r.id in cfg.get("mod", []) or any(getattr(p, x, False) for x in STAFF_PERMS):
            mod.append(r)
    return high, mod

@bot.command(name="الادارة", aliases=["الإدارة", "رتب_الادارة"])
@commands.guild_only()
@admin_only()
async def staff_cmd(ctx):
    high, mod = detect_staff(ctx.guild)
    fmt = lambda rs: " ".join(r.mention for r in rs[:25]) or "—"
    e = E("🛡️ رتب الإدارة بهذا السيرفر",
          "أتعرف عليها من **صلاحياتها** مو من أسمائها، فتشتغل مهما كانت التسمية.\n"
          "`تعيين_ادارة عليا @رتبة` • `تعيين_ادارة عادية @رتبة` • `حذف_ادارة @رتبة` لتعديل التصنيف يدوياً.", PURPLE)
    e.add_field(name="👑 الإدارة العليا", value=fmt(high), inline=False)
    e.add_field(name="🛡️ الإدارة العادية", value=fmt(mod), inline=False)
    await ctx.send(embed=e)

@bot.command(name="تعيين_ادارة", aliases=["تعيين_الادارة"])
@commands.guild_only()
@admin_only()
async def set_staff_role(ctx, level: str, *, role: discord.Role):
    k = {"عليا": "high", "العليا": "high", "عادية": "mod", "عاديه": "mod", "مشرف": "mod"}.get(level)
    if not k or role.is_default() or role.managed:
        return await ctx.reply("الاستخدام: `تعيين_ادارة عليا|عادية @الرتبة`")
    cfg = db.cfg(ctx.guild.id).setdefault("staff", {})
    other = "mod" if k == "high" else "high"
    cfg.setdefault(k, [])
    cfg.setdefault(other, [])
    if role.id in cfg[other]:
        cfg[other].remove(role.id)
    if role.id not in cfg[k]:
        cfg[k].append(role.id)
    db.mark()
    await ctx.send(f"✅ {role.mention} صارت **{'إدارة عليا' if k == 'high' else 'إدارة عادية'}** بهذا السيرفر.",
                   allowed_mentions=discord.AllowedMentions.none())

@bot.command(name="حذف_ادارة")
@commands.guild_only()
@admin_only()
async def del_staff_role(ctx, *, role: discord.Role):
    cfg = db.cfg(ctx.guild.id).setdefault("staff", {})
    for k in ("high", "mod"):
        if role.id in cfg.get(k, []):
            cfg[k].remove(role.id)
    db.mark()
    await ctx.send(f"🗑️ شلت التصنيف اليدوي عن {role.mention}.", allowed_mentions=discord.AllowedMentions.none())

# ───────────────────────── هيكل السيرفر: أقسام + رومات (إنشاء / تسمية / حذف) ─────────────────────────
CAT_RE = re.compile(r"^(?:(?:قسم|category)\s*[:：]\s*(.+)|قسم\s+(.+))$", re.I)
VOICE_KEEP = ("🔊",)
VOICE_STRIP = ("فويس:", "صوت:", "voice:")
TEXT_STRIP = ("نص:", "text:", "#")

def parse_layout(text):
    """سطور الرسالة ← [(اسم القسم أو None, [(نوع, اسم)])] بنفس الترتيب."""
    groups = [(None, [])]
    for raw in (text or "").replace("\r", "").split("\n"):
        line = raw.strip()
        if not line:
            continue
        m = CAT_RE.match(line)
        if m:
            groups.append(((m.group(1) or m.group(2)).strip()[:100], []))
            continue
        kind, low = "text", line.lower()
        if any(low.startswith(p) for p in VOICE_KEEP):
            kind = "voice"
        else:
            for p in VOICE_STRIP:
                if low.startswith(p):
                    kind, line = "voice", line[len(p):].strip()
                    break
            else:
                for p in TEXT_STRIP:
                    if low.startswith(p):
                        line = line[len(p):].strip()
                        break
        if line:
            groups[-1][1].append((kind, line[:100]))
    if not groups[0][1]:
        groups.pop(0)
    return groups

def parse_names(text):
    return [l.strip() for l in (text or "").replace("\r", "").split("\n") if l.strip()]

def ordered_categories(guild):
    return sorted(guild.categories, key=lambda c: c.position)

def ordered_channels(guild):
    return [ch for _, chans in guild.by_category() for ch in chans]

def numbered(objs, limit=3800):
    out, n = [], 0
    for i, o in enumerate(objs, 1):
        line = f"`{i}.` {o.name}"
        n += len(line) + 1
        if n > limit:
            out.append("…")
            break
        out.append(line)
    return "\n".join(out) or "—"

async def run_renames(ctx, pairs, label, notes=""):
    guild = ctx.guild
    if not guild.me.guild_permissions.manage_channels:
        return await ctx.reply("❌ أحتاج صلاحية **Manage Channels**.")
    msg = await ctx.send(embed=E(f"✏️ جاري تغيير أسماء {label}...", f"العدد: **{len(pairs)}**", PURPLE))
    done = skipped = failed = 0
    lines = []
    QUIET.add(guild.id)
    try:
        for obj, new in pairs:
            if new == "-" or new == obj.name:
                skipped += 1
                continue
            old = obj.name
            try:
                await obj.edit(name=new[:100], reason=f"Bot rename by {ctx.author}")
                done += 1
                lines.append(f"`{old}` ➜ `{new[:100]}`")
            except discord.HTTPException:
                failed += 1
            await asyncio.sleep(0.5)
    finally:
        QUIET.discard(guild.id)
    body = (f"✅ تغيّر: **{done}** • ⏭️ تخطي: **{skipped}** • ⚠️ فشل: **{failed}**\n" + notes + "\n\n"
            + "\n".join(lines[:20]))[:4000]
    await msg.edit(embed=E(f"✅ تمت تسمية {label}", body, 0x2ECC71))

@bot.command(name="اسماء_الاقسام", aliases=["تسمية_الاقسام", "اسماء_اقسام"])
@commands.guild_only()
@admin_only()
async def rename_categories(ctx, *, text: str = ""):
    cats = ordered_categories(ctx.guild)
    names = parse_names(text)
    if not names:
        return await ctx.send(embed=E("🗂️ الأقسام الحالية (بالترتيب)", numbered(cats) +
                              "\n\nاكتب الأمر ثم الأسماء الجديدة **سطر لكل قسم بنفس الترتيب** (الزخرفة مسموحة)، و`-` لترك اسم قسم كما هو.\n"
                              "```اسماء_الاقسام\n✦━ معلومات ━✦\n✦━ الفويس ━✦```", PURPLE))
    notes = ""
    if len(names) > len(cats):
        notes += f"⚠️ زيادة **{len(names) - len(cats)}** اسم تجاهلتها (عدد الأقسام {len(cats)}).\n"
    if len(names) < len(cats):
        notes += f"ℹ️ بقيت **{len(cats) - len(names)}** أقسام بدون تغيير.\n"
    await run_renames(ctx, list(zip(cats, names)), "الأقسام", notes)

@bot.command(name="اسماء_الرومات", aliases=["تسمية_الرومات", "اسماء_رومات"])
@commands.guild_only()
@admin_only()
async def rename_channels(ctx, *, text: str = ""):
    chans = ordered_channels(ctx.guild)
    names = parse_names(text)
    if not names:
        return await ctx.send(embed=E("💬 الرومات الحالية (بترتيب ظهورها)", numbered(chans) +
                              "\n\nاكتب الأمر ثم الأسماء الجديدة **سطر لكل روم بنفس الترتيب** (كتابي وصوتي، قسماً بعد قسم)، و`-` لترك الاسم.", PURPLE))
    notes = ""
    if len(names) > len(chans):
        notes += f"⚠️ زيادة **{len(names) - len(chans)}** اسم تجاهلتها (عدد الرومات {len(chans)}).\n"
    if len(names) < len(chans):
        notes += f"ℹ️ بقيت **{len(chans) - len(names)}** رومات بدون تغيير.\n"
    await run_renames(ctx, list(zip(chans, names)), "الرومات", notes)

LAYOUT_USAGE = ("اكتب الأقسام والرومات **برسالة واحدة** بالترتيب اللي تريده:\n"
                "```انشاء_هيكل\nقسم: ✦━ معلومات ━✦\n📜・القوانين\n📢・الاعلانات\n"
                "قسم: ✦━ الفويس ━✦\n🔊・عام\nفويس: سوالف```\n"
                "• السطر اللي يبدأ بـ `قسم:` = قسم جديد • الروم الكتابي سطر عادي\n"
                "• الصوتي يبدأ بـ `🔊` أو `فويس:` • الزخرفة مسموحة بكل الأسماء")

@bot.command(name="انشاء_هيكل", aliases=["انشاء_رومات", "انشاء_اقسام", "هيكل"])
@commands.guild_only()
@admin_only()
async def build_layout(ctx, *, text: str = ""):
    groups = parse_layout(text)
    if not groups:
        return await ctx.send(embed=E("🏗️ إنشاء الهيكل", LAYOUT_USAGE, PURPLE))
    guild = ctx.guild
    if not guild.me.guild_permissions.manage_channels:
        return await ctx.reply("❌ أحتاج صلاحية **Manage Channels**.")
    total = sum(len(c) for _, c in groups) + sum(1 for n, _ in groups if n)
    if total > 200 or len(guild.channels) + total > 500:
        return await ctx.reply(f"❌ العدد كبير ({total}). الحد 200 بالمرة و500 بالسيرفر.")
    if any(len(c) > 50 for _, c in groups):
        return await ctx.reply("❌ القسم الواحد ما يسع أكثر من 50 روم.")
    msg = await ctx.send(embed=E("🏗️ جاري إنشاء الهيكل...", f"عدد العناصر: **{total}**", PURPLE))
    cats = chans = 0
    err = ""
    QUIET.add(guild.id)
    try:
        for cat_name, items in groups:
            cat = None
            if cat_name:
                cat = await guild.create_category(cat_name, reason=f"Bot layout by {ctx.author}")
                cats += 1
                await asyncio.sleep(0.4)
            for kind, name in items:
                if kind == "voice":
                    await guild.create_voice_channel(name, category=cat, reason=f"Bot layout by {ctx.author}")
                else:
                    await guild.create_text_channel(name, category=cat, reason=f"Bot layout by {ctx.author}")
                chans += 1
                await asyncio.sleep(0.4)
    except discord.Forbidden:
        err = "\n❌ توقفت: صلاحيات ناقصة."
    except discord.HTTPException as ex:
        err = f"\n❌ توقفت بسبب خطأ: `{str(ex)[:150]}`"
    finally:
        QUIET.discard(guild.id)
    await msg.edit(embed=E("✅ تم إنشاء الهيكل" if not err else "⚠️ إنشاء جزئي",
                           f"🗂️ أقسام: **{cats}** • 💬 رومات: **{chans}**{err}", 0x2ECC71 if not err else 0xE67E22))

@bot.command(name="تسمية_الهيكل", aliases=["اعادة_تسمية"])
@commands.guild_only()
@admin_only()
async def rename_layout(ctx, *, text: str = ""):
    """يعيد تسمية الأقسام والرومات الموجودة (برسالة واحدة) بنفس ترتيبها."""
    groups = parse_layout(text)
    if not groups:
        return await ctx.send(embed=E("✏️ تسمية الهيكل الحالي", "نفس صيغة `انشاء_هيكل` لكنها **تعيد تسمية الموجود** بنفس الترتيب (قسماً قسماً ثم رومات كل قسم) "
                              "بدل ما تنشئ جديد. علامات الصوتي/الكتابي تُهمل هنا.\n" + LAYOUT_USAGE.replace("انشاء_هيكل", "تسمية_الهيكل"), PURPLE))
    ex_uncat, ex_cats = [], []
    for cat, chans in ctx.guild.by_category():
        if cat is None:
            ex_uncat = chans
        else:
            ex_cats.append((cat, chans))
    it = iter(ex_cats)
    pairs, missing = [], 0
    for cat_name, items in groups:
        if cat_name is None:
            targets = ex_uncat
        else:
            nxt = next(it, None)
            if nxt is None:
                missing += 1 + len(items)
                continue
            pairs.append((nxt[0], cat_name))
            targets = nxt[1]
        missing += max(0, len(items) - len(targets))
        pairs.extend((ch, nm) for (_, nm), ch in zip(items, targets))
    notes = f"ℹ️ **{missing}** عنصر ما له مقابل موجود (استخدم `انشاء_هيكل` لإضافته).\n" if missing else ""
    await run_renames(ctx, pairs, "الهيكل", notes)

class ConfirmView(discord.ui.View):
    def __init__(self, author_id, timeout=30):
        super().__init__(timeout=timeout)
        self.author_id, self.ok = author_id, None

    async def interaction_check(self, interaction):
        if interaction.user.id == self.author_id:
            return True
        await interaction.response.send_message("❌ هذا التأكيد مو إلك.", ephemeral=True)
        return False

    @discord.ui.button(label="تأكيد الحذف", emoji="💥", style=discord.ButtonStyle.danger)
    async def yes(self, interaction, button):
        self.ok = True
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(label="إلغاء", emoji="✖️", style=discord.ButtonStyle.secondary)
    async def no(self, interaction, button):
        self.ok = False
        await interaction.response.defer()
        self.stop()

@bot.command(name="حذف_الهيكل", aliases=["حذف_كل_الرومات", "حذف_الكل"])
@commands.guild_only()
@admin_only()
async def wipe_layout(ctx):
    guild = ctx.guild
    if not guild.me.guild_permissions.manage_channels:
        return await ctx.reply("❌ أحتاج صلاحية **Manage Channels**.")
    targets = [c for c in guild.channels if c.id != ctx.channel.id]
    cats = sum(isinstance(c, discord.CategoryChannel) for c in targets)
    view = ConfirmView(ctx.author.id)
    msg = await ctx.send(embed=E("⚠️ تأكيد حذف كل الأقسام والرومات",
                                 f"راح أحذف **{len(targets) - cats}** روم و **{cats}** قسم.\n"
                                 f"هذا الروم ({ctx.channel.mention}) راح يبقى حتى أكتب لك النتيجة وتبني الهيكل الجديد.\n"
                                 "**هذا الإجراء ما ينعاد!** عندك 30 ثانية.", 0xE74C3C), view=view)
    await view.wait()
    for c in view.children:
        c.disabled = True
    if not view.ok:
        return await msg.edit(embed=E("✖️ انلغى الحذف", "ما انحذف شي.", 0x95A5A6), view=view)
    await msg.edit(embed=E("💥 جاري الحذف...", "لحظات.", 0xE74C3C), view=view)
    await log_event(guild, "💥 حذف الهيكل", f"{ctx.author.mention} حذف كل الأقسام والرومات ({len(targets)}).", "red")
    deleted_ids, failed = set(), 0
    QUIET.add(guild.id)
    try:
        for c in sorted(targets, key=lambda c: isinstance(c, discord.CategoryChannel)):
            try:
                await c.delete(reason=f"Bot wipe by {ctx.author}")
                deleted_ids.add(c.id)
            except discord.HTTPException:
                failed += 1
            await asyncio.sleep(0.4)
    finally:
        QUIET.discard(guild.id)
    cfg = db.cfg(guild.id)
    for k, v in list(cfg.items()):
        if isinstance(v, int) and v in deleted_ids and (k.endswith("_channel") or k.startswith("alog_")):
            cfg.pop(k, None)
    db.mark()
    await ctx.channel.send(embed=E("✅ تم الحذف", f"🗑️ انحذف **{len(deleted_ids)}** • ⚠️ فشل **{failed}** "
                                   "(قنوات القواعد/التحديثات بسيرفرات المجتمع ما تنحذف).\n"
                                   "ابنِ الهيكل الجديد بـ `انشاء_هيكل` ثم `تجهيز لوغات`.", 0x2ECC71))

HELP_SECTIONS["structure"] = ("🏗️", "الهيكل واللوقات والإدارة", "تسمية/إنشاء/حذف الأقسام والرومات، لوق لكل أمر إداري، رتب الإدارة.", [
    "🏗️ الأقسام والرومات (إدارة عليا فقط)",
    ("اسماء_الاقسام", "اسماء_الاقسام ثم الأسماء سطر لكل قسم", "يغيّر أسماء كل الأقسام بنفس الترتيب اللي تكتبه (مع الزخرفة). بدون أسماء يعرض الحالية."),
    ("اسماء_الرومات", "اسماء_الرومات ثم الأسماء سطر لكل روم", "يغيّر أسماء كل الرومات (كتابي وصوتي) بنفس الترتيب."),
    ("تسمية_الهيكل", "تسمية_الهيكل + قسم: ... + رومات", "أقسام ورومات بالزخرفة برسالة واحدة تُطبَّق على الموجود بنفس الترتيب."),
    ("انشاء_هيكل", "انشاء_هيكل + قسم: ... + رومات", "ينشئ الأقسام والرومات اللي تختارها برسالة واحدة (🔊 أو فويس: للصوتي)."),
    ("حذف_الهيكل", "حذف_الهيكل", "يحذف كل الأقسام والرومات بأمر واحد بعد تأكيد."),
    "📜 لوقات الإدارة",
    ("سجلات", "سجلات", "يعرض لوق كل أمر إداري (حظر، طرد، ميوت، تحذير، مسح، قفل، رتب، مستوى، طوارئ، اعلان، هيكل، اعدادات)."),
    ("ضبط_حظر", "ضبط_<النوع> #روم | انشاء | حذف", "يربط لوق الأمر بروم موجود، أو ينشئ روماً جديداً، أو يلغي اللوق. نفس الشي لـ ضبط_ترحيب وضبط_لفل..."),
    ("تجهيز", "تجهيز [رتب|رومات|لوغات|حماية]", "تجهيز اختياري: كل الأجزاء أو اللي تحددها، ويُنشئ لوق لكل أمر إداري."),
    "🛡️ رتب الإدارة",
    ("الادارة", "الادارة", "يعرض رتب الإدارة العليا والعادية اللي عرفها البوت من الصلاحيات (مهما كانت أسماؤها)."),
    ("تعيين_ادارة", "تعيين_ادارة عليا|عادية @رتبة", "تصنيف يدوي لرتبة إدارة بهذا السيرفر. `حذف_ادارة @رتبة` لإلغائه."),
])

@bot.command(name="حماية")
@commands.guild_only()
@admin_only()
async def protection_cmd(ctx, kind: str = None):
    cfg = db.cfg(ctx.guild.id)
    mapping = {"رابط": "antilink", "روابط": "antilink", "سبام": "antispam"}
    if kind in mapping:
        cfg[mapping[kind]] = not cfg[mapping[kind]]
        db.mark()
    e = E("🛡️ نظام الحماية", color=0x3498DB)
    e.add_field(name="🔗 منع روابط الدعوات", value="🟢 شغّال" if cfg["antilink"] else "🔴 مطفي", inline=True)
    e.add_field(name="💥 منع السبام", value="🟢 شغّال" if cfg["antispam"] else "🔴 مطفي", inline=True)
    await ctx.send(embed=e)

def valid_media_key(key):
    key = key or ""
    return key in MEDIA_LABELS or key == "help_home" or (key.startswith("help_") and key[5:] in HELP_SECTIONS)

@bot.command(name="صور")
@commands.guild_only()
@admin_only()
async def media_list(ctx):
    lines = [f"{'🟢' if k in MEDIA_CACHE else '⚪'} `{k}` — {l}" for k, l in MEDIA_LABELS.items()]
    e = E("🖼️ مفاتيح الصور", "\n".join(lines)[:3800])
    e.add_field(name="📚 صور أقسام المساعدة", inline=False,
                value="`help_home` للرئيسية • `help_<القسم>` مثل `help_mod` `help_levels` `help_voice` `help_tools`\n"
                      "بدونها يتولّد لكل قسم بنر تلقائي بلونه وعدد أوامره.")
    await ctx.send(embed=e)

@bot.command(name="صورة", aliases=["صوره"])
@commands.guild_only()
@admin_only()
async def media_set(ctx, key: str = None, url: str = None):
    if key in ("حذف", "delete") and url:
        media_remove(url)
        return await ctx.send(f"🗑️ تم حذف صورة `{url}`.")
    if not valid_media_key(key):
        return await ctx.reply("الاستخدام: `!صورة المفتاح رابط` — اكتب `صور` لتشوف المفاتيح.")
    att = ctx.message.attachments[0] if ctx.message.attachments else None
    if att:
        data, src = await att.read(), None
    elif url:
        data, src = await fetch_bytes(url), url
    else:
        return await ctx.reply("حط رابط مباشر أو أرفق صورة.")
    if not data or not media_install(key, data):
        return await ctx.reply("❌ رابط غير صالح أو صيغة غير مدعومة.")
    if src:
        db.data["_media"][key] = src
    db.mark()
    e = E("✅ تم حفظ الصورة", f"`{key}`")
    f = attach_media(e, key)
    await ctx.send(embed=e, files=files_of(f))

# ───────────────────────── رسائل الخاص (DM) ─────────────────────────
async def dm_notice(user, title, text, color):
    try:
        await user.send(embed=E(title, text, color))
        return True
    except (discord.Forbidden, discord.HTTPException):
        return False

# ───────────────────────── حذف رتبة ─────────────────────────
@bot.command(name="حذف_رتبة", aliases=["حذف_رتبه"])
@commands.guild_only()
@staff_perms(manage_roles=True)
async def delete_role_cmd(ctx, *, role: discord.Role):
    if role.is_default() or role.managed:
        return await ctx.reply("❌ هذي الرتبة ما تنحذف (أساسية أو خاصة ببوت).")
    if ctx.author.id != ctx.guild.owner_id and role >= ctx.author.top_role:
        return await ctx.reply("❌ الرتبة أعلى من رتبتك أو مساوية.")
    if ctx.guild.me and role >= ctx.guild.me.top_role:
        return await ctx.reply("❌ رتبة البوت لازم تكون أعلى من الرتبة المطلوبة.")
    name = role.name
    await role.delete(reason=f"حذف بواسطة {ctx.author}")
    await ctx.send(embed=E("🗑️ تم حذف الرتبة", f"`{name}` بواسطة {ctx.author.mention}", 0xE74C3C))
    await log_event(ctx.guild, "🗑️ حذف رتبة بأمر", f"{ctx.author.mention} حذف `{name}`", "red")

# ───────────────────────── هوية البوت لكل سيرفر ─────────────────────────
@bot.command(name="تعيين_اسم", aliases=["تعيين_اسم_البوت", "اسم_البوت", "سمي", "سمّي"])
@commands.guild_only()
@admin_only()
async def set_bot_name(ctx, *, name: str = ""):
    """أونر/إدارة السيرفر يسمّي البوت. البوت يعتمد هذا الاسم بكل مكان، وإذا أحد سأله «شنو اسمك» يجاوب به."""
    name = re.sub(r"\s+", " ", name.replace("@", "＠")).strip()[:32]
    cfg = db.cfg(ctx.guild.id)
    if not name:
        cur = cfg.get("bot_name")
        txt = (f"اسم البوت الحالي: **{cur}**" if cur else "البوت بدون اسم حالياً.")
        return await ctx.send(embed=E("🏷️ اسم البوت", f"{txt}\n\nللتسمية: `تعيين_اسم يوتا`\nللإزالة: `تعيين_اسم ازالة`"))
    note = ""
    if name in ("ازالة", "إزالة", "حذف", "reset", "مسح"):
        cfg.pop("bot_name", None)
        db.mark()
        try:
            await ctx.guild.me.edit(nick=None)
        except discord.HTTPException:
            pass
        return await ctx.send(embed=E("✅ تمت إزالة الاسم", "رجع البوت بدون اسم، ويقدر الأونر يسميه بأي وقت."))
    cfg["bot_name"] = name
    db.mark()
    try:
        await ctx.guild.me.edit(nick=name)
    except discord.HTTPException:
        note = "\n⚠️ ما قدرت أغيّر اللقب، تأكد من صلاحية **Change Nickname**."
    await ctx.send(embed=E("✅ تم تسمية البوت", f"اسم البوت بهذا السيرفر صار **{name}**.\n"
                           f"إذا سألوه «شنو اسمك؟» يجاوب بهذا الاسم، وتستخدمه رسائل الترحيب واللفل والإيمبدات، "
                           f"وبقية السيرفرات ما تتأثر.{note}"))

@bot.command(name="تعيين_بايو")
@commands.guild_only()
@admin_only()
async def set_bot_bio(ctx, *, text: str = ""):
    text = text.strip()[:190]
    if not text:
        return await ctx.reply("الاستخدام: `تعيين_بايو نص البايو`")
    db.cfg(ctx.guild.id)["bot_bio"] = text
    db.mark()
    try:
        await ctx.guild.me.edit(bio=text)
    except (TypeError, discord.HTTPException):
        pass
    await ctx.send(embed=E("✅ تم ضبط البايو", text))

@bot.command(name="تعيين_افتار", aliases=["تعيين_صورة"])
@commands.guild_only()
@admin_only()
async def set_bot_avatar(ctx, url: str = None):
    att = ctx.message.attachments[0] if ctx.message.attachments else None
    src = att.url if att else url
    if not src or urlparse(src).scheme not in ("http", "https"):
        return await ctx.reply("الاستخدام: `تعيين_افتار رابط_الصورة` أو أرفق صورة مع الأمر.")
    data = await att.read() if att else await fetch_bytes(src)
    if not data or not sniff_ext(data):
        return await ctx.reply("❌ الصورة غير صالحة.")
    db.cfg(ctx.guild.id)["bot_avatar"] = src
    db.mark()
    try:
        await ctx.guild.me.edit(avatar=data)
    except (TypeError, discord.HTTPException):
        pass
    await ctx.send(embed=E("✅ تم ضبط صورة البوت", "ستظهر في إيمبدات هذا السيرفر."))

@bot.command(name="اعادة_هوية", aliases=["إعادة_هوية"])
@commands.guild_only()
@admin_only()
async def reset_identity(ctx):
    cfg = db.cfg(ctx.guild.id)
    for k in ("bot_name", "bot_bio", "bot_avatar"):
        cfg.pop(k, None)
    db.mark()
    try:
        await ctx.guild.me.edit(nick=None)
    except discord.HTTPException:
        pass
    await ctx.send(embed=E("♻️ تمت إعادة الهوية", "رجع البوت لهويته الافتراضية بهذا السيرفر."))

@bot.command(name="هوية", aliases=["هويه"])
@commands.guild_only()
async def identity_cmd(ctx):
    name, avatar, bio = brand(ctx.guild)
    e = E(f"🪪 هوية البوت — {name}", bio or "ما في بايو مضبوط.", PURPLE)
    if avatar:
        e.set_thumbnail(url=avatar)
    await ctx.send(embed=e)

# ───────────────────────── الجيفات والردود التلقائية ─────────────────────────
GIF_TYPES = {"ترحيب": "welcome", "لفل": "levelup", "ليفل": "levelup", "وداع": "farewell", "ودع": "farewell"}
_trigger_last = {}

def chat_triggers(gid):
    return db.data.setdefault("_chat", {}).setdefault(str(gid), {})

async def chat_trigger(message):
    trig = db.data.get("_chat", {}).get(str(message.guild.id))
    if not trig or not message.content:
        return
    tokens = set(re.findall(r"[\w']+", message.content.lower()))
    for word, val in trig.items():
        if word not in tokens:
            continue
        k, now = (message.channel.id, word), time.time()
        if now - _trigger_last.get(k, 0) < 5:
            return
        _trigger_last[k] = now
        try:
            if val.get("media") and val["media"] in MEDIA_CACHE:
                data, fn = MEDIA_CACHE[val["media"]]
                await message.channel.send(file=discord.File(io.BytesIO(data), filename=fn))
            elif val.get("url"):
                await message.channel.send(val["url"])
        except discord.HTTPException:
            pass
        return

@bot.command(name="اضافة_جيف", aliases=["إضافة_جيف", "اضافه_جيف"])
@commands.guild_only()
@admin_only()
async def add_gif(ctx, kind: str = None, *, rest: str = ""):
    att = ctx.message.attachments[0] if ctx.message.attachments else None
    parts = rest.split()
    if kind in ("شات", "chat"):
        if not parts or not (att or len(parts) > 1):
            return await ctx.reply("الاستخدام: `اضافة_جيف شات يوتا رابط_الجيف` (أو أرفق الجيف).")
        word = parts[0].lower()
        triggers = chat_triggers(ctx.guild.id)
        old = triggers.get(word)
        if old and old.get("media"):
            media_remove(old["media"])
        if att:
            key = f"chat_{ctx.guild.id}_{zlib.crc32(word.encode())}"
            if not media_install(key, await att.read()):
                return await ctx.reply("❌ صيغة غير مدعومة (GIF / PNG / JPG / WEBP).")
            triggers[word] = {"media": key}
        else:
            if urlparse(parts[1]).scheme not in ("http", "https"):
                return await ctx.reply("❌ الرابط غير صالح.")
            triggers[word] = {"url": parts[1]}
        db.mark()
        return await ctx.send(embed=E("✅ تمت إضافة جيف الشات", f"أي أحد يكتب **{word}** بالشات يرسل البوت الجيف تلقائياً."))
    key = GIF_TYPES.get(kind or "")
    if not key:
        return await ctx.reply("الاستخدام: `اضافة_جيف [ترحيب|لفل|وداع] رابط` أو `اضافة_جيف شات كلمة رابط`")
    if att:
        data, src = await att.read(), None
    elif parts:
        data, src = await fetch_bytes(parts[0]), parts[0]
    else:
        return await ctx.reply("حط رابط مباشر أو أرفق الجيف.")
    if not data or not media_install(key, data):
        return await ctx.reply("❌ رابط غير صالح أو صيغة غير مدعومة.")
    if src:
        db.data["_media"][key] = src
    else:
        db.data["_media"].pop(key, None)
    db.mark()
    e = E("✅ تم ضبط الجيف", f"النوع: **{kind}**")
    f = attach_media(e, key)
    await ctx.send(embed=e, files=files_of(f))

@bot.command(name="حذف_جيف")
@commands.guild_only()
@admin_only()
async def delete_gif(ctx, kind: str = None, word: str = None):
    if kind in ("شات", "chat") and word:
        old = chat_triggers(ctx.guild.id).pop(word.lower(), None)
        if old and old.get("media"):
            media_remove(old["media"])
        db.mark()
        return await ctx.send("🗑️ تم حذف الرد." if old else "ما لقيت هذي الكلمة.")
    if kind in GIF_TYPES:
        media_remove(GIF_TYPES[kind])
        return await ctx.send(f"🗑️ تم حذف جيف **{kind}**.")
    await ctx.reply("الاستخدام: `حذف_جيف شات كلمة` أو `حذف_جيف [ترحيب|لفل|وداع]`")

@bot.command(name="الجيفات", aliases=["جيفات"])
@commands.guild_only()
@admin_only()
async def list_gifs(ctx):
    sysl = [f"{'🟢' if k in MEDIA_CACHE else '⚪'} {n}" for n, k in (("ترحيب", "welcome"), ("لفل", "levelup"), ("وداع", "farewell"))]
    trig = chat_triggers(ctx.guild.id)
    chat = "\n".join(f"• **{w}**" for w in trig) or "لا يوجد"
    e = E("🎞️ الجيفات والردود التلقائية", color=PURPLE)
    e.add_field(name="جيفات النظام", value="\n".join(sysl), inline=False)
    e.add_field(name="جيفات الشات", value=chat[:1000], inline=False)
    await ctx.send(embed=e)

# ───────────────────────── المتجر ─────────────────────────
def shop_items(gid):
    return db.data.setdefault("_shop", {}).setdefault(str(gid), [])

@bot.command(name="المتجر", aliases=["متجر", "shop"])
@commands.guild_only()
async def shop_cmd(ctx):
    items = shop_items(ctx.guild.id)
    lines = []
    for i, it in enumerate(items, 1):
        role = ctx.guild.get_role(it["role_id"])
        lines.append(f"**{i}_{it['name']}** — 💰 `{it['price']:,}` • {role.mention if role else '(رتبة محذوفة)'}")
    e = E("🛒 متجر المملكة", "\n".join(lines) or "المتجر فاضي حالياً.", GOLD)
    e.add_field(name="رصيدك", value=f"`{db.user(ctx.author.id)['coins']:,}` عملة", inline=False)
    e.add_field(name="طريقة الشراء", value="`شراء [رقم المنتج]`", inline=False)
    await ctx.send(embed=e)

@bot.command(name="شراء")
@commands.guild_only()
async def buy_cmd(ctx, number: int):
    items = shop_items(ctx.guild.id)
    if not 1 <= number <= len(items):
        return await ctx.reply("❌ رقم المنتج غير صحيح، شوف `المتجر`.")
    it = items[number - 1]
    role = ctx.guild.get_role(it["role_id"])
    if role is None:
        return await ctx.reply("❌ رتبة هذا المنتج انحذفت.")
    if role in ctx.author.roles:
        return await ctx.reply("✅ تملك هذي الرتبة مسبقاً.")
    if ctx.guild.me and role >= ctx.guild.me.top_role:
        return await ctx.reply("❌ رتبة البوت لازم تكون أعلى من رتبة المنتج.")
    u = db.user(ctx.author.id)
    if u["coins"] < it["price"]:
        return await ctx.reply(f"❌ رصيدك `{u['coins']:,}` ما يكفي (السعر `{it['price']:,}`).")
    u["coins"] -= it["price"]          # نخصم أولاً حتى ما تتكرر عملية الشراء أثناء الانتظار
    db.mark()
    try:
        await ctx.author.add_roles(role, reason="شراء من المتجر")
    except discord.HTTPException:
        u["coins"] += it["price"]      # فشل الإعطاء → نرجّع العملات
        db.mark()
        return await ctx.reply("❌ تعذر إعطاؤك الرتبة، رجعنا لك عملاتك.")
    await ctx.send(embed=E("✅ تمت عملية الشراء", f"اشتريت **{it['name']}** وحصلت على {role.mention}\nرصيدك: `{u['coins']:,}`", GOLD))

@bot.command(name="اضافة_منتج", aliases=["إضافة_منتج"])
@commands.guild_only()
@admin_only()
async def add_product(ctx, price: int, role: discord.Role, *, name: str = ""):
    name = name.strip() or role.name
    if price <= 0 or role.is_default() or role.managed:
        return await ctx.reply("الاستخدام: `اضافة_منتج 500 @رتبة اسم المنتج`")
    items = shop_items(ctx.guild.id)
    if len(items) >= 20:
        return await ctx.reply("❌ الحد الأقصى 20 منتجاً.")
    items.append({"name": name[:50], "price": price, "role_id": role.id})
    db.mark()
    await ctx.send(embed=E("✅ تمت إضافة المنتج", f"**{len(items)}_{name}** — `{price:,}` عملة → {role.mention}"))

@bot.command(name="حذف_منتج")
@commands.guild_only()
@admin_only()
async def delete_product(ctx, number: int):
    items = shop_items(ctx.guild.id)
    if not 1 <= number <= len(items):
        return await ctx.reply("❌ رقم غير صحيح.")
    it = items.pop(number - 1)
    db.mark()
    await ctx.send(f"🗑️ تم حذف المنتج **{it['name']}**.")

# ═════════════════════════ الفعاليات (جيفاواي • تذكير بالصلاة • رسائل تلقائية) ═════════════════════════
# (كان ضمن «قسم البوت الذكي»؛ حُذفت الدردشة والنماذج والرسم ووصف الصور وبقيت الفعاليات المفيدة)
ON_WORDS = ("تشغيل", "تفعيل", "شغل", "فعل", "on", "ON")
OFF_WORDS = ("ايقاف", "إيقاف", "اطفاء", "وقف", "تعطيل", "off", "OFF")

HADITHS = [
    ("إِنَّمَا الأَعْمَالُ بِالنِّيَّاتِ، وَإِنَّمَا لِكُلِّ امْرِئٍ مَا نَوَى", "متفق عليه"),
    ("لَا يُؤْمِنُ أَحَدُكُمْ حَتَّى يُحِبَّ لِأَخِيهِ مَا يُحِبُّ لِنَفْسِهِ", "متفق عليه"),
    ("الْكَلِمَةُ الطَّيِّبَةُ صَدَقَةٌ", "متفق عليه"),
    ("تَبَسُّمُكَ فِي وَجْهِ أَخِيكَ لَكَ صَدَقَةٌ", "رواه الترمذي"),
    ("خَيْرُكُمْ مَنْ تَعَلَّمَ الْقُرْآنَ وَعَلَّمَهُ", "رواه البخاري"),
    ("مَنْ كَانَ يُؤْمِنُ بِاللَّهِ وَالْيَوْمِ الْآخِرِ فَلْيَقُلْ خَيْرًا أَوْ لِيَصْمُتْ", "متفق عليه"),
    ("الدِّينُ النَّصِيحَةُ", "رواه مسلم"),
    ("اتَّقِ اللَّهَ حَيْثُمَا كُنْتَ، وَأَتْبِعِ السَّيِّئَةَ الْحَسَنَةَ تَمْحُهَا", "رواه الترمذي"),
]
AYAHS = [
    ("فَإِنَّ مَعَ الْعُسْرِ يُسْرًا ۝ إِنَّ مَعَ الْعُسْرِ يُسْرًا", "سورة الشرح: 5-6"),
    ("أَلَا بِذِكْرِ اللَّهِ تَطْمَئِنُّ الْقُلُوبُ", "سورة الرعد: 28"),
    ("فَاذْكُرُونِي أَذْكُرْكُمْ وَاشْكُرُوا لِي وَلَا تَكْفُرُونِ", "سورة البقرة: 152"),
    ("وَمَن يَتَوَكَّلْ عَلَى اللَّهِ فَهُوَ حَسْبُهُ", "سورة الطلاق: 3"),
    ("وَقُل رَّبِّ زِدْنِي عِلْمًا", "سورة طه: 114"),
    ("إِنَّ اللَّهَ مَعَ الصَّابِرِينَ", "سورة البقرة: 153"),
    ("ادْعُونِي أَسْتَجِبْ لَكُمْ", "سورة غافر: 60"),
    ("وَاصْبِرْ فَإِنَّ اللَّهَ لَا يُضِيعُ أَجْرَ الْمُحْسِنِينَ", "سورة هود: 115"),
    ("وَلَسَوْفَ يُعْطِيكَ رَبُّكَ فَتَرْضَى", "سورة الضحى: 5"),
    ("لَا يُكَلِّفُ اللَّهُ نَفْسًا إِلَّا وُسْعَهَا", "سورة البقرة: 286"),
]
FALLBACK_QUESTIONS = [
    "لو تگدر تسافر لأي بلد هسه، وين تروح؟ ✈️",
    "شنو أحسن أكلة عندك وما تمل منها؟ 🍽️",
    "لو عندك قوة خارقة وحدة، شنو تختار؟ 🦸",
    "شنو آخر لعبة أو مسلسل عجبك وتنصح بيه؟ 🎮",
    "صباحي لو ليلي؟ وليش؟ 🌙☀️",
    "شنو أغرب شي صار وياك هالأسبوع؟ 😅",
    "لو تفتح مشروع، شنو يكون؟ 💡",
]
CONGRATS = ("مبروك", "ألف مبروك", "عاش يا وحش", "كفو يا بطل", "تهانينا الحارة")
PRAYERS = (("Fajr", "الفجر"), ("Dhuhr", "الظهر"), ("Asr", "العصر"), ("Maghrib", "المغرب"), ("Isha", "العشاء"))
_prayer_cache = {}
_prayer_fail = {}

def ev_cfg(guild):
    # المفتاح القديم "ai" محفوظ كما هو حتى تبقى إعدادات السيرفرات الحالية شغالة بدون ضياع
    return db.cfg(guild.id).setdefault("ai", {})

def events_channel(guild):
    """روم الفعاليات: المضبوط بـ ضبط فعاليات، ثم الروم القديم المحفوظ، ثم البحث بالاسم."""
    cfg = db.cfg(guild.id)
    for cid in (cfg.get("events_channel"), (cfg.get("ai") or {}).get("channel"), cfg.get("games_channel")):
        ch = guild.get_channel(cid) if cid else None
        if ch:
            return ch
    return find_channel(guild, EVENTS_NAMES)

# ───── رسائل تلقائية (حديث • آية • سؤال • صلاة على النبي) ─────
async def send_auto(guild, ch, kind=None):
    CUR_GUILD.set(guild)
    kind = kind or random.choices(["hadith", "ayah", "question", "salawat"], [30, 30, 30, 10])[0]
    if kind == "hadith":
        t, s = random.choice(HADITHS)
        e = E("📜 حديث شريف", f"**{t}**\n\n— *{s}*", 0x2ECC71)
    elif kind == "ayah":
        t, s = random.choice(AYAHS)
        e = E("📖 آية من القرآن الكريم", f"﴿ {t} ﴾\n\n— *{s}*", GOLD)
    elif kind == "salawat":
        e = E("🤍 صلوا على النبي", "اللهم صلِّ وسلِّم على نبينا محمد ﷺ", 0x3498DB)
    else:
        e = E("💭 سؤال للمملكة", f"{random.choice(FALLBACK_QUESTIONS)}\n\n*شاركونا إجاباتكم بالشات* 😄", PURPLE)
    try:
        await ch.send(embed=e)
    except discord.HTTPException:
        pass


# ───── الصلاة ─────
async def get_prayer_times(city, country):
    key = (city.lower(), country.lower())
    ent = _prayer_cache.get(key)
    today = None
    if ent:
        try:
            today = datetime.now(ZoneInfo(ent["tz"])).strftime("%d-%m-%Y")
        except Exception:
            today = None
        if ent["date"] == today:
            return ent
    if time.time() - _prayer_fail.get(key, 0) < 300:
        return ent
    params = {"city": city, "country": country, "method": 3}
    if today:
        params["date"] = today
    try:
        async with bot.session.get("https://api.aladhan.com/v1/timingsByCity", params=params,
                                   timeout=aiohttp.ClientTimeout(total=15)) as r:
            j = await r.json()
        d = j["data"]
        tz = d["meta"]["timezone"]
        ent = {"tz": tz, "date": datetime.now(ZoneInfo(tz)).strftime("%d-%m-%Y"),
               "t": {k: d["timings"][k][:5] for k, _ in PRAYERS}}
        _prayer_cache[key] = ent
        return ent
    except Exception as e:
        _prayer_fail[key] = time.time()
        print(f"[PRAYER] {e!r}")
        return ent

PRAYER_LINES = [
    "🕌 حان الآن موعد **صلاة {n}** — قوموا للصلاة يا ملوك، الصلاة نور 🤍",
    "🕋 أذّن لـ **صلاة {n}** — لا تخلي اللعب يشغلك، صلّي وارجع 😉",
    "🤲 حان وقت **صلاة {n}** — الله يتقبل منا ومنكم، ولا تنسون الصلاة على النبي ﷺ",
]

# ───── الجيفاواي العشوائي ─────
GW_INTERVALS = [5 * 3600, 12 * 3600, 24 * 3600, 24 * 3600, 48 * 3600]
GW_DURATIONS = [30, 60, 90, 120]
GW_COINS = [250, 500, 750, 1000, 1500, 2500]
DANGEROUS_PERMS = ("administrator", "manage_guild", "manage_roles", "manage_channels", "manage_messages",
                   "kick_members", "ban_members", "moderate_members", "mention_everyone", "manage_webhooks",
                   "manage_expressions", "manage_emojis_and_stickers", "view_audit_log", "manage_nicknames",
                   "manage_threads", "manage_events")

def safe_roles(guild):
    me = guild.me
    out = []
    if not me or not me.guild_permissions.manage_roles:
        return out
    for r in guild.roles:
        if r.is_default() or r.managed or is_managed_role(r) or r.position >= me.top_role.position:
            continue
        if any(getattr(r.permissions, p, False) for p in DANGEROUS_PERMS):
            continue
        out.append(r)
    return out

def pick_prize(guild):
    customs = (db.cfg(guild.id).get("gw") or {}).get("prizes", [])
    roles = safe_roles(guild)
    pool = [("coins", 50)]
    if roles:
        pool.append(("role", 25))
    if customs:
        pool.append(("custom", 25))
    kind = random.choices([k for k, _ in pool], [w for _, w in pool])[0]
    if kind == "role":
        r = random.choice(roles)
        return {"type": "role", "role_id": r.id, "label": f"رتبة {r.mention}"}
    if kind == "custom":
        return {"type": "custom", "label": random.choice(customs)}
    n = random.choice(GW_COINS)
    return {"type": "coins", "amount": n, "label": f"{n:,} عملة 💰"}

def gw_embed(guild, gw, ended=False, result=""):
    e = discord.Embed(title="🎁 جيفاواي المملكة", color=0x95A5A6 if ended else GOLD, timestamp=discord.utils.utcnow())
    body = f"## {gw['prize']['label']}\n"
    if ended:
        body += result
    else:
        body += (f"اضغط **🎉 اشترك** للدخول!\n⏰ ينتهي: <t:{int(gw['end'])}:R>\n"
                 f"👥 المشاركون: **{len(gw['users'])}**")
    e.description = body
    e.set_footer(text=footer_text(guild))
    return e

class GiveawayView(discord.ui.View):
    def __init__(self, disabled=False):
        super().__init__(timeout=None)
        b = discord.ui.Button(label="اشترك", emoji="🎉", style=discord.ButtonStyle.success,
                              custom_id="nx_gw_join", disabled=disabled)
        b.callback = self.join
        self.add_item(b)

    async def join(self, interaction):
        CUR_GUILD.set(interaction.guild)
        gw = db.data.get("_gw", {}).get(str(interaction.message.id))
        if not gw or time.time() >= gw["end"]:
            return await interaction.response.send_message("⏰ هذا الجيفاواي انتهى.", ephemeral=True)
        uid = interaction.user.id
        if uid in gw["users"]:
            gw["users"].remove(uid)
            note = "↩️ انسحبت من الجيفاواي."
        else:
            gw["users"].append(uid)
            note = "✅ تم تسجيلك، بالتوفيق! 🍀"
        db.mark()
        await interaction.response.edit_message(embed=gw_embed(interaction.guild, gw), view=self)
        try:
            await interaction.followup.send(note, ephemeral=True)
        except discord.HTTPException:
            pass

async def start_giveaway(guild, channel, prize=None, minutes=None):
    CUR_GUILD.set(guild)
    prize = prize or pick_prize(guild)
    minutes = minutes or random.choice(GW_DURATIONS)
    gw = {"guild": guild.id, "channel": channel.id, "prize": prize,
          "end": time.time() + minutes * 60, "users": []}
    try:
        msg = await channel.send(content="🎁 جيفاواي جديد!", embed=gw_embed(guild, gw), view=GiveawayView())
    except discord.HTTPException:
        return None
    db.data.setdefault("_gw", {})[str(msg.id)] = gw
    db.mark()
    return msg

async def deliver_prize(guild, winner, prize):
    t = prize["type"]
    if t == "coins":
        db.user(winner.id)["coins"] += prize["amount"]
        db.mark()
        return "💰 انضافت لرصيدك تلقائياً."
    if t == "role":
        role = guild.get_role(prize["role_id"])
        if role and role_usable(guild, role):
            try:
                await winner.add_roles(role, reason="Bot giveaway")
                return "🎭 انعطيت لك الرتبة تلقائياً."
            except discord.HTTPException:
                pass
        return "⚠️ تعذر إعطاء الرتبة تلقائياً، تواصل مع الإدارة."
    return "📩 تواصل مع الإدارة لاستلام جائزتك."

async def finish_giveaway(mid, gw):
    db.data.get("_gw", {}).pop(mid, None)
    db.mark()
    guild = bot.get_guild(gw["guild"])
    ch = guild.get_channel(gw["channel"]) if guild else None
    if not ch:
        return
    CUR_GUILD.set(guild)
    pool = [m for m in (guild.get_member(u) for u in gw["users"]) if m and not m.bot]
    winner = random.choice(pool) if pool else None
    if winner:
        note = await deliver_prize(guild, winner, gw["prize"])
        result = f"🏆 الفائز: {winner.mention}\n{note}"
    else:
        note, result = "", "😴 ما شارك أحد، انلغى الجيفاواي."
    try:
        msg = await ch.fetch_message(int(mid))
        await msg.edit(content="🎁 انتهى الجيفاواي", embed=gw_embed(guild, gw, True, result), view=GiveawayView(disabled=True))
    except discord.HTTPException:
        pass
    if winner:
        try:
            await ch.send(f"🎉 ألف مبروك {winner.mention}! فزت بـ **{gw['prize']['label']}**\n{note}",
                          allowed_mentions=discord.AllowedMentions(users=True))
        except discord.HTTPException:
            pass

# ───── الحلقة الرئيسية ─────
async def events_tick(guild, now):
    cfg = db.cfg(guild.id)
    ev, gw = cfg.get("ai") or {}, cfg.get("gw") or {}
    ch = events_channel(guild)
    if not ch:
        return
    if gw.get("on"):
        if not gw.get("next"):
            gw["next"] = now + random.uniform(3600, 6 * 3600)
            db.mark()
        elif now >= gw["next"]:
            gw["next"] = now + random.choice(GW_INTERVALS) * random.uniform(0.8, 1.2)
            db.mark()
            await start_giveaway(guild, ch)
    if ev.get("auto"):
        if not ev.get("auto_next"):
            ev["auto_next"] = now + random.uniform(1800, 4 * 3600)
            db.mark()
        elif now >= ev["auto_next"]:
            ev["auto_next"] = now + random.choice([2, 4, 6, 8, 12, 24]) * 3600 * random.uniform(0.7, 1.3)
            db.mark()
            await send_auto(guild, ch)
    if ev.get("prayer"):
        ent = await get_prayer_times(ev.get("city", "Baghdad"), ev.get("country", "Iraq"))
        if ent:
            try:
                hm = datetime.now(ZoneInfo(ent["tz"])).strftime("%H:%M")
            except Exception:
                return
            for k, name in PRAYERS:
                tag = f"{ent['date']}-{k}"
                if ent["t"].get(k) == hm and ev.get("last_prayer") != tag:
                    ev["last_prayer"] = tag
                    db.mark()
                    CUR_GUILD.set(guild)
                    try:
                        await ch.send(embed=E("🕌 تذكير بالصلاة", random.choice(PRAYER_LINES).format(n=name), 0x2ECC71))
                    except discord.HTTPException:
                        pass

@tasks.loop(seconds=30)
async def events_loop():
    try:
        now = time.time()
        for mid, gw in list(db.data.get("_gw", {}).items()):
            if now >= gw["end"]:
                await finish_giveaway(mid, gw)
        for guild in list(bot.guilds):
            try:
                await events_tick(guild, now)
            except Exception as e:
                print(f"[EVENTS] guild={guild.id}: {e!r}")
    except Exception as e:
        print(f"[EVENTS-LOOP] {e!r}")

@events_loop.before_loop
async def _before_events_loop():
    await bot.wait_until_ready()

# ───── لوحة التحكم + الأوامر ─────
def events_status_embed(guild):
    cfg = db.cfg(guild.id)
    ev, gw = cfg.get("ai") or {}, cfg.get("gw") or {}
    ch = events_channel(guild)
    st = lambda v: "🟢 شغّال" if v else "🔴 متوقف"
    e = E("🎉 لوحة الفعاليات", "التحكم بهذا القسم للإدارة العليا فقط • الأزرار بالأسفل تشغّل/توقف كل ميزة.", 0xE91E63)
    e.add_field(name="✨ رسائل تلقائية", value=st(ev.get("auto")), inline=True)
    e.add_field(name="🕌 الصلاة", value=f"{st(ev.get('prayer'))} • `{ev.get('city', 'Baghdad')}, {ev.get('country', 'Iraq')}`", inline=True)
    nxt = f" • القادم <t:{int(gw['next'])}:R>" if gw.get("on") and gw.get("next") else ""
    e.add_field(name="🎁 الجيفاواي", value=st(gw.get("on")) + nxt, inline=True)
    e.add_field(name="📍 الروم", value=ch.mention if ch else "❌ غير محدد (`ضبط فعاليات #روم`)", inline=True)
    return e

def _need_channel(ctx):
    """يحدد روم الفعاليات بالروم الحالي إذا ما كان مضبوطاً."""
    if events_channel(ctx.guild) is None:
        db.cfg(ctx.guild.id)["events_channel"] = ctx.channel.id
        db.mark()
        return True
    return False

def ensure_events_channel(guild, channel):
    if events_channel(guild) is None:
        db.cfg(guild.id)["events_channel"] = channel.id
        db.mark()

class EventsPanelView(discord.ui.View):
    """لوحة تحكم الفعاليات — للإدارة العليا فقط."""
    def __init__(self, guild):
        super().__init__(timeout=600)
        cfg = db.cfg(guild.id)
        ev, gw = cfg.get("ai") or {}, cfg.get("gw") or {}
        states = [("auto", "تلقائي", "✨", ev.get("auto")), ("prayer", "الصلاة", "🕌", ev.get("prayer")),
                  ("gw", "الجيفاواي", "🎁", gw.get("on"))]
        for key, label, emoji, on in states:
            b = discord.ui.Button(label=f"{label}: {'شغّال' if on else 'متوقف'}", emoji=emoji, row=0,
                                  style=discord.ButtonStyle.success if on else discord.ButtonStyle.danger)
            b.callback = self._toggle(key)
            self.add_item(b)
        for label, emoji, cb in (("رسالة الآن", "🎲", self._now_msg), ("جيفاواي الآن", "🎁", self._now_gw)):
            b = discord.ui.Button(label=label, emoji=emoji, style=discord.ButtonStyle.primary, row=1)
            b.callback = cb
            self.add_item(b)
        b = discord.ui.Button(label="تحديث", emoji="🔄", style=discord.ButtonStyle.secondary, row=1)
        b.callback = self._refresh
        self.add_item(b)

    async def interaction_check(self, interaction):
        CUR_GUILD.set(interaction.guild)
        if is_admin(interaction.user):
            return True
        await interaction.response.send_message("❌ لوحة الفعاليات للإدارة العليا فقط.", ephemeral=True)
        return False

    def _toggle(self, key):
        async def cb(interaction):
            guild = interaction.guild
            ev, gw = ev_cfg(guild), db.cfg(guild.id).setdefault("gw", {})
            if key == "auto":
                ev["auto"] = not ev.get("auto")
                ev.pop("auto_next", None)
            elif key == "prayer":
                ev["prayer"] = not ev.get("prayer")
            else:
                gw["on"] = not gw.get("on")
                gw.pop("next", None)
            ensure_events_channel(guild, interaction.channel)
            db.mark()
            await interaction.response.edit_message(embed=events_status_embed(guild), view=EventsPanelView(guild))
        return cb

    async def _now_msg(self, interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        await send_auto(guild, events_channel(guild) or interaction.channel)
        await interaction.followup.send("✅ انرسلت رسالة تلقائية.", ephemeral=True)

    async def _now_gw(self, interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        msg = await start_giveaway(guild, events_channel(guild) or interaction.channel)
        await interaction.followup.send("✅ انطلق جيفاواي جديد." if msg else "❌ تعذر إرسال الجيفاواي.", ephemeral=True)

    async def _refresh(self, interaction):
        await interaction.response.edit_message(embed=events_status_embed(interaction.guild), view=EventsPanelView(interaction.guild))

@bot.command(name="فعاليات", aliases=["لوحة_الفعاليات", "الفعاليات"])
@commands.guild_only()
@admin_only()
async def events_panel_cmd(ctx):
    await ctx.send(embed=events_status_embed(ctx.guild), view=EventsPanelView(ctx.guild))

@bot.command(name="تلقائي", aliases=["سوالف"])
@commands.guild_only()
@admin_only()
async def auto_cmd(ctx, action: str = None):
    ev = ev_cfg(ctx.guild)
    if action in ON_WORDS:
        ev["auto"] = True
        ev.pop("auto_next", None)
        db.mark()
        note = " (حددت هذا الروم)" if _need_channel(ctx) else ""
        return await ctx.send(f"✨ تم تشغيل الرسائل التلقائية، تجي بأوقات عشوائية.{note}")
    if action in OFF_WORDS:
        ev["auto"] = False
        db.mark()
        return await ctx.send("🔴 تم إيقاف الرسائل التلقائية.")
    if action in ("الان", "الآن", "now"):
        ch = events_channel(ctx.guild) or ctx.channel
        return await send_auto(ctx.guild, ch)
    await ctx.send(embed=events_status_embed(ctx.guild))

@bot.command(name="صلاة", aliases=["الصلاة", "اذان"])
@commands.guild_only()
@admin_only()
async def prayer_cmd(ctx, action: str = None, *, rest: str = ""):
    ev = ev_cfg(ctx.guild)
    if action in ON_WORDS:
        ev["prayer"] = True
        db.mark()
        note = " (حددت هذا الروم)" if _need_channel(ctx) else ""
        return await ctx.send(f"🕌 تم تشغيل تذكير الصلاة لمدينة `{ev.get('city', 'Baghdad')}`.{note}")
    if action in OFF_WORDS:
        ev["prayer"] = False
        db.mark()
        return await ctx.send("🔴 تم إيقاف تذكير الصلاة.")
    if action in ("مدينة", "city"):
        parts = rest.split()
        if not parts:
            return await ctx.reply("الاستخدام: `صلاة مدينة Baghdad Iraq` (بالإنجليزي)")
        ev["city"], ev["country"] = parts[0], (parts[1] if len(parts) > 1 else "Iraq")
        db.mark()
        _prayer_cache.clear()
        return await ctx.send(f"✅ المدينة صارت `{ev['city']}, {ev['country']}`.")
    await ctx.send(embed=events_status_embed(ctx.guild))

@bot.command(name="جيفاواي", aliases=["جيفاوي", "giveaway"])
@commands.guild_only()
@admin_only()
async def giveaway_cmd(ctx, action: str = None):
    gw = db.cfg(ctx.guild.id).setdefault("gw", {})
    if action in ON_WORDS:
        gw["on"] = True
        gw.pop("next", None)
        db.mark()
        note = " (حددت هذا الروم)" if _need_channel(ctx) else ""
        return await ctx.send(f"🎁 تم تشغيل الجيفاواي العشوائي: أوقات ومدد وجوائز عشوائية.{note}")
    if action in OFF_WORDS:
        gw["on"] = False
        db.mark()
        return await ctx.send("🔴 تم إيقاف الجيفاواي العشوائي.")
    if action in ("الان", "الآن", "now"):
        msg = await start_giveaway(ctx.guild, events_channel(ctx.guild) or ctx.channel)
        return None if msg else await ctx.reply("❌ تعذر إرسال الجيفاواي.")
    await ctx.send(embed=events_status_embed(ctx.guild))

@bot.command(name="جيفاواي_جديد", aliases=["جيفاواي_يدوي"])
@commands.guild_only()
@admin_only()
async def giveaway_new_cmd(ctx, minutes: int, *, prize: str):
    """جيفاواي يدوي بالروم الحالي: جيفاواي_جديد 30 نيترو  أو  جيفاواي_جديد 60 عملات 500"""
    if not 1 <= minutes <= 10080:
        return await ctx.reply("❌ المدة من 1 إلى 10080 دقيقة.")
    prize = prize.strip()[:100]
    m = re.fullmatch(r"(?:عملات|coins)\s+(\d{1,7})", prize, re.I)
    if m:
        n = int(m.group(1))
        info = {"type": "coins", "amount": n, "label": f"{n:,} عملة 💰"}
    else:
        info = {"type": "custom", "label": prize}
    msg = await start_giveaway(ctx.guild, ctx.channel, info, minutes)
    if msg is None:
        await ctx.reply("❌ تعذر إرسال الجيفاواي.")

@bot.command(name="جيفاواي_جائزة", aliases=["جائزة_جيفاواي", "جوائز"])
@commands.guild_only()
@admin_only()
async def giveaway_prize_cmd(ctx, action: str = "قائمة", *, rest: str = ""):
    gw = db.cfg(ctx.guild.id).setdefault("gw", {})
    prizes = gw.setdefault("prizes", [])
    if action in ("اضافة", "إضافة", "add") and rest.strip():
        if len(prizes) >= 25:
            return await ctx.reply("❌ الحد الأقصى 25 جائزة.")
        prizes.append(rest.strip()[:80])
        db.mark()
        return await ctx.send(f"✅ انضافت الجائزة **{prizes[-1]}** للسحب العشوائي.")
    if action in ("حذف", "delete", "remove") and rest.strip().isdigit():
        i = int(rest.strip())
        if 1 <= i <= len(prizes):
            old = prizes.pop(i - 1)
            db.mark()
            return await ctx.send(f"🗑️ تم حذف **{old}**.")
        return await ctx.reply("❌ رقم غير صحيح.")
    lines = "\n".join(f"**{i}.** {p}" for i, p in enumerate(prizes, 1)) or "ما في جوائز خاصة بعد."
    e = E("🎁 الجوائز الخاصة", lines + "\n\n`جيفاواي_جائزة اضافة كيس بي` • `جيفاواي_جائزة حذف 1`\n"
          "العملات والرتبة (من اختيار البوت) تلقائية.", GOLD)
    await ctx.send(embed=e)

HELP_SECTIONS["events"] = ("🎉", "الفعاليات والتذكير", "جيفاواي بالأزرار، رسائل تلقائية (حديث/آية/سؤال)، وتذكير بأوقات الصلاة.", [
    "🎛️ اللوحة",
    ("فعاليات", "فعاليات", "لوحة أزرار تشغّل/توقف كل فعالية وتجرّبها فوراً."),
    "🎁 الجيفاواي",
    ("جيفاواي", "جيفاواي [تشغيل|ايقاف|الان]", "جيفاواي عشوائي بأوقات ومدد وجوائز (عملات / رتبة / جوائز خاصة)."),
    ("جيفاواي_جديد", "جيفاواي_جديد [الدقائق] [الجائزة]", "جيفاواي يدوي بالروم الحالي، مثال: `جيفاواي_جديد 30 نيترو` أو `جيفاواي_جديد 60 عملات 500`."),
    ("جيفاواي_جائزة", "جيفاواي_جائزة [اضافة نص | حذف رقم | قائمة]", "جوائز خاصة تدخل في السحب العشوائي (مثل: كيس بي)."),
    "✨ رسائل تلقائية وصلاة",
    ("تلقائي", "تلقائي [تشغيل|ايقاف|الان]", "حديث، آية، سؤال أو صلاة على النبي بأوقات عشوائية (كل ساعات أو يوم)."),
    ("صلاة", "صلاة [تشغيل|ايقاف|مدينة Baghdad Iraq]", "تذكير بأوقات الصلاة حسب المدينة."),
    "📍 الروم",
    ("ضبط فعاليات", "ضبط فعاليات #روم", "الروم اللي ينرسل فيه الجيفاواي والرسائل التلقائية والصلاة."),
])


# ═════════════════════════ الأدوات المساعدة (تذاكر • اقتراحات • تصويت • تذكير • معلومات) ═════════════════════════
BOOT_TIME = time.time()
TICKET_CAT = "🎫・التذاكر"
_ticket_last = {}

def ticket_owner_id(channel):
    """صاحب التذكرة (يُحفظ بوصف الروم topic = ticket:<id>) أو None إذا الروم مو تذكرة."""
    m = re.fullmatch(r"ticket:(\d+)", getattr(channel, "topic", None) or "")
    return int(m.group(1)) if m else None

def is_ticket_staff(member):
    p = member.guild_permissions
    return bool(is_admin(member) or is_mod_role(member) or p.manage_channels or p.manage_messages)

def ticket_staff_roles(guild):
    high, mod = detect_staff(guild)
    return [r for r in high + mod if not r.managed][:20]

class TicketCloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        b = discord.ui.Button(label="إغلاق التذكرة", emoji="🔒", style=discord.ButtonStyle.danger, custom_id="nx_ticket_close")
        b.callback = self.close
        self.add_item(b)

    async def close(self, interaction):
        CUR_GUILD.set(interaction.guild)
        ch = interaction.channel
        owner = ticket_owner_id(ch)
        if owner is None:
            return await interaction.response.send_message("❌ هذا الروم مو تذكرة.", ephemeral=True)
        if interaction.user.id != owner and not is_ticket_staff(interaction.user):
            return await interaction.response.send_message("❌ بس صاحب التذكرة أو الإدارة يگدرون يسكرونها.", ephemeral=True)
        await interaction.response.send_message(embed=E("🔒 جاري إغلاق التذكرة", "ينحذف هذا الروم خلال **5 ثواني**...", 0xE74C3C))
        await log_event(interaction.guild, "🎫 إغلاق تذكرة", f"`{ch.name}` أغلقها {interaction.user.mention}", "red",
                        fields=[("👤 صاحب التذكرة", f"<@{owner}>", True)])
        await asyncio.sleep(5)
        try:
            await ch.delete(reason=f"Ticket closed by {interaction.user}")
        except discord.HTTPException:
            pass

class TicketOpenView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        b = discord.ui.Button(label="فتح تذكرة", emoji="🎫", style=discord.ButtonStyle.success, custom_id="nx_ticket_open")
        b.callback = self.open_ticket
        self.add_item(b)

    async def open_ticket(self, interaction):
        guild, user = interaction.guild, interaction.user
        if guild is None:
            return
        CUR_GUILD.set(guild)
        me = guild.me
        if not me.guild_permissions.manage_channels:
            return await interaction.response.send_message("❌ البوت يحتاج صلاحية **Manage Channels**.", ephemeral=True)
        for ch in guild.text_channels:
            if ticket_owner_id(ch) == user.id:
                return await interaction.response.send_message(f"📌 عندك تذكرة مفتوحة: {ch.mention}", ephemeral=True)
        if time.time() - _ticket_last.get(user.id, 0) < 15:
            return await interaction.response.send_message("⏳ انتظر شوي قبل تفتح تذكرة ثانية.", ephemeral=True)
        _ticket_last[user.id] = time.time()
        await interaction.response.defer(ephemeral=True)
        base = dict(view_channel=True, send_messages=True, read_message_history=True, attach_files=True, embed_links=True)
        ow = {guild.default_role: discord.PermissionOverwrite(view_channel=False),
              user: discord.PermissionOverwrite(**base),
              me: discord.PermissionOverwrite(**base, manage_channels=True)}
        for r in ticket_staff_roles(guild):
            ow[r] = discord.PermissionOverwrite(**base)
        try:
            cat = discord.utils.get(guild.categories, name=TICKET_CAT)
            if cat is None:
                cat = await guild.create_category(
                    TICKET_CAT, reason="Tickets",
                    overwrites={guild.default_role: discord.PermissionOverwrite(view_channel=False),
                                me: discord.PermissionOverwrite(**base, manage_channels=True)})
            name = ("تذكرة-" + re.sub(r"[^\w\-]", "", user.name.lower()))[:90]
            ch = await guild.create_text_channel(name, category=cat, overwrites=ow, topic=f"ticket:{user.id}",
                                                 reason=f"Ticket by {user}")
        except discord.HTTPException as ex:
            print(f"[TICKET] {ex!r}")
            return await interaction.followup.send("❌ تعذر إنشاء التذكرة، تأكد من صلاحيات البوت.", ephemeral=True)
        e = E(f"🎫 تذكرة {user.display_name}",
              "اكتب طلبك أو مشكلتك هنا بالتفصيل، والإدارة راح تجاوبك بأقرب وقت.\n\n"
              "🔒 هذا الروم يشوفه **أنت والإدارة فقط**.\nلما تخلص اضغط **إغلاق التذكرة**.", 0x2ECC71)
        e.set_thumbnail(url=user.display_avatar.url)
        await ch.send(content=user.mention, embed=e, view=TicketCloseView())
        await log_event(guild, "🎫 تذكرة جديدة", f"{user.mention} فتح {ch.mention}", "green")
        await interaction.followup.send(f"✅ انفتحت تذكرتك: {ch.mention}", ephemeral=True)

@bot.command(name="تذكرة_لوحة", aliases=["لوحة_تذاكر", "ticket_panel"])
@commands.guild_only()
@admin_only()
async def ticket_panel_cmd(ctx):
    e = E("🎫 مركز الدعم", "عندك استفسار أو مشكلة أو شكوى؟\n"
          "اضغط الزر بالأسفل وينفتح لك **روم خاص** بينك وبين الإدارة فقط. 🔒", 0x2ECC71)
    await ctx.send(embed=e, view=TicketOpenView())
    try:
        await ctx.message.delete()
    except discord.HTTPException:
        pass

@bot.command(name="تذكرة_اضافة", aliases=["اضافة_للتذكرة"])
@commands.guild_only()
@staff_perms(manage_messages=True)
async def ticket_add_cmd(ctx, member: discord.Member):
    if ticket_owner_id(ctx.channel) is None:
        return await ctx.reply("❌ هذا الأمر يشتغل داخل التذاكر فقط.")
    await ctx.channel.set_permissions(member, view_channel=True, send_messages=True,
                                      read_message_history=True, attach_files=True)
    await ctx.send(f"✅ انضاف {member.mention} للتذكرة.")

# ───── الاقتراحات ─────
@bot.command(name="اقتراح", aliases=["suggest"])
@commands.guild_only()
@commands.cooldown(1, 60, commands.BucketType.user)
async def suggest_cmd(ctx, *, text: str):
    ch = get_channel(ctx.guild, "suggest_channel", SUGGEST_NAMES)
    if ch is None:
        ctx.command.reset_cooldown(ctx)
        return await ctx.reply("❌ ما في روم اقتراحات بعد. الإدارة تضبطه بأمر `ضبط اقتراحات #روم`.")
    e = E("💡 اقتراح جديد", text[:3500], 0xF1C40F)
    e.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
    try:
        msg = await ch.send(embed=e)
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")
    except discord.HTTPException:
        ctx.command.reset_cooldown(ctx)
        return await ctx.reply("❌ تعذر إرسال الاقتراح، تأكد من صلاحيات البوت بالروم.")
    try:
        await ctx.message.delete()
    except discord.HTTPException:
        pass
    await ctx.send(f"✅ انرسل اقتراحك إلى {ch.mention}", delete_after=8)

# ───── التصويت ─────
NUM_EMOJI = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

@bot.command(name="تصويت", aliases=["poll", "استفتاء"])
@commands.guild_only()
@commands.cooldown(1, 30, commands.BucketType.user)
async def poll_cmd(ctx, *, text: str):
    """تصويت السؤال | خيار1 | خيار2 ...  (بدون خيارات = ✅ / ❌)"""
    parts = [p.strip() for p in re.split(r"[|\n]", text) if p.strip()]
    if not parts:
        return await ctx.reply("الاستخدام: `تصويت السؤال | خيار1 | خيار2`")
    q, opts = parts[0][:250], parts[1:]
    if len(opts) == 1 or len(opts) > 10:
        ctx.command.reset_cooldown(ctx)
        return await ctx.reply("❌ حط من 2 إلى 10 خيارات، أو اكتب السؤال بس لتصويت ✅ / ❌.")
    if opts:
        body = "\n".join(f"{NUM_EMOJI[i]}  {o[:100]}" for i, o in enumerate(opts))
        emojis = NUM_EMOJI[:len(opts)]
    else:
        body, emojis = "✅  موافق\n❌  غير موافق", ["✅", "❌"]
    e = E(f"📊 {q}", body, 0x3498DB)
    e.set_author(name=f"تصويت من {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
    msg = await ctx.send(embed=e)
    for em in emojis:
        try:
            await msg.add_reaction(em)
        except discord.HTTPException:
            break
    try:
        await ctx.message.delete()
    except discord.HTTPException:
        pass

# ───── التذكير ─────
_DUR_UNITS = {"ث": 1, "s": 1, "د": 60, "m": 60, "س": 3600, "h": 3600, "ي": 86400, "d": 86400}

def parse_duration(token):
    m = re.fullmatch(r"(\d{1,5})\s*([A-Za-z\u0600-\u06FF]*)", (token or "").strip())
    if not m:
        return None
    mult = _DUR_UNITS.get((m.group(2) or "د")[0].lower())
    return int(m.group(1)) * mult if mult else None

@bot.command(name="ذكرني", aliases=["تذكير", "remind"])
@commands.guild_only()
async def remind_cmd(ctx, duration: str, *, text: str):
    secs = parse_duration(duration)
    if secs is None or not 60 <= secs <= 30 * 86400:
        return await ctx.reply("❌ المدة من دقيقة إلى 30 يوم. أمثلة: `ذكرني 30د اشرب ماي` • `ذكرني 2س اجتماع` • `ذكرني 1ي الراتب`")
    items = db.data.setdefault("_remind", [])
    if sum(1 for r in items if r["u"] == ctx.author.id) >= 10:
        return await ctx.reply("❌ عندك 10 تذكيرات شغالة، انتظر وحد منها ينتهي.")
    end = time.time() + secs
    items.append({"u": ctx.author.id, "c": ctx.channel.id, "end": end, "t": text.strip()[:300]})
    db.mark()
    await ctx.send(f"⏰ تمام {ctx.author.mention}، أذكرك <t:{int(end)}:R> — **{text.strip()[:100]}**")

@tasks.loop(seconds=20)
async def remind_loop():
    try:
        items = db.data.get("_remind")
        if not items:
            return
        now = time.time()
        due = [r for r in items if now >= r["end"]]
        if not due:
            return
        db.data["_remind"] = [r for r in items if now < r["end"]]
        db.mark()
        for r in due:
            e = E("⏰ تذكير", r["t"], 0xF1C40F)
            sent = False
            ch = bot.get_channel(r["c"])
            if ch is not None:
                try:
                    await ch.send(content=f"<@{r['u']}>", embed=e)
                    sent = True
                except discord.HTTPException:
                    pass
            if not sent:
                user = bot.get_user(r["u"])
                if user is not None:
                    try:
                        await user.send(embed=e)
                    except discord.HTTPException:
                        pass
    except Exception as ex:
        print(f"[REMIND] {ex!r}")

@remind_loop.before_loop
async def _before_remind_loop():
    await bot.wait_until_ready()

# ───── معلومات العضو + حالة البوت ─────
@bot.command(name="معلومات", aliases=["مستخدم", "userinfo"])
@commands.guild_only()
async def userinfo_cmd(ctx, member: discord.Member = None):
    member = member or ctx.author
    u = db.user(member.id)
    roles = [r.mention for r in reversed(member.roles) if not r.is_default()]
    e = E(f"🪪 {member.display_name}", color=member.color.value or PURPLE)
    e.set_thumbnail(url=member.display_avatar.url)
    e.add_field(name="🆔 المعرف", value=f"`{member.id}`", inline=True)
    e.add_field(name="🎖️ أعلى رتبة", value=member.top_role.mention if roles else "—", inline=True)
    e.add_field(name="🚀 بوست", value="✅" if member.premium_since else "—", inline=True)
    if member.joined_at:
        e.add_field(name="📅 انضم للسيرفر", value=discord.utils.format_dt(member.joined_at, "R"), inline=True)
    e.add_field(name="🕰️ عمر الحساب", value=discord.utils.format_dt(member.created_at, "R"), inline=True)
    vmin = vc_minutes(ctx.guild, member.id)
    e.add_field(name="📈 المستويات", inline=False,
                value=f"💬 كتابة `{u['level']}` • 🎙️ فويس `{vc_level_of(vmin)}` ({fmt_hours(vmin)}) • 💰 `{u['coins']:,}`")
    e.add_field(name=f"🎭 الرتب ({len(roles)})", value=(" ".join(roles[:12]) or "—") + (" …" if len(roles) > 12 else ""), inline=False)
    await ctx.send(embed=e)

@bot.command(name="بنق", aliases=["ping", "بينغ", "حالة_البوت"])
async def ping_cmd(ctx):
    up = int(time.time() - BOOT_TIME)
    d, rem = divmod(up, 86400)
    h, rem = divmod(rem, 3600)
    e = E("🏓 حالة البوت", color=0x2ECC71)
    e.add_field(name="📡 التأخير", value=f"`{round(bot.latency * 1000)}ms`", inline=True)
    e.add_field(name="⏱️ مدة التشغيل", value=f"`{d}ي {h}س {rem // 60}د`", inline=True)
    e.add_field(name="🌐 السيرفرات", value=f"`{len(bot.guilds)}`", inline=True)
    await ctx.send(embed=e)

HELP_SECTIONS["tools"] = ("🛠️", "الأدوات المساعدة", "تذاكر الدعم، اقتراحات، تصويت، تذكير، ومعلومات الأعضاء.", [
    "👥 للجميع",
    ("معلومات", "معلومات [@العضو]", "بطاقة معلومات: الرتب، تاريخ الانضمام، عمر الحساب، لفل الكتابة والفويس."),
    ("اقتراح", "اقتراح [نص الاقتراح]", "يرسل اقتراحك لروم الاقتراحات مع تصويت ✅ ❌."),
    ("تصويت", "تصويت السؤال | خيار1 | خيار2", "تصويت بأزرار الأرقام (2 إلى 10 خيارات)، أو بدون خيارات لتصويت ✅ ❌."),
    ("ذكرني", "ذكرني [المدة] [النص]", "يذكرك بالروم أو بالخاص، مثال: `ذكرني 30د اشرب ماي` (د دقائق • س ساعات • ي أيام)."),
    ("بنق", "بنق", "سرعة البوت ومدة تشغيله."),
    "🎫 التذاكر",
    ("تذكرة_لوحة", "تذكرة_لوحة", "(إدارة عليا) يرسل لوحة بزر **فتح تذكرة**؛ كل عضو ينفتح له روم خاص مع الإدارة."),
    ("تذكرة_اضافة", "تذكرة_اضافة @العضو", "(إشراف) يضيف عضواً للتذكرة الحالية."),
    "📍 الضبط",
    ("ضبط اقتراحات", "ضبط اقتراحات #روم", "(إدارة عليا) الروم اللي تنرسل فيه الاقتراحات."),
])


# ───────────────────────── معالج الأخطاء ─────────────────────────
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.CommandOnCooldown):
        return await ctx.send(f"⏳ انتظر **{error.retry_after:.0f}** ثانية.", delete_after=5)
    if isinstance(error, HierarchyError):
        return await ctx.send(str(error) or "🚫 ما تگدر تنفذ هذا الأمر على شخص أعلى منك.", delete_after=10,
                              allowed_mentions=discord.AllowedMentions.none())
    if ctx.message.id in RAW_IDS:
        return  # أوامر بدون بادئة: لا نزعج الشات بأخطاء الاستخدام
    if isinstance(error, (commands.MissingPermissions, commands.CheckFailure)):
        return await ctx.send("❌ ليس لديك صلاحية لهذا الأمر.", delete_after=6)
    if isinstance(error, commands.UserInputError):
        return await ctx.send("❌ استخدام خاطئ. اكتب `مساعدة` لمعرفة طريقة الاستخدام.", delete_after=8)
    print(f"[CMD] {ctx.command}: {error!r}")

# تشغيل البوت
# لا نعيد تشغيل العملية ذاتياً عند فشل تسجيل الدخول أو خطأ إعدادات؛ ذلك قد يصنع حلقة
# إعادة تشغيل لا نهائية. discord.py يتولى إعادة الاتصال بالأخطاء الشبكية المعتادة.
def main():
    if not TOKEN:
        raise SystemExit("[RUN] ما لقيت التوكن: ضعه بمتغير البيئة DISCORD_TOKEN أو بملف token.txt بجانب الملف.")
    try:
        bot.run(TOKEN, reconnect=True, log_handler=None)
    except KeyboardInterrupt:
        print("[RUN] تم إيقاف البوت يدوياً.")
    except Exception as e:
        print(f"[RUN] تعذر تشغيل البوت: {e!r}")
        raise
    finally:
        db.flush_sync()

if __name__ == "__main__":
    main()
