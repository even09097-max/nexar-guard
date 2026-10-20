# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════════════╗
# ║  MULTI-SERVER DISCORD BOT  •  Python 3.10+                           ║
# ║  pip install -r requirements.txt                                     ║
# ║  التوكن من متغير البيئة DISCORD_TOKEN (لا تكتبه داخل الكود)           ║
# ║  فعّل Message Content Intent + Server Members Intent                 ║
# ║  البوت بلا اسم ثابت: أونر كل سيرفر يسمّيه بأمر  تعيين_اسم             ║
# ╠══════════════════════════════════════════════════════════════════════╣
# ║  فهرس الأقسام (ابحث عن العنوان للوصول للقسم):                         ║
# ║   01 الإعدادات والثوابت          10 المساعدة (لوحة تفاعلية)           ║
# ║   02 الرتب والألوان              11 البروفايل والمتصدرين              ║
# ║   03 قاعدة البيانات              12 الإدارة والمودريشن                ║
# ║   04 الصور والبطاقات             13 إدارة XP واللفلات                 ║
# ║   05 النواة (البوت + الهوية)     14 الإعلانات والتجهيز والهيكل        ║
# ║   06 XP واللفلات                 15 قسم الألعاب + الألعاب الجديدة      ║
# ║   07 نظام الفويس (لفل + ساعات)   16 المتجر والجيفات والردود          ║
# ║   08 الأحداث واللوقات            17 البوت الذكي (نماذج متعددة)        ║
# ║   09 الحماية                     18 معالج الأخطاء والتشغيل            ║
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

TOKEN = "MTU1OTkwNTIzMjQ5Mjk1Nzc0Ng.G833Zj.xSEuRR-Auy3mTiZ7-4C6EsvJmNh3s1554BFr4w"

# ───────────────────────── الإعدادات ─────────────────────────
PREFIX = "!"
# خزّن البيانات والوسائط بجانب هذا الملف بدل الاعتماد على مجلد التشغيل الحالي؛
# يمكن تغيير المسارات من متغيرات البيئة عند الاستضافة.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.abspath(os.getenv("BOT_DB_FILE") or os.getenv("NEXAR_DB_FILE") or os.path.join(BASE_DIR, "users_stats.json"))
MEDIA_DIR = os.path.abspath(os.getenv("BOT_MEDIA_DIR") or os.getenv("NEXAR_MEDIA_DIR") or os.path.join(BASE_DIR, "media"))
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
GAMES_NAMES = ("العاب", "🎮・الالعاب", "الالعاب", "games")
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
    "coins": 0, "last_daily": 0, "voice_minutes": 0, "games_played": 0, "games_won": 0,
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
    "help": "المساعدة", "games": "قسم الألعاب", "leaderboard": "المتصدرين",
    "colors": "لوحة الألوان", "setup": "التجهيز",
    "ban": "حظر", "kick": "طرد", "mute": "ميوت", "unmute": "فك ميوت", "warn": "تحذير",
    "pardon": "عفو", "clear": "مسح", "lock": "قفل", "unlock": "فتح",
    "announce": "الإعلان", "emergency": "طوارئ", "calm": "استقرار",
    "daily": "الراتب", "win": "فوز بلعبة", "lose": "خسارة بلعبة",
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

def render_profile(avatar_bytes, name, level, xp, need, rank_en, cols, pos, total, msgs, voice_min, coins, warns):
    W, H = 940, 320
    c1, c2 = _rgb(cols[0]), _rgb(cols[1])
    dark1 = tuple(int(v * 0.35) for v in c1)
    dark2 = tuple(int(v * 0.35) for v in c2)
    base = _gradient(W, H, dark1, dark2).convert("RGBA")
    d = ImageDraw.Draw(base)
    d.rounded_rectangle((12, 12, W - 13, H - 13), radius=26, outline=c1, width=3)
    S = 170
    ax, ay = 40, 40
    d.ellipse((ax - 7, ay - 7, ax + S + 7, ay + S + 7), fill=c2)
    d.ellipse((ax - 3, ay - 3, ax + S + 3, ay + S + 3), fill=(12, 8, 28))
    try:
        av = _circle(Image.open(io.BytesIO(avatar_bytes)), S)
        base.paste(av, (ax, ay), av)
    except Exception:
        pass
    d = ImageDraw.Draw(base)
    x = 245
    nm = ar(clean_name(name))
    d.text((x, 30), nm, font=_fit_text(d, nm, W - x - 220, 46), fill=(255, 255, 255))
    d.text((x, 92), rank_en, font=get_font(28), fill=(255, 215, 0))
    d.text((W - 40, 34), f"LEVEL {level}", font=get_font(40), fill=(255, 255, 255), anchor="ra")
    d.text((W - 40, 86), f"RANK #{pos}/{total}", font=get_font(24), fill=(210, 210, 255), anchor="ra")
    bx, by, bw, bh = x, 140, W - x - 40, 34
    d.rounded_rectangle((bx, by, bx + bw, by + bh), radius=17, fill=(0, 0, 0, 170))
    ratio = max(0.0, min(1.0, xp / max(1, need)))
    if ratio > 0:
        fw = max(bh, int(bw * ratio))
        bar = _gradient(fw, bh, c1, c2).convert("RGBA")
        m = Image.new("L", (fw, bh), 0)
        ImageDraw.Draw(m).rounded_rectangle((0, 0, fw - 1, bh - 1), radius=17, fill=255)
        base.paste(bar, (bx, by), m)
    d = ImageDraw.Draw(base)
    d.text((bx + bw // 2, by + bh // 2), f"{xp:,} / {need:,} XP", font=get_font(20), fill=(255, 255, 255), anchor="mm")
    stats = [("MESSAGES", f"{msgs:,}"), ("VOICE", f"{voice_min // 60}h {voice_min % 60}m"),
             ("COINS", f"{coins:,}"), ("WARNINGS", str(warns))]
    sw = (W - x - 40) // 4
    for i, (lab, val) in enumerate(stats):
        sx = x + i * sw
        d.text((sx, 205), val, font=get_font(32), fill=(255, 255, 255))
        d.text((sx, 248), lab, font=get_font(18), fill=(200, 200, 230))
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
        flush_loop.start()
        voice_loop.start()
        ai_loop.start()
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
                         f"📜 اقرأ القوانين • 🎨 اختار لونك • 🎮 العب وارتقِ باللفلات"),
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
            usable = (message.channel.id not in RAW_BLOCK
                      and cmd is not None and not cmd.hidden
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
                await ai_maybe_reply(message)
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
        ("بوت", "بوت [كلامك] أو منشن البوت", "سولف مع البوت الذكي، أو منشنه / رد على رسالته."),
        ("R", "R [@العضو]", "بطاقة الملف الشخصي + بطاقة الفويس (لفل الفويس وساعاتك وترتيبك بالساعات)."),
        ("افتار", "افتار [@العضو]", "يعرض صورة العضو بحجم كبير."),
        ("سيرفر", "سيرفر", "معلومات عن السيرفر (الأعضاء، الرومات، البوست...)."),
        ("هوية", "هوية", "يعرض اسم البوت وبايو وصورة هذا السيرفر."),
        ("الوان", "الوان", "لوحة 50 لوناً، تختار منها لوناً واحداً فقط."),
        ("لون", "لون [1-50]", "يطبق اللون برقمه مباشرة."),
        ("الغاء_لون", "الغاء_لون", "يزيل لونك الحالي."),
        ("تحذيرات", "تحذيرات [@العضو]", "يعرض سجل التحذيرات."),
    ]),
    "levels": ("🏆", "قسم المستويات (Levels)", "نظام الـ XP والرتب والترتيب.", [
        ("R", "R [@العضو]", "بطاقة بروفايل بمستواك وشريط تقدم الـ XP وترتيبك."),
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
        ("لفل", "لفل @العضو [المستوى]", "يضبط مستوى العضو."),
        ("اكس_بي", "اكس_بي @العضو [المبلغ]", "يعطي العضو XP (وتجي تهنئة اللفل تلقائياً)."),
        ("خصم", "خصم @العضو [عدد]", "ينقص من مستوى العضو."),
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
        ("صورة", "صورة [المفتاح] [الرابط]", "يضبط صورة أي رسالة."),
    ]),
    "games": ("🎮", "قسم الألعاب (Games)", "اربح عملات وXP وتنافس مع أصحابك.", [
        "🧍 الألعاب الفردية",
        ("سلوت", "سلوت [الرهان]", "ماكينة الحظ، 3 رموز متشابهة تعني جائزة كبيرة."),
        ("ألغام", "ألغام [الرهان]", "افتح المربعات وجمّع الجواهر وانسحب قبل اللغم."),
        ("خمن", "خمن", "خمّن رقماً من 1 إلى 10 بـ 3 محاولات."),
        ("سؤال", "سؤال", "سؤال ثقافي بأربع خيارات."),
        ("كتابة", "كتابة", "اكتب الجملة بأسرع وقت وبدون أخطاء."),
        ("عملة", "عملة [الرهان]", "اختر صورة أو كتابة وضاعف رهانك."),
        "⚔️ الألعاب الثنائية (VS)",
        ("اكس_او", "اكس_او @العضو", "إكس أو كلاسيكية."),
        ("اربعة", "اربعة @العضو", "أربعة تربح (Connect 4)."),
        ("حجرة", "حجرة @العضو", "حجرة ورقة مقص باختيار سري."),
        ("مبارزة", "مبارزة @العضو", "مبارزة بالهجوم والدفاع والعلاج."),
        "🎉 الألعاب الجماعية",
        ("روليت", "روليت", "روليت الموت، آخر ناجٍ يفوز."),
        ("قنبلة", "قنبلة", "مرّر القنبلة قبل أن تنفجر فيك."),
        ("مسابقة", "مسابقة [عدد الأسئلة]", "مسابقة ثقافية، أول من يجاوب يكسب نقطة."),
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
    ("ضبط العاب / الوان", "ضبط العاب #روم  |  ضبط الوان #روم", "روم الألعاب وروم لوحة الألوان."),
    ("ضبط_حظر ...", "ضبط_حظر #روم  (أو طرد، ميوت، تحذير...)", "لوق مستقل لكل أمر إداري."),
    ("انشاء / حذف", "ضبط لفل انشاء  |  ضبط لفل حذف", "ينشئ روماً جديداً ويربطه، أو يلغي الربط."),
])

HELP_ORDER = ["general", "levels", "voice", "economy", "games", "newgames", "ai", "mod", "admin", "xpadmin", "rooms", "structure", "custom", "setup"]
HELP_LOCKED = {"mod", "admin", "xpadmin", "rooms", "structure", "custom", "setup", "ai"}   # أقسام الإدارة

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

def help_home(guild=None, staff=True):
    guild = guild or CUR_GUILD.get()
    name = brand(guild)[0]
    e = E(f"📚 لوحة مساعدة {name}",
          "╭───────────────────╮\n  اختر القسم من القائمة 👇 أو تنقّل بالأزرار\n╰───────────────────╯\n"
          "✦ الأوامر تُكتب **بدون** `!` — مثال: `حظر @عضو السبب`\n🔎 ما لقيت أمرك؟ اضغط **بحث**", PURPLE)
    pub, locked = [], []
    for k in help_keys(staff):
        icon, nm, intro, items = HELP_SECTIONS[k]
        cnt = sum(1 for it in items if not isinstance(it, str))
        (locked if k in HELP_LOCKED else pub).append(f"{icon} **{nm}** — `{cnt}` أمر")
    e.add_field(name="👥 للجميع", value="\n".join(pub) or "—", inline=False)
    if staff and locked:
        e.add_field(name="🔒 للإدارة فقط", value="\n".join(locked), inline=False)
    e.add_field(name="✨ ابدأ من هنا", inline=False,
                value="`R` بروفايلك + لفل الفويس • `توب_فويس` ترتيب الساعات • `مستويات` رتبك • `العاب` الألعاب • `الوان` لونك • `راتب` عملاتك اليومية")
    e.add_field(name="🆕 جديد", inline=False,
                value="⚡ `اكس_بي` إعطاء XP • 🔥 `مضاعف_اكس_بي` • 🎉 `رسالة_لفل` و`تجربة_لفل` • "
                      "📍 `ضبط` لوحة الرومات • 🩺 `فحص_اللفل`")
    return e

def help_embed(key, staff=True):
    icon, name, intro, items = HELP_SECTIONS[key]
    keys = help_keys(staff)
    pos = keys.index(key) + 1 if key in keys else 1
    lock = "\n🔒 *هذا القسم للإدارة فقط.*" if key in HELP_LOCKED else ""
    e = E(f"{icon}  {name}", f"*{intro}*{lock}\n✦ الأوامر تُكتب **بدون** `!` — مثال: `حظر @عضو السبب`\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬", PURPLE)
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
        def flush(text, first_):
            e.add_field(name=f"━━ {title} ━━" if first_ else f"━━ {title} (تابع) ━━", value=text, inline=False)
        for c in cmds:
            line = f"▸ `{c[1]}`\n　↳ {c[2]}\n"
            if chunk and len(chunk) + len(line) > 1000:
                flush(chunk, first)
                chunk, first = "", False
            chunk += line
        if chunk:
            flush(chunk, first)
    e.set_footer(text=f"{footer_text()} • القسم {pos}/{len(keys)} — استخدم ◀️ ▶️")
    return e

class HelpSelect(discord.ui.Select):
    def __init__(self, staff=True):
        opts = [discord.SelectOption(
                    label=("🔒 " if k in HELP_LOCKED else "") + HELP_SECTIONS[k][1][:90], value=k,
                    emoji=HELP_SECTIONS[k][0], description=HELP_SECTIONS[k][2][:90]) for k in help_keys(staff)][:25]
        super().__init__(placeholder="📂 اختر القسم", options=opts, row=0)

    async def callback(self, interaction):
        v = self.view
        v.key = self.values[0]
        CUR_GUILD.set(interaction.guild)
        await interaction.response.edit_message(embed=help_embed(v.key, v.staff), view=v)

class HelpSearchModal(discord.ui.Modal, title="🔎 البحث في الأوامر"):
    query = discord.ui.TextInput(label="اكتب كلمة أو اسم أمر", placeholder="مثال: فويس • حظر • لعبة • نموذج",
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
        await interaction.response.edit_message(embed=help_embed(self.key, self.staff), view=self)

    @discord.ui.button(label="السابق", emoji="◀️", style=discord.ButtonStyle.secondary, row=1)
    async def prev(self, interaction, button):
        await self._go(interaction, -1)

    @discord.ui.button(label="الرئيسية", emoji="🏠", style=discord.ButtonStyle.primary, row=1)
    async def home(self, interaction, button):
        self.key = None
        await interaction.response.edit_message(embed=help_home(interaction.guild, self.staff), view=self)

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
    e = help_home(ctx.guild, staff)
    f = attach_media(e, "help")
    view = HelpView(ctx.author.id, staff)
    view.message = await ctx.send(embed=e, view=view, files=files_of(f))

# ═════════════════════════ نظام الفويس (لفل + ساعات) ═════════════════════════
# • لفل الفويس مستقل تماماً عن لفل الكتابة، ويُحسب فقط من عدد ساعات الجلسات بالفويس.
# • الأمر  R  يعرض بطاقة البروفايل + بطاقة الفويس (لفل الفويس، الساعات، الترتيب).
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
    ("R", "R [@العضو]", "بطاقة البروفايل + بطاقة الفويس (لفل الفويس، الساعات، ترتيبك بالساعات)."),
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
    card = None
    if PIL_OK:
        try:
            av = await asset_bytes(member.display_avatar)
            if av:
                png = await asyncio.to_thread(
                    render_profile, av, member.display_name, lvl, xp, need, entry[2], entry[3],
                    pos, max(len(entries), pos), u["messages"], vmin, u["coins"], len(warns))
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
    e.add_field(name="🏆 المستوى", value=f"`{lvl}`", inline=True)
    e.add_field(name="🥇 الترتيب", value=f"`#{pos}` من {len(entries)}", inline=True)
    e.add_field(name="✨ XP", value=f"`{xp:,}/{need:,}`", inline=True)
    e.add_field(name="💬 الرسائل", value=f"`{u['messages']:,}`", inline=True)
    e.add_field(name="🎙️ الفويس", value=f"لفل `{vc_level_of(vmin)}` • `{fmt_hours(vmin)}`", inline=True)
    e.add_field(name="💰 العملات", value=f"`{u['coins']:,}`", inline=True)
    e.add_field(name="🎮 الألعاب", value=f"لعب `{u['games_played']}` • فوز `{u['games_won']}`", inline=True)
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
        ve, vcard = await build_voice(member)
    if e is None:
        # بطاقة البروفايل + بطاقة الفويس (لفل الفويس والساعات والترتيب) بنفس الرسالة
        return await ctx.send(files=files + ([vcard] if vcard else []), embed=None if vcard else ve)
    if vcard:
        files = list(files) + [vcard]
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
    "العاب": "games_channel", "ألعاب": "games_channel", "الوان": "colors_channel", "ألوان": "colors_channel",
}
NAMES_BY_KEY = {"welcome_channel": WELCOME_NAMES, "level_channel": LEVEL_NAMES, "log_channel": LOG_NAMES,
                "games_channel": GAMES_NAMES, "colors_channel": COLORS_NAMES}
DEFAULT_CH = {
    "welcome_channel": ("👋・الترحيب", "ro"), "level_channel": ("🆙・اللفلات", "ro"),
    "log_channel": ("📜・اللوقات", "private"), "games_channel": ("🎮・الالعاب", "open"),
    "colors_channel": ("🎨・الالوان", "ro"),
}
LOGS_CAT = "📜・سجلات الإدارة"

# لكل مجموعة أوامر إدارية لوق خاص بها (ضبط_<الاسم> #روم)
_SETTINGS_CMDS = ["ضبط", "حماية", "تجهيز", "تعيين_اسم", "تعيين_بايو", "تعيين_افتار", "اعادة_هوية", "اضافة_جيف", "حذف_جيف",
                  "اضافة_منتج", "حذف_منتج", "صورة", "تعيين_خط", "تعيين_صورة_الاعلان", "تعيين_صورة_الجانب",
                  "تعيين_الفلات", "حذف_فلات", "انشاء_رتب_لفل", "حذف_رتب_لفل", "تعيين_نيو_مبر", "رتب_كل_5", "ثيم_الفلات", "اعادة_الفلات",
                  "مزامنة_الرتب", "ذكاء", "ذكاء_روم", "نموذج", "اعدادات_فويس", "تعيين_ساعات", "تلقائي", "صلاة", "جيفاواي", "جيفاواي_جائزة",
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
    ("games_channel", "🎮", "روم الألعاب", "روم مخصص للألعاب"),
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
                "قسم: ✦━ الفويس ━✦\n🔊・عام\nفويس: ألعاب```\n"
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

@bot.command(name="صور")
@commands.guild_only()
@admin_only()
async def media_list(ctx):
    lines = [f"{'🟢' if k in MEDIA_CACHE else '⚪'} `{k}` — {l}" for k, l in MEDIA_LABELS.items()]
    await ctx.send(embed=E("🖼️ مفاتيح الصور", "\n".join(lines[:25])))

@bot.command(name="صورة", aliases=["صوره"])
@commands.guild_only()
@admin_only()
async def media_set(ctx, key: str = None, url: str = None):
    if key in ("حذف", "delete") and url:
        media_remove(url)
        return await ctx.send(f"🗑️ تم حذف صورة `{url}`.")
    if key not in MEDIA_LABELS:
        return await ctx.reply("الاستخدام: `!صورة المفتاح رابط`")
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

# ═════════════════════════ قسم الألعاب ═════════════════════════
ACTIVE = set()

def player_stats(players, winners):
    for m in players:
        db.user(m.id)["games_played"] += 1
    for m in winners:
        db.user(m.id)["games_won"] += 1
    db.mark()

async def reward(member, coins=0, xp=0, channel=None):
    db.user(member.id)["coins"] += coins
    db.mark()
    if xp:
        await grant_xp(member, xp, channel)

async def check_bet(ctx, bet, minimum=10, maximum=10000):
    u = db.user(ctx.author.id)
    if bet < minimum or bet > maximum:
        await ctx.reply(f"❌ الرهان من **{minimum}** إلى **{maximum:,}** عملة.")
        return False
    if bet > u["coins"]:
        await ctx.reply(f"❌ رصيدك `{u['coins']:,}` ما يكفي.")
        return False
    return True

class OwnedView(discord.ui.View):
    def __init__(self, allowed, timeout=120):
        super().__init__(timeout=timeout)
        self.allowed = set(allowed)
        self.message = None

    async def interaction_check(self, interaction):
        CUR_GUILD.set(interaction.guild)
        if interaction.user.id in self.allowed:
            return True
        await interaction.response.send_message("❌ هذي اللعبة مو إلك.", ephemeral=True)
        return False

SLOT_SYMBOLS = ["🍒", "🍋", "🍇", "🔔", "💎", "7️⃣"]
SLOT_WEIGHTS = [30, 26, 20, 12, 8, 4]
SLOT_PAY = {"🍒": 3, "🍋": 4, "🍇": 5, "🔔": 8, "💎": 15, "7️⃣": 30}

def slot_embed(final, text):
    body = "╔═══════════╗\n║  " + "  │  ".join(final) + "  ║\n╚═══════════╝"
    return E("🎰 ماكينة الحظ", f"{body}\n{text}", PURPLE)

QUESTIONS = [
    ("ما عاصمة العراق؟", "بغداد", ["البصرة", "الموصل", "أربيل"]),
    ("ما عاصمة مصر؟", "القاهرة", ["الإسكندرية", "الجيزة", "أسوان"]),
    ("ما عاصمة السعودية؟", "الرياض", ["جدة", "مكة", "الدمام"]),
    ("ما عاصمة اليابان؟", "طوكيو", ["كيوتو", "أوساكا", "سابورو"]),
    ("ما عاصمة فرنسا؟", "باريس", ["ليون", "مرسيليا", "نيس"]),
    ("كم ناتج 12 × 12؟", "144", ["124", "132", "156"]),
    ("كم دقيقة في الساعة؟", "60", ["30", "90", "100"]),
    ("كم عدد ألوان قوس قزح؟", "7", ["5", "6", "8"]),
    ("ما أكبر كوكب في المجموعة الشمسية؟", "المشتري", ["زحل", "المريخ", "الأرض"]),
    ("ما أصغر كوكب في المجموعة الشمسية؟", "عطارد", ["الزهرة", "المريخ", "نبتون"]),
    ("ما أكبر محيط في العالم؟", "الهادئ", ["الأطلسي", "الهندي", "المتجمد"]),
    ("ما أسرع حيوان بري؟", "الفهد", ["الأسد", "الحصان", "النمر"]),
    ("ما الغاز الذي يحتاجه الإنسان ليتنفس؟", "الأكسجين", ["النيتروجين", "الهيدروجين", "الهيليوم"]),
]

SENTENCES = [
    "المملكة تحتاج الى ملوك لا يعرفون الخوف",
    "من جد وجد ومن زرع حصد",
    "العلم نور والجهل ظلام",
    "الصبر مفتاح الفرج",
    "نكسب المجد بالعمل والاجتهاد",
]

def valid_opponent(ctx, opp):
    return isinstance(opp, discord.Member) and not opp.bot and opp.id != ctx.author.id

# ───── ألغام ─────
class MineTile(discord.ui.Button):
    def __init__(self, idx):
        super().__init__(emoji="⬛", style=discord.ButtonStyle.secondary, row=idx // 5)
        self.idx = idx

    async def callback(self, interaction):
        v = self.view
        if v.done:
            return await interaction.response.defer()
        if self.idx in v.mines:
            self.emoji, self.style = "💥", discord.ButtonStyle.danger
            await v.finish(interaction, False, self.idx)
        else:
            self.emoji, self.style, self.disabled = "💎", discord.ButtonStyle.success, True
            v.opened += 1
            if v.opened >= v.MAX_GEMS:
                await v.finish(interaction, True)
            else:
                await interaction.response.edit_message(embed=v.embed("💎 جوهرة! كمّل أو انسحب."), view=v)

class MineCash(discord.ui.Button):
    def __init__(self):
        super().__init__(label="سحب الأرباح", emoji="💰", style=discord.ButtonStyle.primary, row=3)

    async def callback(self, interaction):
        v = self.view
        if not v.done:
            await v.finish(interaction, True)

class MinesView(OwnedView):
    MAX_GEMS = 6

    def __init__(self, ctx, bet):
        super().__init__([ctx.author.id], timeout=90)
        self.ctx, self.bet = ctx, bet
        self.mines = set(random.sample(range(15), 3))
        self.opened = 0
        self.done = False
        for i in range(15):
            self.add_item(MineTile(i))
        self.add_item(MineCash())

    def mult(self):
        if not self.opened:
            return 1.0
        p = 1.0
        for i in range(self.opened):
            p *= (12 - i) / (15 - i)
        return round(0.95 / p, 2)

    def embed(self, text):
        return E("💣 الألغام", f"{text}\nالرهان `{self.bet:,}` • الجواهر `{self.opened}/{self.MAX_GEMS}` • المضاعف `x{self.mult()}`", PURPLE)

    def _lock(self, hit=None):
        self.done = True
        self.stop()
        for c in self.children:
            c.disabled = True
            if isinstance(c, MineTile) and c.idx in self.mines and c.idx != hit:
                c.emoji = "💣"

    async def finish(self, interaction, won, hit=None):
        self._lock(hit)
        a = self.ctx.author
        if won:
            pay = int(self.bet * self.mult())
            db.user(a.id)["coins"] += pay
            player_stats([a], [a] if pay > self.bet else [])
            text = f"💰 سحبت **{pay:,}** عملة"
        else:
            player_stats([a], [])
            text = "💥 انفجر لغم! خسرت الرهان."
        db.mark()
        await interaction.response.edit_message(embed=self.embed(text), view=self)

    async def on_timeout(self):
        if self.done:
            return
        self._lock()
        pay = int(self.bet * self.mult())
        db.user(self.ctx.author.id)["coins"] += pay
        db.mark()
        if self.message:
            try:
                await self.message.edit(embed=self.embed(f"⏰ انتهى الوقت — استرجعت `{pay:,}` عملة"), view=self)
            except discord.HTTPException:
                pass

# ───── خمن ─────
class GuessBtn(discord.ui.Button):
    def __init__(self, n):
        super().__init__(label=str(n), style=discord.ButtonStyle.secondary, row=(n - 1) // 5)
        self.n = n

    async def callback(self, interaction):
        v = self.view
        v.tries -= 1
        self.disabled = True
        if self.n == v.number:
            v.over = True
            v.stop()
            for c in v.children:
                c.disabled = True
            await interaction.response.edit_message(embed=E("🎉 صح!", f"الرقم كان **{v.number}** — ربحت 80 عملة", GOLD), view=v)
            player_stats([v.ctx.author], [v.ctx.author])
            await reward(v.ctx.author, 80, 15, v.ctx.channel)
        elif v.tries <= 0:
            v.over = True
            v.stop()
            for c in v.children:
                c.disabled = True
            player_stats([v.ctx.author], [])
            await interaction.response.edit_message(embed=E("😢 خسرت", f"الرقم كان **{v.number}**", 0xE74C3C), view=v)
        else:
            hint = "⬆️ الرقم **أكبر**" if v.number > self.n else "⬇️ الرقم **أصغر**"
            await interaction.response.edit_message(embed=E("🔢 خمّن الرقم (1-10)", f"{hint}\nباقي **{v.tries}** محاولات", PURPLE), view=v)

class GuessView(OwnedView):
    def __init__(self, ctx):
        super().__init__([ctx.author.id], timeout=60)
        self.ctx = ctx
        self.number = random.randint(1, 10)
        self.tries = 3
        self.over = False
        for i in range(1, 11):
            self.add_item(GuessBtn(i))

    async def on_timeout(self):
        if self.over:
            return
        for c in self.children:
            c.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass

# ───── سؤال ─────
class QuizBtn(discord.ui.Button):
    def __init__(self, text, correct):
        super().__init__(label=text[:80], style=discord.ButtonStyle.secondary)
        self.text, self.correct = text, correct

    async def callback(self, interaction):
        v = self.view
        v.done = True
        v.stop()
        for c in v.children:
            c.disabled = True
            if c.correct:
                c.style = discord.ButtonStyle.success
        if not self.correct:
            self.style = discord.ButtonStyle.danger
        a = v.ctx.author
        if self.correct:
            await interaction.response.edit_message(embed=E("✅ إجابة صحيحة", "ربحت 60 عملة 🎉", GOLD), view=v)
            player_stats([a], [a])
            await reward(a, 60, 20, v.ctx.channel)
        else:
            await interaction.response.edit_message(embed=E("❌ إجابة خاطئة", f"الصحيح: **{v.q[1]}**", 0xE74C3C), view=v)
            player_stats([a], [])

class SoloQuizView(OwnedView):
    def __init__(self, ctx, q):
        super().__init__([ctx.author.id], timeout=20)
        self.ctx, self.q, self.done = ctx, q, False
        opts = [q[1]] + list(q[2])
        random.shuffle(opts)
        for o in opts:
            self.add_item(QuizBtn(o, o == q[1]))

    async def on_timeout(self):
        if self.done:
            return
        for c in self.children:
            c.disabled = True
        if self.message:
            try:
                await self.message.edit(embed=E("⏰ انتهى الوقت", f"الجواب: **{self.q[1]}**", 0xE74C3C), view=self)
            except discord.HTTPException:
                pass

# ───── عملة ─────
class CoinView(OwnedView):
    def __init__(self, ctx, bet):
        super().__init__([ctx.author.id], timeout=45)
        self.ctx, self.bet, self.done = ctx, bet, False

    async def flip(self, interaction, choice):
        self.done = True
        self.stop()
        for c in self.children:
            c.disabled = True
        a = self.ctx.author
        res = random.choice(["صورة", "كتابة"])
        if res == choice:
            db.user(a.id)["coins"] += self.bet * 2
            text = f"🎉 طلعت **{res}**! ربحت `{self.bet:,}` عملة"
            player_stats([a], [a])
        else:
            text = f"😢 طلعت **{res}**... خسرت `{self.bet:,}` عملة"
            player_stats([a], [])
        db.mark()
        await interaction.response.edit_message(embed=E("🪙 قلب العملة", text, GOLD), view=self)

    @discord.ui.button(label="صورة", emoji="🪙", style=discord.ButtonStyle.primary)
    async def heads(self, interaction, button):
        await self.flip(interaction, "صورة")

    @discord.ui.button(label="كتابة", emoji="📜", style=discord.ButtonStyle.primary)
    async def tails(self, interaction, button):
        await self.flip(interaction, "كتابة")

    async def on_timeout(self):
        if self.done:
            return
        self.done = True
        db.user(self.ctx.author.id)["coins"] += self.bet
        db.mark()
        for c in self.children:
            c.disabled = True
        if self.message:
            try:
                await self.message.edit(embed=E("⏰ انتهى الوقت", "تم استرجاع رهانك.", 0x95A5A6), view=self)
            except discord.HTTPException:
                pass

# ───── ألعاب ثنائية ─────
class TurnView(OwnedView):
    def __init__(self, ctx, p1, p2, timeout=180):
        super().__init__([p1.id, p2.id], timeout)
        self.ctx = ctx
        self.players = [p1, p2]
        self.turn = 0
        self.over = False

    @property
    def current(self):
        return self.players[self.turn]

    def lock(self):
        self.over = True
        for c in self.children:
            c.disabled = True
        self.stop()

    async def settle(self, winner_idx):
        player_stats(self.players, [] if winner_idx is None else [self.players[winner_idx]])
        if winner_idx is not None:
            await reward(self.players[winner_idx], 60, 25, self.ctx.channel)

    async def on_timeout(self):
        if self.over:
            return
        self.over = True
        for c in self.children:
            c.disabled = True
        if self.message:
            try:
                await self.message.edit(content="⏰ انتهى وقت اللعبة.", view=self)
            except discord.HTTPException:
                pass

async def not_your_turn(interaction):
    await interaction.response.send_message("⏳ مو دورك.", ephemeral=True)

# اكس او
class XOCell(discord.ui.Button):
    def __init__(self, i):
        super().__init__(label="\u200b", style=discord.ButtonStyle.secondary, row=i // 3)
        self.i = i

    async def callback(self, interaction):
        v = self.view
        if interaction.user.id != v.current.id:
            return await not_your_turn(interaction)
        self.label = None
        self.emoji = "❌" if v.turn == 0 else "⭕"
        self.style = discord.ButtonStyle.danger if v.turn == 0 else discord.ButtonStyle.primary
        self.disabled = True
        v.board[self.i] = v.turn
        w = v.winner()
        if w is not None:
            v.lock()
            await interaction.response.edit_message(embed=E("🏆 إكس أو", f"الفائز {v.players[w].mention} 🎉 (+60 عملة)", GOLD), view=v)
            return await v.settle(w)
        if all(x is not None for x in v.board):
            v.lock()
            await interaction.response.edit_message(embed=E("🤝 تعادل", "ما في فائز هالمرة.", 0x95A5A6), view=v)
            return await v.settle(None)
        v.turn ^= 1
        await interaction.response.edit_message(embed=v.status(), view=v)

class XOView(TurnView):
    LINES = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)]

    def __init__(self, ctx, p1, p2):
        super().__init__(ctx, p1, p2)
        self.board = [None] * 9
        for i in range(9):
            self.add_item(XOCell(i))

    def status(self):
        a, b = self.players
        return E("❌⭕ إكس أو", f"❌ {a.mention} • ⭕ {b.mention}\n🎯 الدور: {self.current.mention}", PURPLE)

    def winner(self):
        for a, b, c in self.LINES:
            if self.board[a] is not None and self.board[a] == self.board[b] == self.board[c]:
                return self.board[a]
        return None

# أربعة
class C4Btn(discord.ui.Button):
    def __init__(self, col):
        super().__init__(label=str(col + 1), style=discord.ButtonStyle.secondary, row=col // 5)
        self.col = col

    async def callback(self, interaction):
        v = self.view
        if interaction.user.id != v.current.id:
            return await not_your_turn(interaction)
        r = v.drop(self.col)
        if r is None:
            self.disabled = True
            return await interaction.response.send_message("❌ العمود ممتلئ.", ephemeral=True)
        if v.grid[0][self.col] is not None:
            self.disabled = True
        if v.wins(r, self.col):
            v.lock()
            w = v.turn
            await interaction.response.edit_message(
                embed=E("🏆 أربعة تربح", f"الفائز {v.players[w].mention} 🎉 (+60 عملة)\n\n{v.render()}", GOLD), view=v)
            return await v.settle(w)
        if all(x is not None for x in v.grid[0]):
            v.lock()
            await interaction.response.edit_message(embed=E("🤝 تعادل", v.render(), 0x95A5A6), view=v)
            return await v.settle(None)
        v.turn ^= 1
        await interaction.response.edit_message(embed=v.status(), view=v)

class C4View(TurnView):
    def __init__(self, ctx, p1, p2):
        super().__init__(ctx, p1, p2, timeout=300)
        self.grid = [[None] * 7 for _ in range(6)]
        for c in range(7):
            self.add_item(C4Btn(c))

    def render(self):
        sym = {None: "⚪", 0: "🔴", 1: "🟡"}
        rows = "\n".join("".join(sym[x] for x in row) for row in self.grid)
        return rows + "\n1️⃣2️⃣3️⃣4️⃣5️⃣6️⃣7️⃣"

    def status(self):
        a, b = self.players
        return E("🔴🟡 أربعة تربح", f"🔴 {a.mention} • 🟡 {b.mention}\n🎯 الدور: {self.current.mention}\n\n{self.render()}", PURPLE)

    def drop(self, col):
        for r in range(5, -1, -1):
            if self.grid[r][col] is None:
                self.grid[r][col] = self.turn
                return r
        return None

    def wins(self, r, c):
        p = self.grid[r][c]
        for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
            n = 1
            for s in (1, -1):
                rr, cc = r + dr * s, c + dc * s
                while 0 <= rr < 6 and 0 <= cc < 7 and self.grid[rr][cc] == p:
                    n += 1
                    rr += dr * s
                    cc += dc * s
            if n >= 4:
                return True
        return False

# حجرة ورقة مقص
class RPSBtn(discord.ui.Button):
    def __init__(self, key, emoji, name):
        super().__init__(label=name, emoji=emoji, style=discord.ButtonStyle.primary)
        self.key = key

    async def callback(self, interaction):
        v = self.view
        uid = interaction.user.id
        if uid in v.picks:
            return await interaction.response.send_message("✅ اخترت مسبقاً.", ephemeral=True)
        v.picks[uid] = self.key
        if len(v.picks) < 2:
            return await interaction.response.send_message(f"✅ اخترت **{self.label}** — انتظر خصمك.", ephemeral=True)
        a, b = v.players
        ka, kb = v.picks[a.id], v.picks[b.id]
        em = {k: v.CH[k][0] for k in v.CH}
        v.lock()
        if ka == kb:
            w, text = None, "🤝 تعادل!"
        elif v.BEATS[ka] == kb:
            w, text = 0, f"🏆 الفائز {a.mention} (+60 عملة)"
        else:
            w, text = 1, f"🏆 الفائز {b.mention} (+60 عملة)"
        await interaction.response.edit_message(
            embed=E("✊✋✌️ النتيجة", f"{a.mention} {em[ka]}  ⚔️  {em[kb]} {b.mention}\n\n{text}", GOLD), view=v)
        await v.settle(w)

class RPSView(TurnView):
    CH = {"rock": ("✊", "حجرة"), "paper": ("✋", "ورقة"), "scissors": ("✌️", "مقص")}
    BEATS = {"rock": "scissors", "paper": "rock", "scissors": "paper"}

    def __init__(self, ctx, p1, p2):
        super().__init__(ctx, p1, p2, timeout=90)
        self.picks = {}
        for k, (emo, name) in self.CH.items():
            self.add_item(RPSBtn(k, emo, name))

    def status(self):
        a, b = self.players
        return E("✊✋✌️ حجرة ورقة مقص", f"{a.mention} ⚔️ {b.mention}\nكل واحد يختار سراً 👀", PURPLE)

# مبارزة
class DuelBtn(discord.ui.Button):
    def __init__(self, kind, label, emoji, style):
        super().__init__(label=label, emoji=emoji, style=style)
        self.kind = kind

    async def callback(self, interaction):
        v = self.view
        if interaction.user.id != v.current.id:
            return await not_your_turn(interaction)
        me, foe = v.turn, 1 - v.turn
        name = v.players[me].display_name
        if self.kind == "attack":
            dmg = random.randint(15, 25)
            if v.shield[foe]:
                dmg //= 2
                v.shield[foe] = False
            v.hp[foe] = max(0, v.hp[foe] - dmg)
            v.log = f"⚔️ {name} ضرب بـ **{dmg}**"
        elif self.kind == "defend":
            v.shield[me] = True
            v.log = f"🛡️ {name} رفع الدرع"
        else:
            if v.heals[me] <= 0:
                return await interaction.response.send_message("❌ ما بقي عندك علاج.", ephemeral=True)
            v.heals[me] -= 1
            amt = random.randint(10, 20)
            v.hp[me] = min(100, v.hp[me] + amt)
            v.log = f"💊 {name} تعالج **+{amt}**"
        if v.hp[foe] <= 0:
            v.lock()
            await interaction.response.edit_message(
                embed=E("🏆 نهاية المبارزة", f"{v.log}\nالفائز {v.players[me].mention} 👑 (+60 عملة)", GOLD), view=v)
            return await v.settle(me)
        v.turn = foe
        await interaction.response.edit_message(embed=v.embed(), view=v)

class DuelView(TurnView):
    def __init__(self, ctx, p1, p2):
        super().__init__(ctx, p1, p2, timeout=240)
        self.hp = [100, 100]
        self.shield = [False, False]
        self.heals = [2, 2]
        self.log = "⚔️ بدأت المبارزة!"
        self.add_item(DuelBtn("attack", "هجوم", "⚔️", discord.ButtonStyle.danger))
        self.add_item(DuelBtn("defend", "دفاع", "🛡️", discord.ButtonStyle.primary))
        self.add_item(DuelBtn("heal", "علاج", "💊", discord.ButtonStyle.success))

    def embed(self):
        lines = []
        for i in (0, 1):
            sh = " 🛡️" if self.shield[i] else ""
            lines.append(f"{self.players[i].mention} ❤️ `{self.hp[i]}/100` {bar(self.hp[i] / 100, 10, '🟥', '⬛')}{sh}")
        return E("⚔️ مبارزة الملوك", "\n".join(lines) + f"\n\n{self.log}\n🎯 الدور: {self.current.mention}", PURPLE)

# ───── لوبي الألعاب الجماعية ─────
class LobbyView(discord.ui.View):
    def __init__(self, host, title, mn, mx):
        super().__init__(timeout=45)
        self.host, self.title, self.mn, self.mx = host, title, mn, mx
        self.players = [host]

    def embed(self):
        names = "\n".join(f"• {m.mention}" for m in self.players)
        return E(self.title, f"اضغط **انضمام** — الحد الأدنى `{self.mn}` والأقصى `{self.mx}`\n"
                 f"المضيف {self.host.mention} يضغط **ابدأ** (أو تبدأ تلقائياً بعد 45 ثانية).\n\n👥 اللاعبون ({len(self.players)}):\n{names}", PURPLE)

    @discord.ui.button(label="انضمام", emoji="✅", style=discord.ButtonStyle.success)
    async def join(self, interaction, button):
        if interaction.user.bot or any(m.id == interaction.user.id for m in self.players):
            return await interaction.response.send_message("أنت منضم مسبقاً.", ephemeral=True)
        if len(self.players) >= self.mx:
            return await interaction.response.send_message("❌ اللوبي ممتلئ.", ephemeral=True)
        self.players.append(interaction.user)
        await interaction.response.edit_message(embed=self.embed(), view=self)

    @discord.ui.button(label="ابدأ", emoji="▶️", style=discord.ButtonStyle.primary)
    async def start(self, interaction, button):
        if interaction.user.id != self.host.id:
            return await interaction.response.send_message("❌ فقط المضيف يبدأ.", ephemeral=True)
        if len(self.players) < self.mn:
            return await interaction.response.send_message(f"❌ تحتاج {self.mn} لاعبين على الأقل.", ephemeral=True)
        await interaction.response.defer()
        self.stop()

async def run_lobby(ctx, title, mn, mx):
    view = LobbyView(ctx.author, title, mn, mx)
    msg = await ctx.send(embed=view.embed(), view=view)
    await view.wait()
    for c in view.children:
        c.disabled = True
    try:
        await msg.edit(view=view)
    except discord.HTTPException:
        pass
    if len(view.players) < mn:
        await ctx.send(f"❌ ما اكتمل العدد ({mn} لاعبين على الأقل).")
        return None
    return view.players

class BombPass(discord.ui.View):
    def __init__(self, holder, others, timeout):
        super().__init__(timeout=timeout)
        self.holder, self.target = holder, None
        sel = discord.ui.Select(placeholder="اختر من تمرر له القنبلة",
                                options=[discord.SelectOption(label=m.display_name[:100], value=str(m.id)) for m in others])
        sel.callback = self.pick
        self.add_item(sel)

    async def interaction_check(self, interaction):
        if interaction.user.id == self.holder.id:
            return True
        await interaction.response.send_message("❌ القنبلة مو معاك.", ephemeral=True)
        return False

    async def pick(self, interaction):
        self.target = int(self.children[0].values[0])
        await interaction.response.defer()
        self.stop()

# ───── أوامر الألعاب ─────
@bot.command(name="العاب", aliases=["ألعاب", "games"])
@commands.guild_only()
async def games_hub(ctx):
    e = E("🎮 مدينة الألعاب الملكية", "العب، اربح عملات 💰 وXP، وتنافس مع أصحابك!\n"
          "رصيدك: `{:,}` عملة".format(db.user(ctx.author.id)["coins"]), PURPLE)
    e.add_field(name="🧍 فردي", value="`سلوت 100` • `ألغام 100` • `خمن` • `سؤال` • `كتابة` • `عملة 100`", inline=False)
    e.add_field(name="⚔️ ثنائي (VS)", value="`اكس_او @عضو` • `اربعة @عضو` • `حجرة @عضو` • `مبارزة @عضو`", inline=False)
    e.add_field(name="🎉 جماعي", value="`روليت` • `قنبلة` • `مسابقة 5`", inline=False)
    e.add_field(name="🆕 ألعاب جديدة", inline=False,
                value="🧩 `ألغاز` • 🕵️ `برا_السالفة` • 🔪 `مافيا` • 🖼️ `كود_نيمز` (لوحة صور + مفتاح سري)")
    f = attach_media(e, "games")
    await ctx.send(embed=e, files=files_of(f))

# سلوت
@bot.command(name="سلوت", aliases=["slots"])
@commands.guild_only()
@commands.cooldown(1, 6, commands.BucketType.user)
async def slots_cmd(ctx, bet: int = 50):
    if not await check_bet(ctx, bet):
        return
    u = db.user(ctx.author.id)
    u["coins"] -= bet
    final = random.choices(SLOT_SYMBOLS, SLOT_WEIGHTS, k=3)
    kinds = len(set(final))
    pay = bet * SLOT_PAY[final[0]] if kinds == 1 else (int(bet * 1.5) if kinds == 2 else 0)
    u["coins"] += pay
    player_stats([ctx.author], [ctx.author] if pay > bet else [])
    await ctx.send(embed=slot_embed(final, f"💰 النتيجة: {'ربحت ' + str(pay) if pay else 'خسرت'}"))

# ألغام
@bot.command(name="ألغام", aliases=["الغام", "mines"])
@commands.guild_only()
@commands.cooldown(1, 8, commands.BucketType.user)
async def mines_cmd(ctx, bet: int = 100):
    if not await check_bet(ctx, bet, maximum=2000):
        return
    db.user(ctx.author.id)["coins"] -= bet
    db.mark()
    view = MinesView(ctx, bet)
    view.message = await ctx.send(embed=view.embed("اضغط على المربعات وجمّع الجواهر 💎"), view=view)

# خمن الرقم
@bot.command(name="خمن")
@commands.guild_only()
@commands.cooldown(1, 8, commands.BucketType.user)
async def guess_cmd(ctx):
    view = GuessView(ctx)
    view.message = await ctx.send(embed=E("🔢 خمّن الرقم (1-10)", "عندك **3** محاولات!", PURPLE), view=view)

# سؤال
@bot.command(name="سؤال")
@commands.guild_only()
@commands.cooldown(1, 10, commands.BucketType.user)
async def quiz_cmd(ctx):
    q = random.choice(QUESTIONS)
    view = SoloQuizView(ctx, q)
    view.message = await ctx.send(embed=E("🧠 سؤال ثقافي", f"**{q[0]}**\n⏱️ عندك 20 ثانية", PURPLE), view=view)

# مسابقة جماعية
@bot.command(name="مسابقة", aliases=["مسابقه"])
@commands.guild_only()
async def group_quiz(ctx, rounds: int = 5):
    if ctx.channel.id in ACTIVE:
        return await ctx.reply("⏳ في لعبة شغالة بهالروم.")
    rounds = max(1, min(rounds, len(QUESTIONS)))
    ACTIVE.add(ctx.channel.id)
    try:
        await ctx.send(embed=E("🏆 مسابقة المملكة", f"**{rounds}** أسئلة — أول من يكتب الإجابة الصحيحة يكسب نقطة!\nتبدأ بعد 5 ثواني...", GOLD))
        await asyncio.sleep(5)
        scores = defaultdict(int)
        for i, (q, ans, _) in enumerate(random.sample(QUESTIONS, rounds), 1):
            await ctx.send(embed=E(f"❓ السؤال {i}/{rounds}", f"**{q}**\n⏱️ 20 ثانية", PURPLE))

            def check(m, ans=ans):
                return m.channel.id == ctx.channel.id and not m.author.bot and m.content.strip().lower() == ans.lower()
            try:
                m = await bot.wait_for("message", check=check, timeout=20)
                scores[m.author] += 1
                await ctx.send(f"✅ {m.author.mention} جاوب صح: **{ans}**")
            except asyncio.TimeoutError:
                await ctx.send(f"⏰ انتهى الوقت! الجواب: **{ans}**")
            await asyncio.sleep(2)
        ranking = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        if not ranking:
            return await ctx.send("😴 ما أحد جاوب على أي سؤال.")
        medals = ["🥇", "🥈", "🥉"] + ["🔹"] * 20
        prizes = (150, 100, 50)
        lines = [f"{medals[i]} {m.mention} — `{s}` نقطة" + (f" • +{prizes[i]} عملة" if i < 3 else "")
                 for i, (m, s) in enumerate(ranking[:10])]
        await ctx.send(embed=E("🏁 نتائج المسابقة", "\n".join(lines), GOLD))
        player_stats([m for m, _ in ranking], [ranking[0][0]])
        for i, (m, _) in enumerate(ranking[:3]):
            await reward(m, prizes[i], 20, ctx.channel)
    finally:
        ACTIVE.discard(ctx.channel.id)

# كتابة
@bot.command(name="كتابة", aliases=["سرعة"])
@commands.guild_only()
@commands.cooldown(1, 15, commands.BucketType.user)
async def typing_cmd(ctx):
    s = random.choice(SENTENCES)
    await ctx.send(embed=E("⌨️ سرعة الكتابة", f"اكتب هذه الجملة:\n`{s}`"))
    def check(m):
        return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
    try:
        m = await bot.wait_for("message", check=check, timeout=30)
    except asyncio.TimeoutError:
        return await ctx.send("⏰ انتهى الوقت!")
    if m.content.strip() == s:
        await reward(ctx.author, 50, 20, ctx.channel)
        await ctx.send("✅ ممتاز، ربحت 50 عملة!")
    else:
        await ctx.send("❌ خطأ بالكتابة.")

# عملة
@bot.command(name="عملة")
@commands.guild_only()
@commands.cooldown(1, 6, commands.BucketType.user)
async def coin_cmd(ctx, bet: int = 50):
    if not await check_bet(ctx, bet):
        return
    db.user(ctx.author.id)["coins"] -= bet
    db.mark()
    view = CoinView(ctx, bet)
    view.message = await ctx.send(embed=E("🪙 قلب العملة", f"رهان `{bet:,}` — اختر وجهك!", PURPLE), view=view)

# اكس او
@bot.command(name="اكس_او", aliases=["xo"])
@commands.guild_only()
async def xo_cmd(ctx, opponent: discord.Member):
    if not valid_opponent(ctx, opponent):
        return await ctx.reply("❌ اختار عضو حقيقي.")
    view = XOView(ctx, ctx.author, opponent)
    view.message = await ctx.send(content=opponent.mention, embed=view.status(), view=view)

# أربعة
@bot.command(name="اربعة", aliases=["c4"])
@commands.guild_only()
async def c4_cmd(ctx, opponent: discord.Member):
    if not valid_opponent(ctx, opponent):
        return await ctx.reply("❌ اختار عضو حقيقي.")
    view = C4View(ctx, ctx.author, opponent)
    view.message = await ctx.send(content=opponent.mention, embed=view.status(), view=view)

# حجرة
@bot.command(name="حجرة", aliases=["rps"])
@commands.guild_only()
async def rps_cmd(ctx, opponent: discord.Member):
    if not valid_opponent(ctx, opponent):
        return await ctx.reply("❌ اختار عضو حقيقي.")
    view = RPSView(ctx, ctx.author, opponent)
    view.message = await ctx.send(content=opponent.mention, embed=view.status(), view=view)

# مبارزة
@bot.command(name="مبارزة", aliases=["duel"])
@commands.guild_only()
async def duel_cmd(ctx, opponent: discord.Member):
    if not valid_opponent(ctx, opponent):
        return await ctx.reply("❌ اختار عضو حقيقي.")
    view = DuelView(ctx, ctx.author, opponent)
    view.message = await ctx.send(content=opponent.mention, embed=view.embed(), view=view)

# روليت
@bot.command(name="روليت", aliases=["roulette"])
@commands.guild_only()
async def roulette_cmd(ctx):
    if ctx.channel.id in ACTIVE:
        return await ctx.reply("⏳ في لعبة شغالة بهالروم.")
    ACTIVE.add(ctx.channel.id)
    try:
        players = await run_lobby(ctx, "🔫 روليت الموت", 2, 10)
        if not players:
            return
        alive = players[:]
        random.shuffle(alive)
        bullet, pulls, idx = random.randint(1, 6), 0, 0
        await ctx.send(f"🔫 بدأت الروليت بين **{len(alive)}** لاعبين... الله يستر!")
        while len(alive) > 1:
            p = idx % len(alive)
            m = alive[p]
            await ctx.send(f"🔫 {m.mention} يرفع المسدس... 😰")
            await asyncio.sleep(2.5)
            pulls += 1
            if pulls == bullet:
                alive.remove(m)
                idx = p
                bullet, pulls = random.randint(1, 6), 0
                await ctx.send(f"💥 **بوم!** {m.mention} طلع من اللعبة ☠️ — باقي **{len(alive)}**")
            else:
                idx += 1
                await ctx.send("🔘 *كليك*... نجا ✅")
            await asyncio.sleep(1.5)
        winner = alive[0]
        prize = 80 * len(players)
        player_stats(players, [winner])
        await reward(winner, prize, 30, ctx.channel)
        await ctx.send(embed=E("🏆 آخر ناجٍ", f"{winner.mention} فاز بالروليت 👑\n+**{prize:,}** عملة", GOLD))
    finally:
        ACTIVE.discard(ctx.channel.id)

# قنبلة
@bot.command(name="قنبلة", aliases=["bomb", "قنبله"])
@commands.guild_only()
async def bomb_cmd(ctx):
    if ctx.channel.id in ACTIVE:
        return await ctx.reply("⏳ في لعبة شغالة بهالروم.")
    ACTIVE.add(ctx.channel.id)
    try:
        players = await run_lobby(ctx, "💣 مرّر القنبلة", 3, 10)
        if not players:
            return
        alive = players[:]
        holder = random.choice(alive)
        await ctx.send("💣 بدأت اللعبة! القنبلة تنفجر بوقت مجهول، مرّرها بسرعة!")
        while len(alive) > 1:
            explode_at = time.time() + random.uniform(15, 35)
            while True:
                left = explode_at - time.time()
                if left <= 0:
                    break
                others = [m for m in alive if m.id != holder.id]
                view = BombPass(holder, others, min(left, 12))
                msg = await ctx.send(f"💣 القنبلة مع {holder.mention}! اختر من تمرر له ⏱️", view=view)
                await view.wait()
                try:
                    await msg.delete()
                except discord.HTTPException:
                    pass
                if time.time() >= explode_at or view.target is None:
                    break
                holder = next(m for m in others if m.id == view.target)
            alive.remove(holder)
            await ctx.send(f"💥 **بووم!** القنبلة انفجرت بـ {holder.mention} ☠️ — باقي **{len(alive)}**")
            await asyncio.sleep(2)
            if len(alive) > 1:
                holder = random.choice(alive)
        winner = alive[0]
        prize = 70 * len(players)
        player_stats(players, [winner])
        await reward(winner, prize, 30, ctx.channel)
        await ctx.send(embed=E("🏆 الناجي الأخير", f"{winner.mention} نجا من القنبلة 👑\n+**{prize:,}** عملة", GOLD))
    finally:
        ACTIVE.discard(ctx.channel.id)

# ───── رسم أيقونات كود نيمز (صور مرسومة برمجياً، لا تحتاج إنترنت ولا خطوط) ─────
def _star_pts(cx, cy, ro, ri, n=5, rot=-90):
    pts = []
    for i in range(n * 2):
        a = math.radians(rot + i * 180 / n)
        r = ro if i % 2 == 0 else ri
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts

class _Pen:
    """يرسم بإحداثيات 0..100 على لوحة مكبّرة ثم تُصغَّر لنعومة الحواف."""
    def __init__(self, d, k=4):
        self.d, self.k = d, k
    def _p(self, ps):
        return [(x * self.k, y * self.k) for x, y in ps]
    def poly(self, ps, fill=None, outline=None, w=1.5):
        self.d.polygon(self._p(ps), fill=fill, outline=outline, width=max(1, int(w * self.k)) if outline else 1)
    def ell(self, x0, y0, x1, y1, fill=None, outline=None, w=1.5):
        k = self.k
        self.d.ellipse([x0 * k, y0 * k, x1 * k, y1 * k], fill=fill, outline=outline,
                       width=max(1, int(w * k)) if outline else 1)
    def circ(self, cx, cy, r, fill=None, outline=None, w=1.5):
        self.ell(cx - r, cy - r, cx + r, cy + r, fill, outline, w)
    def rect(self, x0, y0, x1, y1, fill=None, outline=None, w=1.5, r=0):
        k = self.k
        if r:
            self.d.rounded_rectangle([x0 * k, y0 * k, x1 * k, y1 * k], radius=r * k, fill=fill, outline=outline,
                                     width=max(1, int(w * k)) if outline else 1)
        else:
            self.d.rectangle([x0 * k, y0 * k, x1 * k, y1 * k], fill=fill, outline=outline,
                             width=max(1, int(w * k)) if outline else 1)
    def line(self, ps, fill, w=3):
        self.d.line(self._p(ps), fill=fill, width=max(1, int(w * self.k)), joint="curve")
    def arc(self, x0, y0, x1, y1, a0, a1, fill, w=3):
        k = self.k
        self.d.arc([x0 * k, y0 * k, x1 * k, y1 * k], a0, a1, fill=fill, width=max(1, int(w * k)))
    def pie(self, x0, y0, x1, y1, a0, a1, fill, outline=None, w=1.5):
        k = self.k
        self.d.pieslice([x0 * k, y0 * k, x1 * k, y1 * k], a0, a1, fill=fill, outline=outline,
                        width=max(1, int(w * k)) if outline else 1)

_INK = (40, 36, 60)

def _i_star(p):
    p.poly(_star_pts(50, 53, 46, 19), (255, 205, 50), _INK, 2)
def _i_heart(p):
    p.circ(33, 36, 21, (230, 50, 80)); p.circ(67, 36, 21, (230, 50, 80))
    p.poly([(13, 44), (87, 44), (50, 90)], (230, 50, 80))
    p.circ(27, 30, 6, (255, 150, 170))
def _i_moon(p):
    p.circ(50, 50, 40, (250, 220, 110), _INK, 2)
    p.circ(66, 42, 33, (0, 0, 0, 0))
    p.circ(30, 30, 3, (255, 245, 200))
def _i_sun(p):
    for i in range(8):
        a = math.radians(i * 45)
        p.line([(50 + 28 * math.cos(a), 50 + 28 * math.sin(a)), (50 + 45 * math.cos(a), 50 + 45 * math.sin(a))], (255, 160, 30), 6)
    p.circ(50, 50, 22, (255, 200, 40), (230, 120, 20), 2.5)
def _i_cloud(p):
    c, o = (238, 244, 253), (110, 140, 185)
    for col, g in ((o, 3), (c, 0)):
        p.circ(32, 60, 18 + g, col); p.circ(54, 44, 24 + g, col); p.circ(74, 60, 18 + g, col)
        p.rect(30 - g, 58 - g, 76 + g, 78 + g, col, r=10)
def _i_bolt(p):
    p.poly([(60, 4), (22, 56), (45, 56), (34, 96), (80, 38), (55, 38)], (255, 215, 40), (200, 130, 10), 2.5)
def _i_tree(p):
    p.rect(44, 70, 56, 96, (120, 78, 40))
    for y, w in ((8, 26), (28, 34), (48, 42)):
        p.poly([(50, y), (50 - w, y + 34), (50 + w, y + 34)], (40, 150, 70), (20, 100, 45), 2)
def _i_house(p):
    p.rect(18, 46, 82, 90, (250, 225, 170), _INK, 2)
    p.poly([(8, 50), (50, 12), (92, 50)], (205, 70, 60), _INK, 2.5)
    p.rect(42, 62, 58, 90, (120, 78, 40), _INK, 2); p.rect(24, 56, 36, 68, (150, 210, 245), _INK, 1.5)
    p.rect(64, 56, 76, 68, (150, 210, 245), _INK, 1.5)
def _i_key(p):
    p.circ(30, 32, 20, None, (235, 180, 40), 7)
    p.line([(44, 46), (84, 86)], (235, 180, 40), 8)
    p.line([(68, 70), (60, 78)], (235, 180, 40), 7); p.line([(78, 80), (70, 88)], (235, 180, 40), 7)
def _i_crown(p):
    p.poly([(10, 78), (6, 28), (30, 52), (50, 18), (70, 52), (94, 28), (90, 78)], (255, 200, 50), (200, 130, 10), 2.5)
    p.rect(10, 78, 90, 90, (235, 160, 30), (200, 130, 10), 2)
    for x, c in ((6, (220, 50, 70)), (50, (60, 120, 230)), (94, (220, 50, 70))):
        p.circ(x, 24 if x != 50 else 14, 5, c)
def _i_gem(p):
    p.poly([(22, 12), (78, 12), (96, 38), (50, 92), (4, 38)], (80, 200, 235), _INK, 2.5)
    p.poly([(4, 38), (96, 38), (50, 92)], (50, 160, 210))
    p.line([(30, 38), (40, 12)], (230, 250, 255), 2); p.line([(70, 38), (60, 12)], (230, 250, 255), 2)
    p.line([(30, 38), (50, 92)], (230, 250, 255), 2); p.line([(70, 38), (50, 92)], (230, 250, 255), 2)
def _i_flower(p):
    p.line([(50, 54), (50, 96)], (50, 150, 60), 5); p.ell(50, 74, 76, 88, (70, 170, 80))
    for i in range(6):
        a = math.radians(i * 60)
        cx, cy = 50 + 20 * math.cos(a), 36 + 20 * math.sin(a)
        p.circ(cx, cy, 13, (245, 110, 170), (200, 60, 120), 1.5)
    p.circ(50, 36, 11, (255, 210, 50), (210, 140, 20), 1.5)
def _i_fish(p):
    p.poly([(70, 50), (96, 26), (96, 74)], (240, 130, 40), _INK, 2)
    p.ell(8, 26, 80, 74, (255, 160, 50), _INK, 2.5)
    p.circ(26, 45, 5, (255, 255, 255), _INK, 1.5); p.circ(25, 45, 2, _INK)
    p.arc(40, 30, 62, 70, 100, 260, (200, 100, 20), 2.5)
def _i_anchor(p):
    c = (70, 90, 130)
    p.circ(50, 18, 9, None, c, 4); p.line([(50, 27), (50, 84)], c, 5); p.line([(30, 40), (70, 40)], c, 5)
    p.arc(14, 30, 86, 92, 10, 170, c, 5)
    p.poly([(8, 58), (22, 56), (18, 72)], c); p.poly([(92, 58), (78, 56), (82, 72)], c)
def _i_bell(p):
    p.pie(18, 14, 82, 78, 180, 360, (250, 200, 50), _INK, 2)
    p.poly([(18, 46), (82, 46), (92, 76), (8, 76)], (250, 200, 50), _INK, 2)
    p.rect(8, 74, 92, 82, (230, 160, 30), _INK, 2, r=3); p.circ(50, 90, 8, (200, 130, 20), _INK, 1.5)
    p.circ(50, 12, 5, (200, 130, 20))
def _i_clock(p):
    p.circ(50, 50, 44, (250, 250, 245), _INK, 4)
    for i in range(12):
        a = math.radians(i * 30)
        p.line([(50 + 36 * math.cos(a), 50 + 36 * math.sin(a)), (50 + 41 * math.cos(a), 50 + 41 * math.sin(a))], _INK, 2.5)
    p.line([(50, 50), (50, 24)], _INK, 4); p.line([(50, 50), (70, 60)], (210, 50, 60), 3.5); p.circ(50, 50, 4, _INK)
def _i_cup(p):
    p.arc(60, 32, 92, 70, 270, 90, (120, 78, 40), 6)
    p.poly([(14, 34), (72, 34), (64, 86), (22, 86)], (250, 250, 245), _INK, 2.5)
    p.rect(18, 40, 68, 52, (150, 100, 60))
    for x in (30, 44, 58):
        p.line([(x, 8), (x + 4, 18), (x, 28)], (170, 170, 190), 2.5)
def _i_sword(p):
    p.poly([(78, 6), (92, 8), (94, 22), (34, 68), (28, 62)], (215, 225, 240), _INK, 2)
    p.line([(20, 56), (44, 80)], (230, 170, 40), 7); p.line([(30, 68), (14, 84)], (120, 78, 40), 8)
    p.circ(10, 90, 5, (230, 170, 40))
def _i_shield(p):
    p.poly([(50, 6), (90, 18), (86, 58), (50, 94), (14, 58), (10, 18)], (70, 110, 220), _INK, 3)
    p.poly([(50, 14), (80, 24), (78, 56), (50, 84), (22, 56), (20, 24)], (240, 245, 255))
    p.poly(_star_pts(50, 50, 22, 9), (220, 60, 70))
def _i_flag(p):
    p.line([(20, 8), (20, 94)], (110, 80, 50), 6)
    p.poly([(22, 10), (88, 22), (68, 38), (88, 54), (22, 50)], (220, 55, 70), _INK, 2.5)
def _i_rocket(p):
    p.poly([(50, 4), (68, 34), (68, 70), (32, 70), (32, 34)], (240, 242, 250), _INK, 2.5)
    p.poly([(50, 4), (66, 30), (34, 30)], (220, 55, 70), _INK, 2)
    p.poly([(32, 52), (14, 76), (32, 72)], (220, 55, 70), _INK, 2); p.poly([(68, 52), (86, 76), (68, 72)], (220, 55, 70), _INK, 2)
    p.circ(50, 46, 8, (130, 200, 245), _INK, 2)
    p.poly([(38, 72), (62, 72), (50, 96)], (255, 170, 40), (230, 90, 20), 2)
def _i_car(p):
    p.poly([(26, 40), (38, 18), (68, 18), (80, 40)], (150, 205, 240), _INK, 2.5)
    p.rect(8, 40, 94, 70, (225, 60, 60), _INK, 2.5, r=8)
    p.circ(28, 72, 12, (50, 50, 60), _INK, 1.5); p.circ(28, 72, 5, (190, 190, 200))
    p.circ(72, 72, 12, (50, 50, 60), _INK, 1.5); p.circ(72, 72, 5, (190, 190, 200))
    p.line([(52, 20), (52, 40)], _INK, 2)
def _i_boat(p):
    p.line([(50, 8), (50, 66)], _INK, 3)
    p.poly([(54, 10), (90, 60), (54, 60)], (250, 250, 245), _INK, 2.5); p.poly([(46, 20), (46, 60), (14, 60)], (240, 90, 90), _INK, 2.5)
    p.poly([(8, 66), (92, 66), (78, 86), (22, 86)], (130, 85, 45), _INK, 2.5)
    p.arc(0, 84, 34, 100, 180, 360, (70, 150, 220), 3); p.arc(32, 84, 66, 100, 180, 360, (70, 150, 220), 3); p.arc(64, 84, 98, 100, 180, 360, (70, 150, 220), 3)
def _i_mountain(p):
    p.poly([(2, 88), (36, 22), (70, 88)], (120, 130, 150), _INK, 2.5); p.poly([(40, 88), (68, 36), (98, 88)], (95, 105, 130), _INK, 2.5)
    p.poly([(36, 22), (26, 42), (36, 38), (44, 44)], (250, 250, 255)); p.poly([(68, 36), (60, 50), (68, 46), (76, 52)], (250, 250, 255))
    p.circ(82, 18, 8, (255, 210, 60))
def _i_eye(p):
    p.poly([(4, 50), (28, 26), (72, 26), (96, 50), (72, 74), (28, 74)], (250, 250, 250), _INK, 3)
    p.circ(50, 50, 20, (70, 130, 200), _INK, 2); p.circ(50, 50, 9, _INK); p.circ(44, 44, 4, (255, 255, 255))
def _i_apple(p):
    p.circ(36, 56, 28, (225, 50, 60)); p.circ(64, 56, 28, (225, 50, 60)); p.rect(30, 44, 70, 84, (225, 50, 60), r=14)
    p.line([(50, 34), (54, 12)], (110, 70, 40), 5); p.poly([(54, 20), (80, 8), (74, 30)], (70, 170, 70), (30, 110, 40), 1.5)
    p.circ(30, 52, 6, (255, 140, 150))
def _i_drop(p):
    p.poly([(50, 4), (80, 56), (20, 56)], (60, 150, 230)); p.circ(50, 62, 30, (60, 150, 230), _INK, 2.5)
    p.poly([(50, 4), (80, 56), (20, 56)], (60, 150, 230)); p.circ(50, 62, 29, (60, 150, 230)); p.circ(38, 58, 6, (200, 235, 255))
def _i_flame(p):
    p.poly([(50, 2), (82, 44), (90, 68), (72, 92), (28, 92), (10, 68), (24, 40), (40, 52)], (245, 110, 30), (200, 60, 10), 2.5)
    p.poly([(50, 36), (70, 62), (64, 88), (36, 88), (30, 62)], (255, 200, 50)); p.circ(50, 80, 10, (255, 245, 190))
def _i_snow(p):
    c = (110, 190, 240)
    for i in range(3):
        a = math.radians(i * 60 + 90)
        p.line([(50 + 44 * math.cos(a), 50 + 44 * math.sin(a)), (50 - 44 * math.cos(a), 50 - 44 * math.sin(a))], c, 5)
    for i in range(6):
        a = math.radians(i * 60 + 90)
        bx, by = 50 + 30 * math.cos(a), 50 + 30 * math.sin(a)
        for d in (-35, 35):
            b = a + math.radians(180 + d)
            p.line([(bx, by), (bx + 12 * math.cos(b), by + 12 * math.sin(b))], c, 3.5)
def _i_gear(p):
    pts = []
    for i in range(16):
        a0 = math.radians(i * 22.5)
        r = 46 if i % 2 == 0 else 34
        pts += [(50 + r * math.cos(a0 - 0.1), 50 + r * math.sin(a0 - 0.1)), (50 + r * math.cos(a0 + 0.1), 50 + r * math.sin(a0 + 0.1))]
    p.poly(pts, (150, 160, 180), _INK, 2.5); p.circ(50, 50, 30, (150, 160, 180)); p.circ(50, 50, 13, (0, 0, 0, 0)); p.circ(50, 50, 13, None, _INK, 2.5)
def _i_note(p):
    p.line([(66, 14), (66, 72)], _INK, 5); p.poly([(66, 12), (92, 24), (92, 42), (66, 30)], _INK)
    p.ell(30, 60, 70, 88, (130, 70, 200), _INK, 2.5)
def _i_book(p):
    p.poly([(6, 22), (48, 30), (48, 88), (6, 80)], (70, 120, 220), _INK, 2.5); p.poly([(94, 22), (52, 30), (52, 88), (94, 80)], (60, 105, 200), _INK, 2.5)
    p.poly([(12, 28), (44, 34), (44, 82), (12, 76)], (250, 246, 230)); p.poly([(88, 28), (56, 34), (56, 82), (88, 76)], (250, 246, 230))
    for y in (44, 54, 64):
        p.line([(17, y - 4), (39, y)], (170, 170, 190), 2); p.line([(83, y - 4), (61, y)], (170, 170, 190), 2)
def _i_lock(p):
    p.arc(26, 6, 74, 70, 180, 360, (130, 135, 150), 8); p.line([(28, 38), (28, 50)], (130, 135, 150), 8); p.line([(72, 38), (72, 50)], (130, 135, 150), 8)
    p.rect(14, 46, 86, 92, (245, 190, 50), _INK, 2.5, r=8); p.circ(50, 64, 7, _INK); p.rect(46, 66, 54, 80, _INK)
def _i_umbrella(p):
    cols = [(220, 55, 70), (250, 250, 245)] * 2
    for i, c in enumerate(cols):
        p.pie(6, 14, 94, 100, 180 + i * 45, 225 + i * 45, c, _INK, 1.5)
    p.line([(50, 56), (50, 84)], _INK, 4); p.arc(36, 74, 60, 98, 0, 180, _INK, 4)
def _i_balloon(p):
    p.line([(50, 78), (46, 90), (54, 96)], (110, 110, 130), 2)
    p.ell(18, 6, 82, 78, (230, 70, 110), _INK, 2.5); p.poly([(50, 76), (42, 88), (58, 88)], (200, 40, 80)); p.circ(36, 28, 7, (255, 160, 190))
def _i_bulb(p):
    p.circ(50, 38, 30, (255, 225, 90), (220, 160, 20), 2.5); p.rect(36, 62, 64, 84, (170, 175, 190), _INK, 2, r=4)
    p.line([(40, 92), (60, 92)], _INK, 4); p.line([(44, 50), (50, 40), (56, 50)], (230, 150, 20), 2.5); p.circ(38, 28, 6, (255, 250, 210))
def _i_leaf(p):
    p.poly([(10, 90), (14, 40), (50, 8), (90, 10), (88, 50), (56, 84)], (80, 185, 80), (30, 120, 50), 2.5)
    p.line([(10, 90), (62, 38)], (30, 120, 50), 3.5)
def _i_planet(p):
    p.arc(4, 32, 96, 68, 180, 360, (200, 150, 70), 5)
    p.circ(50, 50, 28, (235, 150, 70), _INK, 2.5); p.arc(22, 40, 78, 60, 0, 180, (200, 110, 50), 3)
    p.arc(4, 32, 96, 68, 0, 180, (230, 190, 90), 5)
def _i_butterfly(p):
    p.ell(8, 10, 50, 52, (245, 130, 60), _INK, 2); p.ell(50, 10, 92, 52, (245, 130, 60), _INK, 2)
    p.ell(14, 48, 50, 88, (240, 90, 140), _INK, 2); p.ell(50, 48, 86, 88, (240, 90, 140), _INK, 2)
    p.ell(44, 20, 56, 84, _INK); p.line([(48, 22), (38, 4)], _INK, 2); p.line([(52, 22), (62, 4)], _INK, 2)
    p.circ(28, 30, 7, (255, 230, 200)); p.circ(72, 30, 7, (255, 230, 200))
def _i_pencil(p):
    p.poly([(70, 6), (94, 30), (36, 88), (12, 88), (12, 64)], (250, 205, 50), _INK, 2.5)
    p.poly([(12, 64), (36, 88), (6, 94)], (240, 215, 180), _INK, 2); p.poly([(8, 90), (14, 84), (20, 92)], _INK)
    p.poly([(70, 6), (94, 30), (84, 40), (60, 16)], (235, 110, 140), _INK, 2)

CN_ICONS = {
    "نجمة": _i_star, "قلب": _i_heart, "قمر": _i_moon, "شمس": _i_sun, "غيمة": _i_cloud, "برق": _i_bolt,
    "شجرة": _i_tree, "بيت": _i_house, "مفتاح": _i_key, "تاج": _i_crown, "جوهرة": _i_gem, "وردة": _i_flower,
    "سمكة": _i_fish, "مرساة": _i_anchor, "جرس": _i_bell, "ساعة": _i_clock, "كوب": _i_cup, "سيف": _i_sword,
    "درع": _i_shield, "علم": _i_flag, "صاروخ": _i_rocket, "سيارة": _i_car, "قارب": _i_boat, "جبل": _i_mountain,
    "عين": _i_eye, "تفاحة": _i_apple, "قطرة": _i_drop, "نار": _i_flame, "ثلجة": _i_snow, "ترس": _i_gear,
    "نوتة": _i_note, "كتاب": _i_book, "قفل": _i_lock, "مظلة": _i_umbrella, "بالون": _i_balloon, "مصباح": _i_bulb,
    "ورقة": _i_leaf, "كوكب": _i_planet, "فراشة": _i_butterfly, "قلم": _i_pencil,
}
_icon_cache = {}

def cn_icon(name, size=120):
    """صورة RGBA شفافة للأيقونة بالحجم المطلوب."""
    key = (name, size)
    if key in _icon_cache:
        return _icon_cache[key]
    big = 400
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    CN_ICONS[name](_Pen(ImageDraw.Draw(img), big // 100))
    img = img.resize((size, size), Image.LANCZOS)
    _icon_cache[key] = img
    return img


# ═════════════════════════ الألعاب الجديدة (ألغاز • برا السالفة • مافيا • كود نيمز بالصور) ═════════════════════════
# ألعاب جماعية جديدة كلياً (غير موجودة بقسم الألعاب القديم). كلها بأزرار وقوائم، ورتبها/جوائزها
# تُحسب بنفس نظام العملات والـ XP. أدوار الألعاب السرية تظهر برسائل مخفية (ephemeral) فلا تحتاج DM.
RAW_BLOCK = set()   # رومات توقّف فيها الأوامر بدون بادئة مؤقتاً (حتى لا تتحول إجابة لعبة إلى أمر)

def norm_ar(text):
    t = re.sub(r"[\u064B-\u0652\u0640]", "", (text or "").lower())
    for a, b in (("أ", "ا"), ("إ", "ا"), ("آ", "ا"), ("ى", "ي"), ("ة", "ه"), ("ؤ", "و"), ("ئ", "ي"), ("گ", "ك"), ("چ", "ج"), ("پ", "ب")):
        t = t.replace(a, b)
    t = re.sub(r"[^\w\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()

def strip_al(word):
    return word[2:] if word.startswith("ال") and len(word) > 3 else word

def mention_list(members):
    return " ".join(m.mention for m in members)

def plurality(votes, rng=random):
    """votes: {voter: target}. يرجع (الهدف الأكثر أصواتاً, عدد أصواته, هل تعادل). التعادل → الهدف None."""
    counts = {}
    for t in votes.values():
        if t:
            counts[t] = counts.get(t, 0) + 1
    if not counts:
        return None, 0, False
    top = max(counts.values())
    leaders = [t for t, c in counts.items() if c == top]
    if len(leaders) > 1:
        return None, top, True
    return leaders[0], top, False

async def game_guard(ctx):
    """يحجز الروم للعبة؛ يرجع False إذا في لعبة شغالة."""
    if ctx.channel.id in ACTIVE:
        await ctx.reply("⏳ في لعبة شغالة بهالروم، انتظروا تخلص.")
        return False
    ACTIVE.add(ctx.channel.id)
    return True

class OneShotView(discord.ui.View):
    """قائمة اختيار مخفية لشخص واحد (للأدوار السرية والتصويت)."""
    def __init__(self, select, timeout=60):
        super().__init__(timeout=timeout)
        self.add_item(select)

class TargetSelect(discord.ui.Select):
    def __init__(self, options, on_pick, placeholder="اختر لاعباً"):
        super().__init__(placeholder=placeholder, min_values=1, max_values=1, options=options[:25])
        self._on_pick = on_pick

    async def callback(self, interaction):
        await self._on_pick(interaction, int(self.values[0]))

def player_options(members, skip_label=None):
    opts = [discord.SelectOption(label=m.display_name[:100], value=str(m.id)) for m in members]
    if skip_label:
        opts.append(discord.SelectOption(label=skip_label, value="0", emoji="⏭️"))
    return opts

# ───────────────────────── 1) ألغاز ─────────────────────────
RIDDLES = [
    ("شيء يطير بلا جناحين ويبكي بلا عينين؟", ["السحاب", "الغيم", "الغيمه", "سحاب", "غيمه"], "يسبح في السماء ويجلب المطر"),
    ("له أسنان ولا يعض؟", ["المشط", "مشط"], "تستعمله لشعرك"),
    ("شيء كلما أخذت منه كبر؟", ["الحفره", "حفره", "الحفرة"], "تُحفر في الأرض"),
    ("شيء له عين واحدة ولا يرى؟", ["الابره", "ابره", "الإبرة", "الابرة"], "تخيط بها الملابس"),
    ("شيء كلما زاد نقص؟", ["العمر", "عمر"], "كل سنة يزيد وهو بالحقيقة ينقص"),
    ("له أربع أرجل وظهر ولكنه لا يمشي؟", ["الكرسي", "كرسي", "الطاوله", "الطاولة"], "تجلس عليه"),
    ("شيء تذبحه وتبكي عليه؟", ["البصل", "بصل"], "يدخل بكل طبخة"),
    ("شيء إذا لمسته صاح؟", ["الجرس", "جرس"], "يرن عند الباب"),
    ("شيء ملكك ولكن غيرك يستعمله أكثر منك؟", ["اسمك", "الاسم", "اسم"], "الناس تناديك به"),
    ("شيء كلما جف ابتل؟", ["المنشفه", "منشفه", "المنشفة", "الفوطه", "فوطه"], "تمسح بها بعد الاستحمام"),
    ("له رقبة وليس له رأس؟", ["الزجاجه", "زجاجه", "القنينه", "الزجاجة", "القنينة"], "تحتوي سائلاً"),
    ("شيء لا يمكنك استعماله إلا إذا كسرته؟", ["البيضه", "بيضه", "البيضة"], "تأكلها بالفطور"),
    ("شيء يسمع بلا أذن ويتكلم بلا لسان؟", ["الهاتف", "التلفون", "الموبايل", "الجوال", "الهاتف الذكي", "تلفون", "موبايل"], "تحمله بجيبك"),
    ("شيء يحيط بك ولا تراه؟", ["الهواء", "هواء"], "تتنفسه"),
    ("شيء تراه في الليل ولا تراه في النهار؟", ["النجوم", "نجوم", "النجمه"], "تتلألأ فوق"),
    ("ما هو الشيء الذي يوجد في وسط باريس؟", ["حرف الراء", "الراء", "راء"], "فكّر بحروف الكلمة"),
    ("شيء يكتب اسمه خطأ دائماً؟", ["خطا", "خطأ", "كلمه خطا", "كلمة خطأ"], "اكتبه غلط وبتفوز 😄"),
    ("شيء له مفاتيح كثيرة ولا يفتح باباً؟", ["البيانو", "بيانو", "الكيبورد", "لوحه المفاتيح", "الكمبيوتر", "الحاسوب", "لوحة المفاتيح"], "تضغط عليها لتعزف أو تكتب"),
    ("شيء فيه مدن بلا بيوت وجبال بلا حجارة وأنهار بلا ماء؟", ["الخريطه", "خريطه", "الخريطة", "خريطة"], "تفتحها للسفر"),
    ("إذا نطقت باسمه اختفى؟", ["الصمت", "صمت", "السكوت"], "عكس الكلام"),
    ("شيء يولد كبيراً ويموت صغيراً؟", ["الشمعه", "شمعه", "الشمعة", "شمعة"], "تضيء ثم تذوب"),
    ("حيوان ينام وعينه مفتوحة؟", ["السمكه", "سمكه", "السمك", "السمكة"], "يعيش بالماء"),
    ("أنا في كل بيت، أستقبل الضيوف وأنا ثابت؟", ["الباب", "باب"], "تطرقه قبل الدخول"),
    ("أخضر من الخارج أحمر من الداخل وبذوره سوداء؟", ["البطيخ", "الرقي", "رقي", "الرگي", "رگي", "بطيخ", "الجح", "جح"], "فاكهة الصيف"),
    ("ما هو الحرف الذي يوجد في آخر الليل؟", ["اللام", "حرف اللام", "لام"], "انظر لآخر حرف في الكلمة"),
    ("شيء يشرب ولا يرتوي؟", ["الاسفنجه", "الاسفنج", "اسفنجه", "الإسفنجة", "الاسفنجة", "الإسفنج", "الاسفنجة"], "يمتص الماء بالجلي"),
    ("شيء له وجهان ولا يتكلم؟", ["المرايه", "المراه", "مرايه", "المرآة", "مرآة", "المرايا"], "تنظر فيها لنفسك"),
    ("شيء يملأ الغرفة ولا يشغل مكاناً؟", ["الضوء", "النور", "الضو", "ضوء", "نور"], "تطفيه بالزر"),
    ("شيء يجري ولا يمشي؟", ["الماء", "النهر", "ماء", "نهر", "الشلال"], "يصب في البحر"),
    ("شيء مثلث الشكل، عليه جبن، وتحبه الأولاد؟", ["البيتزا", "بيتزا"], "من إيطاليا"),
    ("شيء يمشي بالليل والنهار ولا يتعب؟", ["الساعه", "الساعة", "عقارب الساعة", "ساعه"], "تقول لك الوقت"),
]

class RiddleView(discord.ui.View):
    def __init__(self, hint, host):
        super().__init__(timeout=None)
        self.hint, self.host = hint, host
        self.hint_used = False
        self.skipped = False

    @discord.ui.button(label="تلميح", emoji="💡", style=discord.ButtonStyle.secondary)
    async def hint_btn(self, interaction, button):
        if self.hint_used:
            return await interaction.response.send_message("💡 التلميح انكشف مسبقاً.", ephemeral=True)
        self.hint_used = True
        button.disabled = True
        emb = interaction.message.embeds[0]
        emb.add_field(name="💡 تلميح", value=self.hint, inline=False)
        await interaction.response.edit_message(embed=emb, view=self)

    @discord.ui.button(label="تخطي", emoji="⏭️", style=discord.ButtonStyle.danger)
    async def skip_btn(self, interaction, button):
        if interaction.user.id != self.host.id and not is_admin(interaction.user):
            return await interaction.response.send_message("❌ التخطي لمن بدأ اللعبة أو الإدارة.", ephemeral=True)
        self.skipped = True
        await interaction.response.defer()

def riddle_matches(content, answers):
    msg = norm_ar(content)
    if not msg or len(msg) > 60:
        return False
    accepted = set()
    for a in answers:
        n = norm_ar(a)
        accepted.add(n)
        accepted.add(" ".join(strip_al(w) for w in n.split()))
    words = msg.split()
    stripped = " ".join(strip_al(w) for w in words)
    if msg in accepted or stripped in accepted:
        return True
    if len(words) <= 3:
        return any(strip_al(w) in accepted or w in accepted for w in words)
    return False

@bot.command(name="ألغاز", aliases=["الغاز", "لغز", "riddles", "riddle"])
@commands.guild_only()
async def riddles_cmd(ctx, rounds: int = 5):
    if not await game_guard(ctx):
        return
    RAW_BLOCK.add(ctx.channel.id)
    scores = {}
    try:
        rounds = max(1, min(rounds, 10))
        picks = random.sample(RIDDLES, min(rounds, len(RIDDLES)))
        await ctx.send(embed=E("🧩 جولة ألغاز!", f"**{len(picks)}** ألغاز • أول واحد يكتب الجواب الصحيح بالشات يربح 💰\n"
                               "💡 التلميح يكشف مساعدة (والجائزة تنخفض للنصف).", PURPLE))
        await asyncio.sleep(2)
        for n, (question, answers, hint) in enumerate(picks, 1):
            view = RiddleView(hint, ctx.author)
            e = E(f"🧩 اللغز {n}/{len(picks)}", f"**{question}**\n\n⏱️ عندكم 40 ثانية — اكتبوا الجواب بالشات!", PURPLE)
            msg = await ctx.send(embed=e, view=view)
            deadline = time.monotonic() + 40
            winner = None

            def check(m):
                return (m.channel.id == ctx.channel.id and not m.author.bot
                        and riddle_matches(m.content, answers))
            while winner is None and not view.skipped:
                left = deadline - time.monotonic()
                if left <= 0:
                    break
                try:
                    m = await bot.wait_for("message", check=check, timeout=min(left, 1.5))
                    winner = m.author
                except asyncio.TimeoutError:
                    continue
            view.stop()
            for c in view.children:
                c.disabled = True
            try:
                await msg.edit(view=view)
            except discord.HTTPException:
                pass
            if winner:
                coins = 30 if view.hint_used else 60
                scores[winner] = scores.get(winner, 0) + 1
                await reward(winner, coins, 8, ctx.channel)
                await ctx.send(embed=E("✅ إجابة صحيحة!", f"{winner.mention} جاوب **{answers[0]}** وربح `{coins}` 💰", 0x2ECC71))
            else:
                await ctx.send(embed=E("⌛ ما أحد جاوب" if not view.skipped else "⏭️ تم التخطي", f"الجواب: **{answers[0]}**", 0xE67E22))
            await asyncio.sleep(2)
        if scores:
            board = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
            lines = [f"{['🥇', '🥈', '🥉'][i] if i < 3 else '🔹'} {m.mention} — `{pts}` لغز" for i, (m, pts) in enumerate(board)]
            champ = board[0][0]
            await reward(champ, 100, 15, ctx.channel)
            player_stats(list(scores), [champ])
            await ctx.send(embed=E("🏆 نتيجة الألغاز", "\n".join(lines) + f"\n\n👑 البطل {champ.mention} ياخذ **100** 💰 إضافية!", GOLD))
        else:
            await ctx.send(embed=E("🧩 انتهت الألغاز", "ما أحد جاوب، المرة الجاية أصعب 😄", PURPLE))
    finally:
        RAW_BLOCK.discard(ctx.channel.id)
        ACTIVE.discard(ctx.channel.id)

# ───────────────────────── 2) برا السالفة ─────────────────────────
OUTSIDER_SETS = {
    "📍 أماكن": ["مطار", "مستشفى", "مدرسة", "سوق", "حديقة", "مطعم", "سينما", "شاطئ", "جامعة", "ملعب", "فندق", "مكتبة", "بنك", "محطة قطار", "مول"],
    "🍽️ أكلات": ["برياني", "دولمة", "كباب", "مسگوف", "بيتزا", "برگر", "شاورما", "فلافل", "كبة", "معكرونة", "سمبوسة", "باجة", "تشريب", "شوربة"],
    "🐾 حيوانات": ["أسد", "فيل", "زرافة", "جمل", "قرد", "نمر", "دلفين", "نسر", "ثعلب", "حصان", "بطريق", "تمساح", "ذئب", "أرنب"],
    "💼 مهن": ["طبيب", "مهندس", "معلم", "طيار", "شرطي", "نجار", "طباخ", "حلاق", "محامي", "سائق", "ممرض", "رسام", "صحفي", "مزارع"],
    "📦 أشياء": ["هاتف", "مفتاح", "كرسي", "مرآة", "ساعة", "حقيبة", "نظارة", "مظلة", "كاميرا", "دراجة", "مصباح", "سرير", "تلفزيون"],
    "⚽ رياضة وألعاب": ["كرة قدم", "سباحة", "شطرنج", "ملاكمة", "تنس", "دومينو", "بلايستيشن", "جري", "كرة سلة", "طاولة", "غوص"],
    "🌍 مدن": ["بغداد", "البصرة", "أربيل", "دبي", "القاهرة", "باريس", "إسطنبول", "لندن", "طوكيو", "نيويورك", "بيروت", "الرياض"],
    "🎉 مناسبات": ["عرس", "تخرج", "عيد ميلاد", "رحلة", "حفلة", "مباراة", "مهرجان", "سفرة", "مخيم"],
}

def outsider_pick(rng=random):
    cat = rng.choice(list(OUTSIDER_SETS))
    return cat, rng.choice(OUTSIDER_SETS[cat])

class OutsiderRevealView(discord.ui.View):
    def __init__(self, players, outsider_id, word, category):
        super().__init__(timeout=None)
        self.ids = {m.id for m in players}
        self.outsider_id, self.word, self.category = outsider_id, word, category
        self.seen = set()
        self.all_seen = asyncio.Event()

    @discord.ui.button(label="اعرف دورك", emoji="🎭", style=discord.ButtonStyle.primary)
    async def reveal(self, interaction, button):
        uid = interaction.user.id
        if uid not in self.ids:
            return await interaction.response.send_message("❌ أنت مو من لاعبي هذي الجولة.", ephemeral=True)
        self.seen.add(uid)
        if uid == self.outsider_id:
            txt = (f"🕵️ **أنت برا السالفة!**\nالفئة: **{self.category}**\n"
                   "اسمع كلامهم، حاول تفهم الكلمة، وتصرف كأنك تعرفها!")
        else:
            txt = (f"✅ الكلمة السرية: **{self.word}**\nالفئة: {self.category}\n"
                   "لمّح بدون ما تذكرها حتى ما يعرفها اللي برا السالفة!")
        await interaction.response.send_message(txt, ephemeral=True)
        if self.seen >= self.ids:
            self.all_seen.set()

class SkipToVoteView(discord.ui.View):
    """زر 'انتقلوا للتصويت': إذا ضغطه أكثر من نصف اللاعبين ينتهي النقاش."""
    def __init__(self, allowed_ids, timeout):
        super().__init__(timeout=timeout)
        self.allowed, self.ready = set(allowed_ids), set()

    @discord.ui.button(label="انتقلوا للتصويت", emoji="🗳️", style=discord.ButtonStyle.success)
    async def go(self, interaction, button):
        if interaction.user.id not in self.allowed:
            return await interaction.response.send_message("❌ مو من اللاعبين.", ephemeral=True)
        self.ready.add(interaction.user.id)
        need = len(self.allowed) // 2 + 1
        await interaction.response.send_message(f"🗳️ تم (`{len(self.ready)}/{need}` للانتقال).", ephemeral=True)
        if len(self.ready) >= need:
            self.stop()

class VoteView(discord.ui.View):
    """تصويت عام بقائمة: كل لاعب يصوت (ويقدر يغيّر) والتصويت يخفى عن البقية."""
    def __init__(self, voters, candidates, timeout=50, skip_label=None, placeholder="🗳️ صوّت"):
        super().__init__(timeout=timeout)
        self.voter_ids = {m.id for m in voters}
        self.votes = {}
        self.add_item(TargetSelect(player_options(candidates, skip_label), self.cast, placeholder))

    async def cast(self, interaction, target):
        if interaction.user.id not in self.voter_ids:
            return await interaction.response.send_message("❌ ما تگدر تصوّت.", ephemeral=True)
        if target == interaction.user.id:
            return await interaction.response.send_message("🤨 ما تگدر تصوّت على نفسك.", ephemeral=True)
        self.votes[interaction.user.id] = target
        await interaction.response.send_message(f"✅ تم تسجيل صوتك ({len(self.votes)}/{len(self.voter_ids)} صوّتوا).", ephemeral=True)
        if len(self.votes) >= len(self.voter_ids):
            self.stop()

async def finish_game_rewards(ctx, players, winners, win_coins=150, win_xp=20, lose_coins=30):
    wset = {m.id for m in winners}
    player_stats(players, winners)
    for m in players:
        if m.id in wset:
            await reward(m, win_coins, win_xp, ctx.channel)
        else:
            await reward(m, lose_coins, 0, ctx.channel)

@bot.command(name="برا_السالفة", aliases=["برا", "برا_السالفه", "outsider", "spy"])
@commands.guild_only()
async def outsider_cmd(ctx):
    if not await game_guard(ctx):
        return
    try:
        players = await run_lobby(ctx, "🕵️ برا السالفة", 3, 10)
        if not players:
            return
        category, word = outsider_pick()
        out = random.choice(players)
        rv = OutsiderRevealView(players, out.id, word, category)
        e = E("🕵️ برا السالفة", f"الجميع يعرف **الكلمة السرية** إلا واحد منكم 😈\nالفئة: **{category}**\n\n"
              f"اضغط **اعرف دورك** (بتوصلك رسالة مخفية)\n👥 {mention_list(players)}", PURPLE)
        await ctx.send(embed=e, view=rv)
        try:
            await asyncio.wait_for(rv.all_seen.wait(), timeout=45)
        except asyncio.TimeoutError:
            pass
        rv.stop()
        order = random.sample(players, len(players))
        skip = SkipToVoteView([m.id for m in players], timeout=180)
        await ctx.send(embed=E("💬 بدأ النقاش (3 دقائق)",
                               "كل واحد يسأل اللي بعده سؤال عن الكلمة **بدون ما يذكرها**، ويجاوب بتلميح ذكي.\n"
                               "برا السالفة يحاول يجاري، والباقي يكشفونه!\n\n"
                               "🔄 دور الأسئلة: " + " ➜ ".join(m.display_name for m in order), PURPLE), view=skip)
        await skip.wait()
        vote = VoteView(players, players, timeout=50, placeholder="🕵️ من تشك إنه برا السالفة؟")
        await ctx.send(embed=E("🗳️ وقت التصويت!", f"صوّتوا على من تشكون فيه (50 ثانية)\n{mention_list(players)}", 0xE67E22), view=vote)
        await vote.wait()
        target, count, tie = plurality(vote.votes)
        counts = {}
        for t in vote.votes.values():
            counts[t] = counts.get(t, 0) + 1
        tally = "\n".join(f"• {next(m for m in players if m.id == t).display_name}: `{c}`" for t, c in
                          sorted(counts.items(), key=lambda kv: kv[1], reverse=True)) or "ما أحد صوّت"
        if target is not None and target == out.id:
            await ctx.send(embed=E("🎯 انكشف!", f"{tally}\n\nاللاعبون كشفوا **{out.display_name}**!\n"
                                   f"{out.mention} عندك **20 ثانية** تكتب الكلمة السرية وتنقذ نفسك:", 0xE67E22))
            RAW_BLOCK.add(ctx.channel.id)
            guessed = False
            try:
                m = await bot.wait_for("message", timeout=20,
                                       check=lambda x: x.channel.id == ctx.channel.id and x.author.id == out.id)
                guessed = norm_ar(m.content) == norm_ar(word)
            except asyncio.TimeoutError:
                pass
            finally:
                RAW_BLOCK.discard(ctx.channel.id)
            if guessed:
                winners, why = [out], f"{out.mention} عرف الكلمة **{word}** وقلب الطاولة! 😎"
            else:
                winners, why = [m for m in players if m.id != out.id], f"الكلمة كانت **{word}** — اللاعبون فازوا!"
        else:
            reason = "تعادلت الأصوات" if tie else ("ما أحد صوّت" if not vote.votes else "اتهموا شخصاً بريئاً")
            winners = [out]
            why = f"{reason}! برا السالفة هو {out.mention} والكلمة **{word}** 😈"
            await ctx.send(embed=E("🕵️ النتيجة", f"{tally}\n\n{why}", 0xE74C3C))
            why = None
        if why:
            await ctx.send(embed=E("🏁 انتهت الجولة", why, GOLD))
        await finish_game_rewards(ctx, players, winners)
    finally:
        RAW_BLOCK.discard(ctx.channel.id)
        ACTIVE.discard(ctx.channel.id)


# ───────────────────────── 3) مافيا ─────────────────────────
MAFIA_ROLES = {
    "mafia": ("🔪", "مافيا"), "doctor": ("🩺", "الدكتور"),
    "detective": ("🕵️", "المحقق"), "citizen": ("🧑", "مواطن"),
}

def mafia_assign(player_ids, rng=random):
    """يوزّع الأدوار: مافيا (واحد لكل 4 لاعبين على الأقل 1) + دكتور + محقق + مواطنون. الحد الأدنى 5 لاعبين."""
    ids = list(player_ids)
    if len(ids) < 5:
        raise ValueError("mafia needs at least 5 players")
    rng.shuffle(ids)
    k = max(1, len(ids) // 4)
    roles = {i: "mafia" for i in ids[:k]}
    roles[ids[k]] = "doctor"
    roles[ids[k + 1]] = "detective"
    for i in ids[k + 2:]:
        roles[i] = "citizen"
    return roles

def mafia_winner(roles, alive):
    m = sum(1 for i in alive if roles[i] == "mafia")
    o = len(alive) - m
    if m == 0:
        return "town"
    if m >= o:
        return "mafia"
    return None

def mafia_night(roles, alive, actions, rng=random):
    """actions: {uid: target}. يرجع (الضحية أو None, هل أنقذها الدكتور)."""
    votes = {u: t for u, t in actions.items() if u in alive and roles.get(u) == "mafia" and t in alive}
    counts = {}
    for t in votes.values():
        counts[t] = counts.get(t, 0) + 1
    if not counts:
        return None, False
    top = max(counts.values())
    victim = rng.choice([t for t, c in counts.items() if c == top])
    saves = [t for u, t in actions.items() if u in alive and roles.get(u) == "doctor"]
    return victim, victim in saves

class MafiaGame:
    def __init__(self, players):
        self.players = {m.id: m for m in players}
        self.roles = mafia_assign(list(self.players))
        self.alive = set(self.players)
        self.actions = {}
        self.investigated = set()

    def name(self, uid):
        return self.players[uid].display_name

    def alive_members(self):
        return [self.players[i] for i in self.players if i in self.alive]

class MafiaRoleView(discord.ui.View):
    def __init__(self, game):
        super().__init__(timeout=None)
        self.game, self.seen = game, set()
        self.all_seen = asyncio.Event()

    @discord.ui.button(label="اعرف دورك", emoji="🎭", style=discord.ButtonStyle.primary)
    async def reveal(self, interaction, button):
        g, uid = self.game, interaction.user.id
        if uid not in g.players:
            return await interaction.response.send_message("❌ أنت مو من لاعبي هذي الجولة.", ephemeral=True)
        role = g.roles[uid]
        icon, name = MAFIA_ROLES[role]
        tips = {
            "mafia": "كل ليلة اختر ضحية مع زملائك، وخلال النهار ادّعِ البراءة!",
            "doctor": "كل ليلة اختر لاعباً تحميه من القتل (حتى نفسك).",
            "detective": "كل ليلة تحقق من لاعب واحد وتعرف إذا كان مافيا.",
            "citizen": "اكتشف المافيا بالنقاش وصوّت لإخراجهم.",
        }[role]
        extra = ""
        if role == "mafia":
            mates = [g.name(i) for i, r in g.roles.items() if r == "mafia" and i != uid]
            extra = f"\n🔪 زملاؤك: {', '.join(mates)}" if mates else "\n🔪 أنت المافيا الوحيد!"
        self.seen.add(uid)
        await interaction.response.send_message(f"{icon} دورك: **{name}**\n{tips}{extra}", ephemeral=True)
        if self.seen >= set(g.players):
            self.all_seen.set()

class MafiaNightView(discord.ui.View):
    def __init__(self, game, timeout=50):
        super().__init__(timeout=timeout)
        self.game = game

    @discord.ui.button(label="نفّذ دورك", emoji="🌙", style=discord.ButtonStyle.primary)
    async def act(self, interaction, button):
        g, uid = self.game, interaction.user.id
        if uid not in g.alive:
            return await interaction.response.send_message("💀 أنت خارج اللعبة.", ephemeral=True)
        role = g.roles[uid]
        hints = {
            "mafia": "🔪 اختر **ضحية** الليلة (وتفاهموا مع زملائك):",
            "doctor": "🩺 اختر من **تحميه** الليلة:",
            "detective": "🕵️ اختر من **تتحقق** منه (مرة وحدة بالليلة):",
            "citizen": "😴 ما عندك دور بالليل — اختر أي أحد كتمويه حتى ما ينكشف دورك:",
        }
        pool = [m for m in g.alive_members()
                if not (role == "mafia" and g.roles[m.id] == "mafia") and not (role == "detective" and m.id == uid)]
        sel = TargetSelect(player_options(pool), self.pick, "🌙 اختر لاعباً")
        await interaction.response.send_message(hints[role], view=OneShotView(sel), ephemeral=True)

    async def pick(self, interaction, target):
        g, uid = self.game, interaction.user.id
        if uid not in g.alive or target not in g.alive:
            return await interaction.response.edit_message(content="⚠️ الاختيار غير صالح.", view=None)
        role = g.roles[uid]
        if role == "detective":
            if uid in g.investigated:
                return await interaction.response.edit_message(content="🔎 استخدمت تحقيقك لهالليلة.", view=None)
            g.investigated.add(uid)
            verdict = "🔪 **مافيا!**" if g.roles[target] == "mafia" else "✅ **بريء**"
            msg = f"🔎 نتيجة التحقيق عن **{g.name(target)}**: {verdict}"
        else:
            msg = {"mafia": "🔪 تم تسجيل الضحية.", "doctor": "🩺 تم تسجيل الحماية.",
                   "citizen": "😴 تم."}[role]
        g.actions[uid] = target
        await interaction.response.edit_message(content=msg, view=None)
        if set(g.actions) >= g.alive:
            self.stop()

def mafia_status(g):
    alive = "\n".join(f"• {m.mention}" for m in g.alive_members())
    dead = [g.players[i] for i in g.players if i not in g.alive]
    out = f"👥 **الأحياء ({len(g.alive)}):**\n{alive}"
    if dead:
        out += "\n\n💀 **الخارجون:** " + "، ".join(f"{m.display_name} ({MAFIA_ROLES[g.roles[m.id]][1]})" for m in dead)
    return out

@bot.command(name="مافيا", aliases=["mafia"])
@commands.guild_only()
async def mafia_cmd(ctx):
    if not await game_guard(ctx):
        return
    try:
        players = await run_lobby(ctx, "🔪 مافيا", 5, 12)
        if not players:
            return
        g = MafiaGame(players)
        k = sum(1 for r in g.roles.values() if r == "mafia")
        rv = MafiaRoleView(g)
        await ctx.send(embed=E("🔪 لعبة المافيا بدأت!",
                               f"👥 {len(players)} لاعبين: `{k}` مافيا • 🩺 دكتور • 🕵️ محقق • والباقي مواطنين.\n"
                               "اضغط **اعرف دورك** لتشوف دورك (رسالة مخفية).\n\n" + mention_list(players), 0x992D22), view=rv)
        try:
            await asyncio.wait_for(rv.all_seen.wait(), timeout=50)
        except asyncio.TimeoutError:
            pass
        rv.stop()
        winner = None
        for day in range(1, 13):
            # ── الليل ──
            g.actions.clear()
            g.investigated.clear()
            nv = MafiaNightView(g, timeout=50)
            await ctx.send(embed=E(f"🌙 الليلة {day}", "المدينة نامت... اضغط **نفّذ دورك** (الجميع يضغط حتى ما ينكشف أحد).\n"
                                   "⏱️ 50 ثانية.\n\n" + mafia_status(g), 0x2C3E50), view=nv)
            await nv.wait()
            victim, saved = mafia_night(g.roles, g.alive, g.actions)
            if victim and not saved:
                g.alive.discard(victim)
                role = MAFIA_ROLES[g.roles[victim]]
                dawn = f"🌅 طلع الصباح… وانقتل **{g.name(victim)}** 💀 وكان {role[0]} **{role[1]}**."
            elif victim and saved:
                dawn = "🌅 طلع الصباح… المافيا حاولوا يقتلون أحداً لكن **الدكتور أنقذه** 🩺✨"
            else:
                dawn = "🌅 طلع الصباح… مرّت الليلة بسلام."
            winner = mafia_winner(g.roles, g.alive)
            await ctx.send(embed=E(f"☀️ النهار {day}", dawn, 0xF1C40F))
            if winner:
                break
            # ── النقاش ──
            skip = SkipToVoteView([m.id for m in g.alive_members()], timeout=75)
            await ctx.send(embed=E("💬 وقت النقاش",
                                   "ناقشوا وحاولوا تكشفون المافيا! (75 ثانية أو يضغط أكثر من النص زر الانتقال)\n\n" + mafia_status(g),
                                   0xE67E22), view=skip)
            await skip.wait()
            # ── التصويت ──
            vv = VoteView(g.alive_members(), g.alive_members(), timeout=50, skip_label="امتناع (لا أحد)",
                          placeholder="🗳️ من تريد إخراجه؟")
            await ctx.send(embed=E("🗳️ التصويت", "اختر من تشك فيه (50 ثانية):\n" + mention_list(g.alive_members()), 0xE74C3C), view=vv)
            await vv.wait()
            out, count, tie = plurality(vv.votes)
            if out is not None and out in g.alive:
                g.alive.discard(out)
                role = MAFIA_ROLES[g.roles[out]]
                res = f"⚖️ قرر الأغلبية إخراج **{g.name(out)}** ({count} صوت) وكان {role[0]} **{role[1]}**."
            elif tie:
                res = "⚖️ تعادلت الأصوات… ما انطرد أحد."
            else:
                res = "⚖️ ما اتفقوا على أحد… ما انطرد أحد."
            winner = mafia_winner(g.roles, g.alive)
            await ctx.send(embed=E("⚖️ نتيجة التصويت", res, 0xE74C3C))
            if winner:
                break
        reveal = "\n".join(f"{MAFIA_ROLES[g.roles[i]][0]} {m.mention} — {MAFIA_ROLES[g.roles[i]][1]}"
                           for i, m in g.players.items())
        if winner == "town":
            title, winners = "🏆 فاز المواطنون!", [m for i, m in g.players.items() if g.roles[i] != "mafia"]
        elif winner == "mafia":
            title, winners = "🔪 فازت المافيا!", [m for i, m in g.players.items() if g.roles[i] == "mafia"]
        else:
            title, winners = "🤝 تعادل (انتهت الأيام)", []
        await ctx.send(embed=E(title, f"**الأدوار:**\n{reveal}", GOLD))
        await finish_game_rewards(ctx, players, winners, 150, 20, 30)
    finally:
        ACTIVE.discard(ctx.channel.id)

# ───────────────────────── 4) كود نيمز بالصور ─────────────────────────
CN_COLORS = {"red": (214, 61, 66), "blue": (50, 110, 215), "neutral": (176, 166, 146), "assassin": (28, 28, 34)}
CN_EMOJI = {"red": "🔴", "blue": "🔵", "neutral": "⚪", "assassin": "💀"}
CN_TEAM = {"red": "الأحمر 🔴", "blue": "الأزرق 🔵"}
CN_MAX_TEAM = 5

def cn_other(team):
    return "blue" if team == "red" else "red"

class CNGame:
    """منطق كود نيمز (نسخة الصور): 20 بطاقة = 8 للفريق الأول + 7 للثاني + 4 محايدة + 1 قاتلة."""
    def __init__(self, red, blue, rng=random):
        self.players = {"red": list(red), "blue": list(blue)}   # أول لاعب = الجاسوس
        self.cards = rng.sample(list(CN_ICONS), 20)
        self.first = rng.choice(["red", "blue"])
        roles = [self.first] * 8 + [cn_other(self.first)] * 7 + ["neutral"] * 4 + ["assassin"]
        rng.shuffle(roles)
        self.roles = roles
        self.revealed = [False] * 20
        self.turn = self.first
        self.clue = None
        self.guesses_left = 0
        self.winner = None
        self.log = []

    def remaining(self, team):
        return sum(1 for r, v in zip(self.roles, self.revealed) if r == team and not v)

    def spymaster(self, team):
        return self.players[team][0]

    def operatives(self, team):
        return self.players[team][1:]

    def set_clue(self, word, number):
        self.clue = (word, number)
        self.guesses_left = 99 if number == 0 else number + 1

    def end_turn(self):
        self.turn = cn_other(self.turn)
        self.clue, self.guesses_left = None, 0

    def guess(self, idx):
        """يكشف البطاقة. يرجع (دورها, هل انتهى الدور)."""
        if self.winner or self.revealed[idx]:
            raise ValueError("invalid guess")
        self.revealed[idx] = True
        role, team = self.roles[idx], self.turn
        opp = cn_other(team)
        if role == "assassin":
            self.winner = opp
            return role, True
        if self.remaining(team) == 0:
            self.winner = team
            return role, True
        if self.remaining(opp) == 0:
            self.winner = opp
            return role, True
        if role == team:
            self.guesses_left -= 1
            if self.guesses_left <= 0:
                self.end_turn()
                return role, True
            return role, False
        self.end_turn()
        return role, True

def render_cn_board(game, key=False, reveal_all=False):
    """يرسم لوحة 5×4. key=True → مفتاح الجاسوس (ألوان الأدوار ظاهرة)."""
    cols, rows, cw, ch, gap, top = 5, 4, 190, 168, 14, 74
    W, H = cols * cw + (cols + 1) * gap, top + rows * ch + (rows + 1) * gap
    img = Image.new("RGB", (W, H), (24, 22, 40))
    d = ImageDraw.Draw(img)
    d.text((gap + 8, 20), f"RED {game.remaining('red')}", font=get_font(36), fill=CN_COLORS["red"])
    d.text((W - gap - 8, 20), f"BLUE {game.remaining('blue')}", font=get_font(36), fill=CN_COLORS["blue"], anchor="ra")
    d.text((W // 2, 40), "SPYMASTER KEY" if key else "CODENAMES", font=get_font(26), fill=(255, 215, 0), anchor="mm")
    for i, name in enumerate(game.cards):
        r, c = divmod(i, cols)
        x, y = gap + c * (cw + gap), top + gap + r * (ch + gap)
        role = game.roles[i]
        shown = game.revealed[i] or reveal_all
        bg = CN_COLORS[role] if shown else (247, 239, 219)
        d.rounded_rectangle((x, y, x + cw, y + ch), radius=18, fill=bg)
        ic = cn_icon(name, 112).copy()
        if shown:
            ic.putalpha(ic.getchannel("A").point(lambda v: int(v * 0.38)))
        img.paste(ic, (x + (cw - 112) // 2, y + 20), ic)
        if key and not shown:
            d.rounded_rectangle((x, y, x + cw, y + ch), radius=18, outline=CN_COLORS[role], width=7)
            d.rounded_rectangle((x + 8, y + ch - 36, x + cw - 8, y + ch - 8), radius=10, fill=CN_COLORS[role])
            lab = {"red": "RED", "blue": "BLUE", "neutral": "SAFE", "assassin": "DEADLY"}[role]
            d.text((x + cw // 2, y + ch - 22), lab, font=get_font(20), fill=(255, 255, 255), anchor="mm")
        if shown and role == "assassin":
            d.line((x + 40, y + 30, x + cw - 40, y + ch - 30), fill=(255, 255, 255), width=10)
            d.line((x + cw - 40, y + 30, x + 40, y + ch - 30), fill=(255, 255, 255), width=10)
        d.ellipse((x + 8, y + 8, x + 42, y + 42), fill=(40, 36, 60))
        d.text((x + 25, y + 25), str(i + 1), font=get_font(20), fill=(255, 255, 255), anchor="mm")
    out = io.BytesIO()
    img.save(out, "PNG")
    out.seek(0)
    return out

async def cn_board_file(game, key=False, reveal_all=False, filename="board.png"):
    buf = await asyncio.to_thread(render_cn_board, game, key, reveal_all)
    return discord.File(buf, filename=filename)

class CNLobbyView(discord.ui.View):
    def __init__(self, host):
        super().__init__(timeout=120)
        self.host = host
        self.teams = {"red": [host], "blue": []}
        self.started = False

    def all_players(self):
        return self.teams["red"] + self.teams["blue"]

    def embed(self):
        def names(t):
            lst = self.teams[t]
            return "\n".join(f"{'🕵️' if i == 0 else '🎯'} {m.mention}" for i, m in enumerate(lst)) or "— فاضي —"
        e = E("🖼️ كود نيمز — نسخة الصور",
              "فريقان يتنافسان على كشف **صورهم** عبر تلميحات الجاسوس.\n"
              "🕵️ الجاسوس يشوف المفتاح السري ويعطي تلميحاً (كلمة + رقم) • 🎯 المحققون يخمنون بالأزرار.\n"
              f"كل فريق من 2 إلى {CN_MAX_TEAM} لاعبين. أول لاعب بالفريق هو الجاسوس (غيّره بزر **اصير الجاسوس**).", PURPLE)
        e.add_field(name="🔴 الفريق الأحمر", value=names("red"), inline=True)
        e.add_field(name="🔵 الفريق الأزرق", value=names("blue"), inline=True)
        e.set_footer(text=f"المضيف: {self.host.display_name} • يبدأ اللعب بزر ابدأ")
        return e

    def _team_of(self, uid):
        for t, lst in self.teams.items():
            if any(m.id == uid for m in lst):
                return t
        return None

    async def _join(self, interaction, team):
        user = interaction.user
        if user.bot:
            return
        if len(self.teams[team]) >= CN_MAX_TEAM and self._team_of(user.id) != team:
            return await interaction.response.send_message("❌ الفريق ممتلئ.", ephemeral=True)
        for lst in self.teams.values():
            lst[:] = [m for m in lst if m.id != user.id]
        self.teams[team].append(user)
        await interaction.response.edit_message(embed=self.embed(), view=self)

    @discord.ui.button(label="الأحمر", emoji="🔴", style=discord.ButtonStyle.danger, row=0)
    async def join_red(self, interaction, button):
        await self._join(interaction, "red")

    @discord.ui.button(label="الأزرق", emoji="🔵", style=discord.ButtonStyle.primary, row=0)
    async def join_blue(self, interaction, button):
        await self._join(interaction, "blue")

    @discord.ui.button(label="اصير الجاسوس", emoji="🕵️", style=discord.ButtonStyle.secondary, row=0)
    async def be_spy(self, interaction, button):
        t = self._team_of(interaction.user.id)
        if t is None:
            return await interaction.response.send_message("انضم لفريق أولاً.", ephemeral=True)
        lst = self.teams[t]
        me = next(m for m in lst if m.id == interaction.user.id)
        lst.remove(me)
        lst.insert(0, me)
        await interaction.response.edit_message(embed=self.embed(), view=self)

    @discord.ui.button(label="خروج", emoji="🚪", style=discord.ButtonStyle.secondary, row=1)
    async def leave(self, interaction, button):
        if interaction.user.id == self.host.id:
            return await interaction.response.send_message("أنت المضيف، اضغط ابدأ أو اتركها تنتهي.", ephemeral=True)
        for lst in self.teams.values():
            lst[:] = [m for m in lst if m.id != interaction.user.id]
        await interaction.response.edit_message(embed=self.embed(), view=self)

    @discord.ui.button(label="ابدأ", emoji="▶️", style=discord.ButtonStyle.success, row=1)
    async def start(self, interaction, button):
        if interaction.user.id != self.host.id:
            return await interaction.response.send_message("❌ فقط المضيف يبدأ.", ephemeral=True)
        if len(self.teams["red"]) < 2 or len(self.teams["blue"]) < 2:
            return await interaction.response.send_message("❌ كل فريق يحتاج لاعبين اثنين على الأقل (جاسوس + محقق).", ephemeral=True)
        self.started = True
        await interaction.response.defer()
        self.stop()

class CNCardButton(discord.ui.Button):
    def __init__(self, idx):
        super().__init__(label=str(idx + 1), style=discord.ButtonStyle.secondary, row=idx // 5)
        self.idx = idx

    async def callback(self, interaction):
        await self.view.on_guess(interaction, self.idx)

class CNView(discord.ui.View):
    def __init__(self, game):
        super().__init__(timeout=None)
        self.game = game
        self.phase = "clue"          # clue | guess | between
        self.lock = asyncio.Lock()
        self.turn_event = asyncio.Event()
        self.message = None
        self.cards = [CNCardButton(i) for i in range(20)]
        for b in self.cards:
            self.add_item(b)

    def refresh_buttons(self):
        g = self.game
        for i, b in enumerate(self.cards):
            if g.revealed[i]:
                role = g.roles[i]
                b.disabled, b.emoji = True, CN_EMOJI[role]
                b.style = {"red": discord.ButtonStyle.danger, "blue": discord.ButtonStyle.primary,
                           "neutral": discord.ButtonStyle.secondary, "assassin": discord.ButtonStyle.secondary}[role]
            else:
                b.disabled = not (self.phase == "guess" and g.winner is None)

    def embed(self, note=None):
        g = self.game
        team = g.turn
        color = discord.Color(CN_COLORS[team][0] << 16 | CN_COLORS[team][1] << 8 | CN_COLORS[team][2])
        e = discord.Embed(title="🖼️ كود نيمز", color=color, timestamp=discord.utils.utcnow())
        e.add_field(name="🎯 الدور", value=f"الفريق {CN_TEAM[team]}", inline=True)
        e.add_field(name="🕵️ الجاسوس", value=g.spymaster(team).mention, inline=True)
        if g.clue:
            word, num = g.clue
            e.add_field(name="💬 التلميح", value=f"**{word}** — `{num if num else '∞'}`", inline=True)
            e.add_field(name="🎲 محاولات متبقية", value=f"`{g.guesses_left if g.guesses_left < 90 else '∞'}`", inline=True)
        e.add_field(name="📊 المتبقي", value=f"🔴 `{g.remaining('red')}` • 🔵 `{g.remaining('blue')}`", inline=True)
        ops = " ".join(m.mention for m in g.operatives(team)) or "—"
        e.add_field(name="🎯 المحققون", value=ops, inline=True)
        if g.log:
            e.add_field(name="📜 آخر الأحداث", value="\n".join(g.log[-4:]), inline=False)
        if note:
            e.description = note
        e.set_image(url="attachment://board.png")
        e.set_footer(text=footer_text())
        return e

    async def render(self, interaction=None, note=None, reveal_all=False):
        self.refresh_buttons()
        f = await cn_board_file(self.game, reveal_all=reveal_all)
        e = self.embed(note)
        if interaction is not None:
            await interaction.edit_original_response(embed=e, attachments=[f], view=self)
        else:
            await self.message.edit(embed=e, attachments=[f], view=self)

    async def on_guess(self, interaction, idx):
        g = self.game
        async with self.lock:
            if self.phase != "guess" or g.winner:
                return await interaction.response.send_message("⏳ انتظروا تلميح الجاسوس.", ephemeral=True)
            if interaction.user.id not in [m.id for m in g.operatives(g.turn)]:
                return await interaction.response.send_message("❌ مو دورك — فقط محققو الفريق الحالي يخمنون.", ephemeral=True)
            if g.revealed[idx]:
                return await interaction.response.send_message("هذي البطاقة انكشفت.", ephemeral=True)
            await interaction.response.defer()
            team = g.turn
            role, ended = g.guess(idx)
            tag = {"assassin": "💀 **القاتلة!**", team: "✅ صح!"}.get(role, "❌ خطأ" if role in ("red", "blue") else "⚪ محايدة")
            g.log.append(f"{interaction.user.display_name}: #{idx + 1} ← {tag} ({CN_ICON_AR(g.cards[idx])})")
            if g.winner or ended:
                self.phase = "between"
                self.turn_event.set()
            await self.render(interaction)

    @discord.ui.button(label="إنهاء الدور", emoji="⏹️", style=discord.ButtonStyle.secondary, row=4)
    async def end_turn_btn(self, interaction, button):
        g = self.game
        async with self.lock:
            if self.phase != "guess" or g.winner:
                return await interaction.response.send_message("⏳ مو وقته.", ephemeral=True)
            if interaction.user.id not in [m.id for m in g.operatives(g.turn)]:
                return await interaction.response.send_message("❌ فقط محققو الفريق الحالي.", ephemeral=True)
            await interaction.response.defer()
            g.log.append(f"{interaction.user.display_name}: ⏹️ أنهى الدور")
            g.end_turn()
            self.phase = "between"
            self.turn_event.set()
            await self.render(interaction)

    @discord.ui.button(label="مفتاح الجاسوس", emoji="🔑", style=discord.ButtonStyle.success, row=4)
    async def key_btn(self, interaction, button):
        g = self.game
        if interaction.user.id not in (g.spymaster("red").id, g.spymaster("blue").id):
            return await interaction.response.send_message("🔒 المفتاح للجاسوسين فقط.", ephemeral=True)
        await interaction.response.defer(ephemeral=True)
        f = await cn_board_file(g, key=True, filename="key.png")
        await interaction.followup.send("🔑 **مفتاحك السري** — لا تشاركه! (🔴 أحمر • 🔵 أزرق • SAFE محايد • DEADLY قاتلة)",
                                        file=f, ephemeral=True)

def CN_ICON_AR(name):
    return name

CLUE_RE = re.compile(r"^\s*(\S+(?:\s+\S+)?)\s+(\d)\s*$")

async def cn_wait_clue(ctx, spy, timeout=150):
    RAW_BLOCK.add(ctx.channel.id)
    try:
        m = await bot.wait_for("message", timeout=timeout,
                               check=lambda x: x.channel.id == ctx.channel.id and x.author.id == spy.id
                               and CLUE_RE.match(x.content or ""))
        word, num = CLUE_RE.match(m.content).groups()
        return word[:30], int(num)
    except asyncio.TimeoutError:
        return None
    finally:
        RAW_BLOCK.discard(ctx.channel.id)

async def run_codenames(ctx, red, blue):
    game = CNGame(red, blue)
    view = CNView(game)
    view.refresh_buttons()
    f = await cn_board_file(game)
    allp = red + blue
    view.message = await ctx.send(content=mention_list(allp), embed=view.embed("🎬 بدأت اللعبة!"), file=f, view=view)
    idle = 0
    while game.winner is None:
        team = game.turn
        spy = game.spymaster(team)
        view.phase = "clue"
        view.turn_event.clear()
        async with view.lock:
            await view.render(note=f"⏳ {spy.mention} اكتب تلميحك بالشات: **كلمة ثم رقم** — مثال: `سريع 2`\n"
                                   "(الرقم 0 = بلا حد) • اضغط 🔑 لتشوف المفتاح")
        clue = await cn_wait_clue(ctx, spy)
        if clue is None:
            idle += 1
            game.log.append(f"⌛ {spy.display_name} ما أعطى تلميحاً")
            if idle >= 2:
                await ctx.send(embed=E("🛑 أُلغيت اللعبة", "ما في نشاط كافٍ من الجواسيس.", 0xE74C3C))
                view.stop()
                return
            game.end_turn()
            continue
        word, num = clue
        num = min(num, game.remaining(team)) if num else 0
        game.set_clue(word, num)
        view.phase = "guess"
        async with view.lock:
            await view.render(note=f"🎯 محققو الفريق {CN_TEAM[team]}: خمّنوا بالأزرار!")
        try:
            await asyncio.wait_for(view.turn_event.wait(), timeout=240)
            idle = 0
        except asyncio.TimeoutError:
            async with view.lock:
                if game.winner is None:
                    game.log.append(f"⌛ انتهى وقت الفريق {team}")
                    game.end_turn()
                    view.phase = "between"
            idle += 1
            if idle >= 3:
                await ctx.send(embed=E("🛑 أُلغيت اللعبة", "ما في نشاط كافٍ من المحققين.", 0xE74C3C))
                view.stop()
                return
    async with view.lock:
        view.phase = "between"
        view.refresh_buttons()
        for b in view.children:
            b.disabled = True
        f = await cn_board_file(game, reveal_all=True)
        e = view.embed(f"🏆 فاز الفريق {CN_TEAM[game.winner]}!")
        await view.message.edit(embed=e, attachments=[f], view=view)
    view.stop()
    winners = game.players[game.winner]
    await finish_game_rewards(ctx, allp, winners, 200, 25, 30)
    await ctx.send(embed=E("🏆 نهاية كود نيمز",
                           f"الفائزون: {mention_list(winners)}\n💰 كل فائز +`200` وXP • والبقية +`30` عملة", GOLD))

@bot.command(name="كود_نيمز", aliases=["كودنيمز", "codenames", "كود"])
@commands.guild_only()
async def codenames_cmd(ctx):
    if not PIL_OK:
        return await ctx.reply("❌ هذي اللعبة تحتاج مكتبة Pillow (`pip install pillow`).")
    if not await game_guard(ctx):
        return
    try:
        lobby = CNLobbyView(ctx.author)
        msg = await ctx.send(embed=lobby.embed(), view=lobby)
        await lobby.wait()
        for c in lobby.children:
            c.disabled = True
        try:
            await msg.edit(view=lobby)
        except discord.HTTPException:
            pass
        if not lobby.started:
            return await ctx.send("❌ انتهى وقت التجميع ولم تبدأ اللعبة.")
        await run_codenames(ctx, lobby.teams["red"], lobby.teams["blue"])
    finally:
        RAW_BLOCK.discard(ctx.channel.id)
        ACTIVE.discard(ctx.channel.id)

# تحديث لوحة الألعاب + المساعدة بالألعاب الجديدة
HELP_SECTIONS["newgames"] = ("🆕", "الألعاب الجديدة", "ألغاز، برا السالفة، مافيا، وكود نيمز بالصور — كلها جماعية.", [
    "🧩 ألغاز وتفكير",
    ("ألغاز", "ألغاز [عدد 1-10]", "جولة ألغاز: أول من يكتب الجواب يربح عملات، وزر تلميح يخفّض الجائزة."),
    ("برا_السالفة", "برا_السالفة", "الكل يعرف الكلمة إلا واحد! ناقشوا وصوّتوا لكشفه (3-10 لاعبين)."),
    "🎭 أدوار سرية",
    ("مافيا", "مافيا", "ليل ونهار: مافيا ضد مواطنين مع دكتور ومحقق، أدوار مخفية بأزرار (5-12 لاعب)."),
    "🖼️ بالصور",
    ("كود_نيمز", "كود_نيمز", "فريقان (أحمر/أزرق) يكشفون صورهم بتلميحات الجاسوس، لوحة صور مرسومة + مفتاح سري."),
])


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

# ═════════════════════════ قسم البوت الذكي (دردشة + تلقائي + جيفاواي + صلاة) ═════════════════════════
AI_MODEL = (os.getenv("AI_MODEL") or "gemini-2.5-flash").strip()
GEMINI_KEY_ENV = "GEMINI_API_KEY"
AI_FALLBACK_MODELS = ["gemini-flash-latest", "gemini-flash-lite-latest"]
ON_WORDS = ("تشغيل", "تفعيل", "شغل", "فعل", "on", "ON")
OFF_WORDS = ("ايقاف", "إيقاف", "اطفاء", "وقف", "تعطيل", "off", "OFF")

HELP_SECTIONS["ai"] = ("🤖", "قسم البوت الذكي", "دردشة ذكية، رسائل تلقائية، جيفاواي عشوائي، تذكير بالصلاة.", [
    "💬 الدردشة",
    ("ذكاء", "ذكاء [تشغيل|ايقاف]", "يفتح **لوحة التحكم** بأزرار لتشغيل/إيقاف الدردشة والتلقائي والصلاة والجيفاواي (للإدارة العليا فقط)."),
    ("بوت", "بوت [كلامك]", "سولف مع البوت مباشرة، أو منشنه، أو رد على رسالته (وإذا أرفقت صورة يشوفها ويجاوب عنها)."),
    ("نموذج", "نموذج [chatgpt|gemini|claude|groq|deepseek|openrouter|تلقائي]", "يفتح قائمة اختيار نموذج الذكاء لهذا السيرفر (ChatGPT, Gemini, Claude ...) مع زر اختبار."),
    ("ارسم", "ارسم [وصف الصورة]", "ينشئ صورة من الوصف مجاناً بالذكاء الاصطناعي."),
    ("وصف", "وصف [سؤال اختياري] + أرفق صورة أو رد على صورة", "يصف لك الصورة بالتفصيل أو يجاوب عن سؤالك حولها."),
    ("ذكاء_روم", "ذكاء_روم #روم", "الروم الذي يرسل فيه البوت رسائله التلقائية والجيفاواي والصلاة."),
    "✨ الرسائل التلقائية",
    ("تلقائي", "تلقائي [تشغيل|ايقاف|الان]", "حديث، آية، سؤال أو دعاء بأوقات عشوائية (كل ساعات أو يوم أو يومين)."),
    ("صلاة", "صلاة [تشغيل|ايقاف|مدينة Baghdad Iraq]", "تذكير بأوقات الصلاة حسب المدينة."),
    "🎁 الجيفاواي العشوائي",
    ("جيفاواي", "جيفاواي [تشغيل|ايقاف|الان|حالة]", "جيفاواي بأوقات ومدد وجوائز عشوائية (عملات / رتبة من اختيار البوت / جوائز خاصة)."),
    ("جيفاواي_جائزة", "جيفاواي_جائزة [اضافة نص | حذف رقم | قائمة]", "جوائز خاصة تدخل في السحب العشوائي (مثل: كيس بي)."),
])

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
FALLBACK_REPLIES = [
    "هلا والله! 😄 شلونك؟",
    "عيوني إلك، تفضل شتريد؟ 😎",
    "آمر دلل! 🫡",
    "ههههه والله مرات أضحك على حالي، كمّل أسمعك 😂",
    "حياك الله! تحچي وياي لو أسمع بس؟ 😉",
    "تدلل، أنا هنا 👑",
]
CONGRATS = ("مبروك", "ألف مبروك", "عاش يا وحش", "كفو يا بطل", "تهانينا الحارة")
PRAYERS = (("Fajr", "الفجر"), ("Dhuhr", "الظهر"), ("Asr", "العصر"), ("Maghrib", "المغرب"), ("Isha", "العشاء"))
CHAT_MEM = defaultdict(lambda: deque(maxlen=10))
_ai_last = {}
_prayer_cache = {}
_prayer_fail = {}

def ai_cfg(guild):
    return db.cfg(guild.id).setdefault("ai", {})

def ai_channel(guild):
    cid = (db.cfg(guild.id).get("ai") or {}).get("channel")
    ch = guild.get_channel(cid) if cid else None
    return ch or get_channel(guild, "games_channel", GAMES_NAMES)

# ───── محرك النماذج المتعددة (Gemini • ChatGPT • Claude • Groq • DeepSeek • OpenRouter) ─────
# المفاتيح من متغيرات البيئة؛ الأدمن يختار النموذج لكل سيرفر بأمر  نموذج  (أو القائمة).
# إذا فشل النموذج المختار يجرّب البوت تلقائياً البدائل المتاحة حتى لا يسكت.
AI_PROVIDERS = {
    "gemini": {"label": "Gemini", "emoji": "✨", "keys": ("GEMINI_API_KEY", "GOOGLE_API_KEY"),
               "model_env": "AI_MODEL", "model": "gemini-2.5-flash", "vision": True,
               "desc": "من Google • سريع وفيه رؤية للصور"},
    "openai": {"label": "ChatGPT", "emoji": "🟢", "keys": ("OPENAI_API_KEY",),
               "model_env": "OPENAI_MODEL", "model": "gpt-4o-mini", "vision": True,
               "base": "https://api.openai.com/v1", "desc": "من OpenAI • ذكي ومتوازن"},
    "claude": {"label": "Claude", "emoji": "🟠", "keys": ("ANTHROPIC_API_KEY",),
               "model_env": "ANTHROPIC_MODEL", "model": "claude-haiku-5-5", "vision": True,
               "desc": "من Anthropic • أسلوب طبيعي ودقيق"},
    "groq": {"label": "Groq (Llama)", "emoji": "⚡", "keys": ("GROQ_API_KEY",),
             "model_env": "GROQ_MODEL", "model": "llama-3.3-70b-versatile", "vision": False,
             "base": "https://api.groq.com/openai/v1", "desc": "سرعة خرافية • نص فقط"},
    "deepseek": {"label": "DeepSeek", "emoji": "🐋", "keys": ("DEEPSEEK_API_KEY",),
                 "model_env": "DEEPSEEK_MODEL", "model": "deepseek-chat", "vision": False,
                 "base": "https://api.deepseek.com/v1", "desc": "اقتصادي وقوي • نص فقط"},
    "openrouter": {"label": "OpenRouter", "emoji": "🌐", "keys": ("OPENROUTER_API_KEY",),
                   "model_env": "OPENROUTER_MODEL", "model": "openai/gpt-4o-mini", "vision": True,
                   "base": "https://openrouter.ai/api/v1", "desc": "بوابة لمئات النماذج"},
}
AI_AUTO_ORDER = ("gemini", "openai", "claude", "groq", "deepseek", "openrouter")
AI_NAME_ALIASES = {
    "auto": "auto", "تلقائي": "auto", "اوتو": "auto",
    "gemini": "gemini", "جيميني": "gemini", "جمني": "gemini", "google": "gemini",
    "openai": "openai", "chatgpt": "openai", "gpt": "openai", "جات": "openai", "شات": "openai",
    "جات_جي_بي_تي": "openai", "شات_جي_بي_تي": "openai", "جيبيتي": "openai",
    "claude": "claude", "كلود": "claude",
    "groq": "groq", "llama": "groq", "لاما": "groq", "غروق": "groq",
    "deepseek": "deepseek", "ديب_سيك": "deepseek", "ديبسيك": "deepseek",
    "openrouter": "openrouter", "اوبن_راوتر": "openrouter",
}

def provider_key(pid):
    for env in AI_PROVIDERS[pid]["keys"]:
        v = (os.getenv(env) or "").strip()
        if v:
            return v
    return ""

def provider_model(pid):
    p = AI_PROVIDERS[pid]
    return (os.getenv(p["model_env"]) or p["model"]).strip()

def available_providers(vision=False):
    return [pid for pid in AI_AUTO_ORDER
            if provider_key(pid) and (AI_PROVIDERS[pid]["vision"] or not vision)]

def ai_key():
    """يرجع أي مفتاح متاح (للتوافق مع الأوامر القديمة): truthy إذا وُجد نموذج واحد على الأقل."""
    pids = available_providers()
    return provider_key(pids[0]) if pids else ""

def guild_provider(guild):
    """النموذج المختار لهذا السيرفر: 'auto' أو أحد مفاتيح AI_PROVIDERS."""
    pid = ((db.cfg(guild.id).get("ai") or {}).get("provider") or "auto") if guild else "auto"
    return pid if pid in AI_PROVIDERS else "auto"

def provider_chain(guild, vision=False):
    """ترتيب المحاولة: النموذج المختار أولاً ثم بقية المتاحة."""
    avail = available_providers(vision)
    chosen = guild_provider(guild)
    if chosen != "auto" and chosen in avail:
        return [chosen] + [p for p in avail if p != chosen]
    return avail

async def _http_json(url, headers, body, timeout=25):
    async with bot.session.post(url, headers=headers, json=body,
                                timeout=aiohttp.ClientTimeout(total=timeout)) as r:
        if r.status != 200:
            txt = (await r.text())[:200]
            return r.status, None, txt
        return 200, await r.json(), ""

async def _call_gemini(system, prompt, max_tokens, images):
    key, model = provider_key("gemini"), provider_model("gemini")
    parts = [{"text": prompt}]
    for data, mime in (images or [])[:3]:
        parts.append({"inline_data": {"mime_type": mime, "data": base64.b64encode(data).decode()}})
    body = {"contents": [{"role": "user", "parts": parts}],
            "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.9}}
    if system:
        body["systemInstruction"] = {"parts": [{"text": system}]}
    for m in [model] + [x for x in AI_FALLBACK_MODELS if x != model]:
        try:
            st, j, err = await _http_json(
                f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent",
                {"x-goog-api-key": key, "content-type": "application/json"}, body)
        except Exception as e:
            print(f"[AI] gemini/{m} {e!r}")
            continue
        if st != 200:
            print(f"[AI] gemini/{m} http {st}: {err[:120]!r}")
            if st in (400, 401, 403) and "API key" in err:
                return None
            continue
        cand = (j.get("candidates") or [{}])[0]
        text = "".join(p.get("text", "") for p in (cand.get("content") or {}).get("parts", [])).strip()
        if text:
            return text
    return None

async def _call_openai_compat(pid, system, prompt, max_tokens, images):
    p, key, model = AI_PROVIDERS[pid], provider_key(pid), provider_model(pid)
    if images and p["vision"]:
        content = [{"type": "text", "text": prompt}] + [
            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{base64.b64encode(data).decode()}"}}
            for data, mime in images[:3]]
    else:
        content = prompt
    msgs = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": content}]
    body = {"model": model, "messages": msgs}
    if pid == "openai":
        body["max_completion_tokens"] = max_tokens   # يعمل مع كل موديلات OpenAI الحالية
    else:
        body["max_tokens"], body["temperature"] = max_tokens, 0.9
    headers = {"Authorization": f"Bearer {key}", "content-type": "application/json"}
    st, j, err = await _http_json(f"{p['base']}/chat/completions", headers, body)
    if st != 200:
        print(f"[AI] {pid}/{model} http {st}: {err[:120]!r}")
        return None
    msg = ((j.get("choices") or [{}])[0].get("message") or {})
    text = msg.get("content")
    if isinstance(text, list):
        text = "".join(x.get("text", "") for x in text if isinstance(x, dict))
    return (text or "").strip() or None

async def _call_claude(system, prompt, max_tokens, images):
    key, model = provider_key("claude"), provider_model("claude")
    content = [{"type": "image", "source": {"type": "base64", "media_type": mime,
                                            "data": base64.b64encode(data).decode()}}
               for data, mime in (images or [])[:3]] + [{"type": "text", "text": prompt}]
    body = {"model": model, "max_tokens": max_tokens, "temperature": 0.9,
            "messages": [{"role": "user", "content": content}]}
    if system:
        body["system"] = system
    headers = {"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
    st, j, err = await _http_json("https://api.anthropic.com/v1/messages", headers, body)
    if st != 200:
        print(f"[AI] claude/{model} http {st}: {err[:120]!r}")
        return None
    text = "".join(b.get("text", "") for b in (j.get("content") or []) if b.get("type") == "text").strip()
    return text or None

async def ai_complete_ex(system, prompt, max_tokens=300, images=None, guild=None, provider=None):
    """يرجع (النص, مفتاح النموذج الذي ردّ). provider يفرض نموذجاً معيناً (للاختبار)."""
    guild = guild or CUR_GUILD.get()
    vision = bool(images)
    chain = [provider] if provider else provider_chain(guild, vision)
    if provider and not provider_key(provider):
        return None, None
    for pid in chain:
        try:
            if pid == "gemini":
                text = await _call_gemini(system, prompt, max_tokens, images)
            elif pid == "claude":
                text = await _call_claude(system, prompt, max_tokens, images)
            else:
                text = await _call_openai_compat(pid, system, prompt, max_tokens, images)
        except Exception as e:
            print(f"[AI] {pid} {e!r}")
            text = None
        if text:
            return text, pid
    return None, None

async def ai_complete(system, prompt, max_tokens=300, images=None, guild=None):
    """واجهة بسيطة: تستخدم نموذج السيرفر الحالي مع بدائل تلقائية. images = [(bytes, mime)]."""
    text, _ = await ai_complete_ex(system, prompt, max_tokens, images, guild)
    return text

IMG_MIMES = {"image/png", "image/jpeg", "image/webp"}

async def message_images(message, limit=2):
    """صور الرسالة نفسها، أو الرسالة التي رُد عليها."""
    out = []
    srcs = [message]
    ref = message.reference
    if ref:
        target = ref.resolved if isinstance(ref.resolved, discord.Message) else None
        if target is None and ref.message_id:
            try:
                target = await message.channel.fetch_message(ref.message_id)
            except discord.HTTPException:
                target = None
        if target:
            srcs.append(target)
    for m in srcs:
        for a in m.attachments:
            mime = (a.content_type or "").split(";")[0].lower()
            if mime in IMG_MIMES and a.size <= 6_000_000:
                try:
                    out.append((await a.read(), mime))
                except discord.HTTPException:
                    pass
            if len(out) >= limit:
                return out
    return out

def persona(guild):
    name = bot_name_set(guild)
    names = [e.name for e in guild.emojis if e.available][:30]
    if name:
        who = (f"أنت {name}، بوت ديسكورد ذكي ومرح. اسمك الوحيد «{name}» وقد سمّاك به أونر السيرفر؛ "
               f"إذا سألك أحد عن اسمك قل «{name}» فقط، ولا تذكر أبداً أي اسم آخر ولا تقل إنك Gemini أو ChatGPT أو Claude أو أي نموذج.")
    else:
        who = ("أنت بوت ديسكورد ذكي ومرح وما عندك اسم بعد؛ إذا سألك أحد عن اسمك قل بخفة دم إنك لسه ما عندك اسم "
               "وإن أونر السيرفر يگدر يسميك بأمر `تعيين_اسم`، ولا تقل إنك Gemini أو ChatGPT أو Claude أو أي نموذج.")
    return (
        who + f" تعيش في سيرفر «{guild.name}». "
        "تحچي مثل شاب عراقي لطيف وخفيف دم (لهجة عراقية بيضاء مفهومة، وتتكيف مع أسلوب المتكلم). "
        "تتصرف كإنسان طبيعي: ردودك قصيرة (جملة إلى ثلاث)، ودودة وفيها مزح خفيف، وتستخدم الإيموجي باعتدال. "
        "لا تقول إنك نموذج لغة ولا تعيد السؤال. جاوب بإجابات صحيحة ومفيدة وممتعة، والمعلومات العامة والعلمية باختصار ودقة. "
        "إذا ما تعرف شيئاً قل ما أعرف بدل ما تخترع. "
        "لا تفتي بالأمور الدينية ولا تدخل بالسياسة الحزبية ولا تكتب شيئاً مسيئاً؛ إذا أحد استفزّك رد بخفة دم من غير إهانة. "
        "لا تكتب @everyone ولا @here ولا تمنشن أحداً. "
        "إذا حبيت ترفق ستيكر اكتب [ستيكر] بآخر الرد (نادراً). "
        + (f"إيموجيات السيرفر التي يمكنك استخدامها (اكتبها بهذا الشكل بالضبط): {' '.join(':' + n + ':' for n in names)}." if names else "")
    )

def finalize_reply(guild, raw):
    sticker = "[ستيكر]" in raw or "[sticker]" in raw.lower()
    raw = raw.replace("[ستيكر]", "").replace("[Sticker]", "").replace("[sticker]", "")
    emojis = {e.name: str(e) for e in guild.emojis if e.available}
    raw = re.sub(r":(\w{2,32}):", lambda m: emojis.get(m.group(1), m.group(0)), raw)
    raw = raw.replace("@everyone", "everyone").replace("@here", "here").strip()[:1900]
    if emojis and random.random() < 0.2 and not any(v in raw for v in emojis.values()):
        raw = f"{raw} {random.choice(list(emojis.values()))}".strip()
    if not sticker and guild.stickers and random.random() < 0.1:
        sticker = True
    return raw, sticker

async def ai_generate(guild, channel_id, author_name, text, images=None):
    ctx = "\n".join(f"{n}: {t}" for n, t in list(CHAT_MEM[channel_id])[-8:])
    prompt = (f"آخر الرسائل بالروم:\n{ctx}\n\n" if ctx else "") + f"{author_name} يكلمك الآن: {text}\nرد عليه."
    if images:
        prompt += "\n(مرفق صورة: انظر إليها وجاوب بحسب ما تراه فيها.)"
    raw = await ai_complete(persona(guild), prompt, 400 if images else 320, images) or random.choice(FALLBACK_REPLIES)
    return finalize_reply(guild, raw)

async def send_ai_reply(message, raw, sticker):
    guild = message.guild
    kwargs = {"mention_author": False, "allowed_mentions": discord.AllowedMentions.none()}
    if sticker and guild.stickers:
        kwargs["stickers"] = [random.choice(guild.stickers)]
    if not raw and "stickers" not in kwargs:
        raw = "😄"
    try:
        await message.reply(raw or None, **kwargs)
    except discord.HTTPException:
        kwargs.pop("stickers", None)
        try:
            await message.channel.send(raw or "😄", allowed_mentions=discord.AllowedMentions.none())
        except discord.HTTPException:
            return
    if raw:
        CHAT_MEM[message.channel.id].append((brand(guild)[0], raw[:300]))

async def ai_maybe_reply(message):
    try:
        guild = message.guild
        if not guild or not bot.user:
            return
        text = (message.content or "").strip()
        if text:
            CHAT_MEM[message.channel.id].append((message.author.display_name, text[:300]))
        if not (db.cfg(guild.id).get("ai") or {}).get("on", True):
            return
        mentioned = bot.user in message.mentions and not message.mention_everyone
        replied = False
        ref = message.reference
        if ref and ref.message_id:
            target = ref.resolved if isinstance(ref.resolved, discord.Message) else None
            if target is None:
                try:
                    target = await message.channel.fetch_message(ref.message_id)
                except discord.HTTPException:
                    target = None
            replied = bool(target and target.author.id == bot.user.id)
        if not (mentioned or replied):
            return
        clean = re.sub(rf"<@!?{bot.user.id}>", "", text).strip()[:600] or "هلا"
        ans = name_answer(guild, clean)
        if ans:
            await send_ai_reply(message, ans, False)
            return
        async with message.channel.typing():
            imgs = await message_images(message)
            raw, sticker = await ai_generate(guild, message.channel.id, message.author.display_name, clean, imgs)
        await send_ai_reply(message, raw, sticker)
    except Exception as e:
        print(f"[AI-REPLY] {e!r}")

@bot.command(name="بوت", aliases=["كلمني", "bot"])
@commands.guild_only()
async def talk_cmd(ctx, *, text: str = ""):
    if not (db.cfg(ctx.guild.id).get("ai") or {}).get("on", True):
        return await ctx.reply("😴 الذكاء متوقف بهذا السيرفر.")
    text = text.strip()[:600] or "هلا"
    CHAT_MEM[ctx.channel.id].append((ctx.author.display_name, text[:300]))
    ans = name_answer(ctx.guild, text)
    if ans:
        return await send_ai_reply(ctx.message, ans, False)
    async with ctx.typing():
        imgs = await message_images(ctx.message)
        raw, sticker = await ai_generate(ctx.guild, ctx.channel.id, ctx.author.display_name, text, imgs)
    await send_ai_reply(ctx.message, raw, sticker)


# ───── الرسم ووصف الصور ─────
async def pollinations_image(prompt, seed=None):
    url = ("https://image.pollinations.ai/prompt/" + quote(prompt[:900]) +
           f"?width=1024&height=1024&nologo=true&model=flux&seed={seed or random.randint(1, 999999)}")
    try:
        async with bot.session.get(url, timeout=aiohttp.ClientTimeout(total=90)) as r:
            if r.status != 200:
                print(f"[DRAW] http {r.status}")
                return None
            data = await r.read()
        return data if sniff_ext(data) else None
    except Exception as e:
        print(f"[DRAW] {e!r}")
        return None

@bot.command(name="ارسم", aliases=["رسم", "صورة_ذكاء", "draw", "imagine"])
@commands.guild_only()
@commands.cooldown(1, 15, commands.BucketType.user)
async def draw_cmd(ctx, *, prompt: str = ""):
    prompt = prompt.strip()
    if not prompt:
        ctx.command.reset_cooldown(ctx)
        return await ctx.reply("الاستخدام: `ارسم قطة فضائية تلبس تاج ملكي`")
    async with ctx.typing():
        # الوصف العربي يُترجم لإنجليزي ويُحسّن لنتيجة أجمل (إذا Gemini متصل)
        en = None
        if AR_RE.search(prompt) and ai_key():
            en = await ai_complete("You turn the user's image idea into one vivid English image-generation prompt. "
                                   "Output only the prompt, no quotes, max 60 words.", prompt, 150)
        final = (en or prompt).strip().split("\n")[0]
        data = await pollinations_image(final)
    if not data:
        ctx.command.reset_cooldown(ctx)
        return await ctx.reply("❌ تعذر إنشاء الصورة الآن، جرّب بعد شوي.")
    fn = f"ai_art{sniff_ext(data)}"
    e = E("🎨 رسم الذكاء الاصطناعي", f"**الوصف:** {prompt[:500]}", PURPLE)
    e.set_image(url=f"attachment://{fn}")
    e.set_footer(text=f"طلبها {ctx.author.display_name} • {footer_text(ctx.guild)}")
    await ctx.reply(embed=e, file=discord.File(io.BytesIO(data), filename=fn), mention_author=False)

@bot.command(name="وصف", aliases=["describe", "شنو_بالصورة"])
@commands.guild_only()
@commands.cooldown(1, 8, commands.BucketType.user)
async def describe_cmd(ctx, *, question: str = ""):
    if not available_providers(vision=True):
        return await ctx.reply("⚠️ ما في نموذج متصل يفهم الصور: ضع `GEMINI_API_KEY` أو `OPENAI_API_KEY` أو `ANTHROPIC_API_KEY`.")
    imgs = await message_images(ctx.message)
    if not imgs:
        ctx.command.reset_cooldown(ctx)
        return await ctx.reply("أرفق صورة مع الأمر، أو رد على رسالة فيها صورة واكتب `وصف`.")
    ask = question.strip() or "صف هذه الصورة بالتفصيل."
    async with ctx.typing():
        text = await ai_complete("أنت تصف الصور وتجاوب عنها بدقة وبلهجة عراقية بيضاء مفهومة، بدون اختراع تفاصيل غير موجودة.",
                                 ask, 700, imgs)
    if not text:
        return await ctx.reply("❌ تعذر تحليل الصورة الآن.")
    text = text.replace("@everyone", "everyone").replace("@here", "here")
    await ctx.reply(embed=E("🖼️ وصف الصورة", text[:3900], PURPLE), mention_author=False)

# ───── رسائل تلقائية ─────
async def ai_text_question(guild):
    q = await ai_complete(persona(guild), "اطرح سؤالاً واحداً خفيفاً ومسلياً (أو سؤال ثقافة عامة بسيط) على أعضاء السيرفر بلهجة عراقية، "
                          "بدون مقدمات، سطر واحد فقط.", 120)
    return (q or random.choice(FALLBACK_QUESTIONS)).strip().split("\n")[0][:300]

async def send_auto(guild, ch, kind=None):
    CUR_GUILD.set(guild)
    kind = kind or random.choices(["hadith", "ayah", "question", "salawat", "fun"], [25, 25, 25, 10, 15])[0]
    if kind == "hadith":
        t, s = random.choice(HADITHS)
        e = E("📜 حديث شريف", f"**{t}**\n\n— *{s}*", 0x2ECC71)
    elif kind == "ayah":
        t, s = random.choice(AYAHS)
        e = E("📖 آية من القرآن الكريم", f"﴿ {t} ﴾\n\n— *{s}*", GOLD)
    elif kind == "salawat":
        e = E("🤍 صلوا على النبي", "اللهم صلِّ وسلِّم على نبينا محمد ﷺ", 0x3498DB)
    elif kind == "fun":
        t = await ai_complete(persona(guild), "اكتب معلومة طريفة أو نكتة خفيفة نظيفة بسطرين كحد أقصى بلهجة عراقية.", 200)
        e = E("😄 هلا يا جماعة", (t or random.choice(FALLBACK_QUESTIONS)), PURPLE)
    else:
        q = await ai_text_question(guild)
        CHAT_MEM[ch.id].append((brand(guild)[0], q))
        e = E("💭 سؤال للمملكة", f"{q}\n\n*جاوبوني بالرد على رسالتي* 😄", PURPLE)
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
async def ai_tick(guild, now):
    cfg = db.cfg(guild.id)
    ai, gw = cfg.get("ai") or {}, cfg.get("gw") or {}
    ch = ai_channel(guild)
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
    if ai.get("auto"):
        if not ai.get("auto_next"):
            ai["auto_next"] = now + random.uniform(1800, 4 * 3600)
            db.mark()
        elif now >= ai["auto_next"]:
            ai["auto_next"] = now + random.choice([2, 4, 6, 8, 12, 24]) * 3600 * random.uniform(0.7, 1.3)
            db.mark()
            await send_auto(guild, ch)
    if ai.get("prayer"):
        ent = await get_prayer_times(ai.get("city", "Baghdad"), ai.get("country", "Iraq"))
        if ent:
            try:
                hm = datetime.now(ZoneInfo(ent["tz"])).strftime("%H:%M")
            except Exception:
                return
            for k, name in PRAYERS:
                tag = f"{ent['date']}-{k}"
                if ent["t"].get(k) == hm and ai.get("last_prayer") != tag:
                    ai["last_prayer"] = tag
                    db.mark()
                    CUR_GUILD.set(guild)
                    try:
                        await ch.send(embed=E("🕌 تذكير بالصلاة", random.choice(PRAYER_LINES).format(n=name), 0x2ECC71))
                    except discord.HTTPException:
                        pass

@tasks.loop(seconds=30)
async def ai_loop():
    try:
        now = time.time()
        for mid, gw in list(db.data.get("_gw", {}).items()):
            if now >= gw["end"]:
                await finish_giveaway(mid, gw)
        for guild in bot.guilds:
            await ai_tick(guild, now)
    except Exception as e:
        print(f"[AI-LOOP] {e!r}")

@ai_loop.before_loop
async def _before_ai_loop():
    await bot.wait_until_ready()

# ───── اسم البوت: جواب مباشر (بدون نموذج) عند سؤاله "شنو اسمك" ─────
NAME_Q_RE = re.compile(
    r"(شنو|شن|ايش|إيش|شو|وش|ما|شلون)\s*(هو\s*)?(اسمك|إسمك|اسم\s*البوت)"
    r"|(اسمك|إسمك)\s*(شنو|شن|ايش|إيش|شو|وش)"
    r"|(?<!\w)(شسمك|شاسمك|اسمك\s*ايش)(?!\w)"
    r"|(منو|من|شنو|ايش|إيش)\s*(انت|أنت|إنت)\b"
    r"|what(?:'s|\s+is|s)?\s+your\s+name|your\s+name\b|who\s+are\s+you",
    re.I)

def name_answer(guild, text):
    """إذا السؤال عن اسم البوت يرجع الجواب بالاسم الذي حدده أونر السيرفر؛ وإلا None."""
    if not text or not NAME_Q_RE.search(text):
        return None
    name = bot_name_set(guild)
    if name:
        return random.choice((f"اسمي **{name}** 😎", f"أنا **{name}**، تحت أمرك 🫡", f"يسمونني **{name}** 👑"))
    return "لحد الآن ما عندي اسم 😅 أونر السيرفر يگدر يسميني بأمر `تعيين_اسم اسم_البوت`"

# ───── قائمة نماذج الذكاء (احترافية: قائمة منسدلة + أزرار) ─────
def ai_models_embed(guild):
    chosen = guild_provider(guild)
    e = E("🧠 نماذج الذكاء الاصطناعي",
          "اختر النموذج الذي يرد به البوت في هذا السيرفر.\n"
          "إذا تعطّل النموذج المختار يجرّب البوت بديلاً متاحاً تلقائياً.\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬", PURPLE)
    cur = ("🔀 تلقائي (أول نموذج متاح)" if chosen == "auto"
           else f"{AI_PROVIDERS[chosen]['emoji']} {AI_PROVIDERS[chosen]['label']}")
    e.add_field(name="✅ المختار حالياً", value=f"**{cur}**", inline=False)
    for pid in AI_AUTO_ORDER:
        p = AI_PROVIDERS[pid]
        if provider_key(pid):
            kind = "👁️ يفهم الصور" if p["vision"] else "📝 نص فقط"
            val = f"🟢 متصل • {kind}\n`{provider_model(pid)}`\n{p['desc']}"
        else:
            val = f"⚪ غير مفعّل\n{p['desc']}\n*المفتاح: `{p['keys'][0]}`*"
        e.add_field(name=f"{p['emoji']} {p['label']}{' ◀️' if pid == chosen else ''}", value=val, inline=True)
    return e

class AIModelSelect(discord.ui.Select):
    def __init__(self, guild):
        chosen = guild_provider(guild)
        opts = [discord.SelectOption(label="تلقائي", value="auto", emoji="🔀",
                                     description="أول نموذج متاح مع بدائل تلقائية", default=(chosen == "auto"))]
        for pid in AI_AUTO_ORDER:
            p = AI_PROVIDERS[pid]
            on = bool(provider_key(pid))
            opts.append(discord.SelectOption(label=p["label"] + ("" if on else " (غير مفعّل)"), value=pid,
                                             emoji=p["emoji"], description=p["desc"][:100], default=(chosen == pid)))
        super().__init__(placeholder="🧠 اختر نموذج الذكاء", options=opts, row=0)

    async def callback(self, interaction):
        pid = self.values[0]
        if pid != "auto" and not provider_key(pid):
            p = AI_PROVIDERS[pid]
            return await interaction.response.send_message(
                f"⚠️ **{p['label']}** غير مفعّل: ضع المفتاح `{p['keys'][0]}` بمتغيرات البيئة ثم أعد تشغيل البوت.",
                ephemeral=True)
        ai_cfg(interaction.guild)["provider"] = pid
        db.mark()
        view = AIModelView(interaction.guild, self.view.author_id)
        view.message = self.view.message
        await interaction.response.edit_message(embed=ai_models_embed(interaction.guild), view=view)

class AIModelView(discord.ui.View):
    def __init__(self, guild, author_id=None):
        super().__init__(timeout=180)
        self.author_id, self.message = author_id, None
        self.add_item(AIModelSelect(guild))

    async def interaction_check(self, interaction):
        CUR_GUILD.set(interaction.guild)
        if is_admin(interaction.user):
            return True
        await interaction.response.send_message("🔒 هذي اللوحة للإدارة العليا فقط.", ephemeral=True)
        return False

    @discord.ui.button(label="اختبار", emoji="🧪", style=discord.ButtonStyle.success, row=1)
    async def test_btn(self, interaction, button):
        await interaction.response.defer(ephemeral=True, thinking=True)
        text, pid = await ai_complete_ex(persona(interaction.guild),
                                         "رحّب بالسيرفر بجملة قصيرة واذكر اسمك.", 120, guild=interaction.guild)
        if not text:
            return await interaction.followup.send("❌ ما رد أي نموذج، تأكد من المفاتيح ومن اتصال البوت.", ephemeral=True)
        p = AI_PROVIDERS[pid]
        text = text.replace("@everyone", "everyone").replace("@here", "here")
        await interaction.followup.send(f"{p['emoji']} **{p['label']}** • `{provider_model(pid)}`\n{text[:1500]}",
                                        ephemeral=True)

    @discord.ui.button(label="تحديث", emoji="🔄", style=discord.ButtonStyle.secondary, row=1)
    async def refresh_btn(self, interaction, button):
        view = AIModelView(interaction.guild, self.author_id)
        view.message = self.message
        await interaction.response.edit_message(embed=ai_models_embed(interaction.guild), view=view)

    @discord.ui.button(label="إغلاق", emoji="✖️", style=discord.ButtonStyle.danger, row=1)
    async def close_btn(self, interaction, button):
        self.stop()
        await interaction.response.edit_message(view=None)

    async def on_timeout(self):
        if self.message:
            try:
                await self.message.edit(view=None)
            except discord.HTTPException:
                pass

@bot.command(name="نموذج", aliases=["نماذج", "موديل", "model", "models"])
@commands.guild_only()
@admin_only()
async def ai_model_cmd(ctx, choice: str = None):
    if choice is None:
        view = AIModelView(ctx.guild, ctx.author.id)
        view.message = await ctx.send(embed=ai_models_embed(ctx.guild), view=view)
        return
    pid = AI_NAME_ALIASES.get(choice.strip().lower().replace(" ", "_"))
    if pid is None:
        return await ctx.reply("الاستخدام: `نموذج [تلقائي|chatgpt|gemini|claude|groq|deepseek|openrouter]` أو اكتب `نموذج` فقط للقائمة.")
    if pid != "auto" and not provider_key(pid):
        p = AI_PROVIDERS[pid]
        return await ctx.reply(f"⚠️ **{p['label']}** غير مفعّل: ضع المفتاح `{p['keys'][0]}` بمتغيرات البيئة.")
    ai_cfg(ctx.guild)["provider"] = pid
    db.mark()
    await ctx.send(embed=ai_models_embed(ctx.guild))

# ───── أوامر القسم ─────
def ai_status_embed(guild):
    cfg = db.cfg(guild.id)
    ai, gw = cfg.get("ai") or {}, cfg.get("gw") or {}
    ch = ai_channel(guild)
    st = lambda v: "🟢 شغّال" if v else "🔴 متوقف"
    e = E("🤖 لوحة تحكم البوت الذكي", "التحكم بهذا القسم للإدارة العليا فقط • الأزرار بالأسفل تشغّل/توقف كل ميزة.", PURPLE)
    e.add_field(name="💬 الدردشة (منشن/رد)", value=st(ai.get("on", True)), inline=True)
    e.add_field(name="✨ رسائل تلقائية", value=st(ai.get("auto")), inline=True)
    e.add_field(name="🕌 الصلاة", value=f"{st(ai.get('prayer'))} • `{ai.get('city', 'Baghdad')}, {ai.get('country', 'Iraq')}`", inline=True)
    nxt = f" • القادم <t:{int(gw['next'])}:R>" if gw.get("on") and gw.get("next") else ""
    e.add_field(name="🎁 الجيفاواي", value=st(gw.get("on")) + nxt, inline=True)
    e.add_field(name="📍 الروم", value=ch.mention if ch else "❌ غير محدد (`ذكاء_روم #روم`)", inline=True)
    chosen = guild_provider(guild)
    live = available_providers()
    if live:
        cur = "🔀 تلقائي" if chosen == "auto" else f"{AI_PROVIDERS[chosen]['emoji']} {AI_PROVIDERS[chosen]['label']}"
        e.add_field(name="🧠 النموذج", value=f"✅ {cur}\n`{len(live)}` نموذج متصل • الأمر `نموذج`", inline=True)
    else:
        e.add_field(name="🧠 النموذج", value="⚠️ ما في أي مفتاح (GEMINI_API_KEY / OPENAI_API_KEY ...) — ردود احتياطية فقط", inline=True)
    return e

def _need_channel(ctx):
    """يحدد روم الرسائل التلقائية بالروم الحالي إذا ما كان مضبوطاً."""
    ai = ai_cfg(ctx.guild)
    if not ai.get("channel") and not ai_channel(ctx.guild):
        ai["channel"] = ctx.channel.id
        db.mark()
        return True
    return False

def ensure_ai_channel(guild, channel):
    ai = ai_cfg(guild)
    if not ai.get("channel") and not ai_channel(guild):
        ai["channel"] = channel.id
        db.mark()

class AIPanelView(discord.ui.View):
    """لوحة تحكم البوت الذكي — للإدارة العليا فقط."""
    def __init__(self, guild):
        super().__init__(timeout=600)
        cfg = db.cfg(guild.id)
        ai, gw = cfg.get("ai") or {}, cfg.get("gw") or {}
        states = [("chat", "الدردشة", "💬", ai.get("on", True)), ("auto", "تلقائي", "✨", ai.get("auto")),
                  ("prayer", "الصلاة", "🕌", ai.get("prayer")), ("gw", "الجيفاواي", "🎁", gw.get("on"))]
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
        await interaction.response.send_message("❌ لوحة الذكاء للإدارة العليا فقط.", ephemeral=True)
        return False

    def _toggle(self, key):
        async def cb(interaction):
            guild = interaction.guild
            ai, gw = ai_cfg(guild), db.cfg(guild.id).setdefault("gw", {})
            if key == "chat":
                ai["on"] = not ai.get("on", True)
            elif key == "auto":
                ai["auto"] = not ai.get("auto")
                ai.pop("auto_next", None)
            elif key == "prayer":
                ai["prayer"] = not ai.get("prayer")
            else:
                gw["on"] = not gw.get("on")
                gw.pop("next", None)
            if key != "chat":
                ensure_ai_channel(guild, interaction.channel)
            db.mark()
            await interaction.response.edit_message(embed=ai_status_embed(guild), view=AIPanelView(guild))
        return cb

    async def _now_msg(self, interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        await send_auto(guild, ai_channel(guild) or interaction.channel)
        await interaction.followup.send("✅ انرسلت رسالة تلقائية.", ephemeral=True)

    async def _now_gw(self, interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        msg = await start_giveaway(guild, ai_channel(guild) or interaction.channel)
        await interaction.followup.send("✅ انطلق جيفاواي جديد." if msg else "❌ تعذر إرسال الجيفاواي.", ephemeral=True)

    async def _refresh(self, interaction):
        await interaction.response.edit_message(embed=ai_status_embed(interaction.guild), view=AIPanelView(interaction.guild))

@bot.command(name="ذكاء", aliases=["ai", "الذكاء", "لوحة_الذكاء"])
@commands.guild_only()
@admin_only()
async def ai_toggle(ctx, action: str = None):
    ai = ai_cfg(ctx.guild)
    if action in ON_WORDS:
        ai["on"] = True
        db.mark()
    elif action in OFF_WORDS:
        ai["on"] = False
        db.mark()
    await ctx.send(embed=ai_status_embed(ctx.guild), view=AIPanelView(ctx.guild))

@bot.command(name="ذكاء_روم", aliases=["روم_البوت"])
@commands.guild_only()
@admin_only()
async def ai_room(ctx, channel: discord.TextChannel = None):
    channel = channel or ctx.channel
    ai_cfg(ctx.guild)["channel"] = channel.id
    db.mark()
    await ctx.send(f"✅ رسائل البوت التلقائية والجيفاواي والصلاة بـ {channel.mention}.")

@bot.command(name="تلقائي", aliases=["سوالف"])
@commands.guild_only()
@admin_only()
async def auto_cmd(ctx, action: str = None):
    ai = ai_cfg(ctx.guild)
    if action in ON_WORDS:
        ai["auto"] = True
        ai.pop("auto_next", None)
        db.mark()
        note = " (حددت هذا الروم)" if _need_channel(ctx) else ""
        return await ctx.send(f"✨ تم تشغيل الرسائل التلقائية، تجي بأوقات عشوائية.{note}")
    if action in OFF_WORDS:
        ai["auto"] = False
        db.mark()
        return await ctx.send("🔴 تم إيقاف الرسائل التلقائية.")
    if action in ("الان", "الآن", "now"):
        ch = ai_channel(ctx.guild) or ctx.channel
        return await send_auto(ctx.guild, ch)
    await ctx.send(embed=ai_status_embed(ctx.guild))

@bot.command(name="صلاة", aliases=["الصلاة", "اذان"])
@commands.guild_only()
@admin_only()
async def prayer_cmd(ctx, action: str = None, *, rest: str = ""):
    ai = ai_cfg(ctx.guild)
    if action in ON_WORDS:
        ai["prayer"] = True
        db.mark()
        note = " (حددت هذا الروم)" if _need_channel(ctx) else ""
        return await ctx.send(f"🕌 تم تشغيل تذكير الصلاة لمدينة `{ai.get('city', 'Baghdad')}`.{note}")
    if action in OFF_WORDS:
        ai["prayer"] = False
        db.mark()
        return await ctx.send("🔴 تم إيقاف تذكير الصلاة.")
    if action in ("مدينة", "city"):
        parts = rest.split()
        if not parts:
            return await ctx.reply("الاستخدام: `صلاة مدينة Baghdad Iraq` (بالإنجليزي)")
        ai["city"], ai["country"] = parts[0], (parts[1] if len(parts) > 1 else "Iraq")
        db.mark()
        _prayer_cache.clear()
        return await ctx.send(f"✅ المدينة صارت `{ai['city']}, {ai['country']}`.")
    await ctx.send(embed=ai_status_embed(ctx.guild))

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
        msg = await start_giveaway(ctx.guild, ai_channel(ctx.guild) or ctx.channel)
        return None if msg else await ctx.reply("❌ تعذر إرسال الجيفاواي.")
    await ctx.send(embed=ai_status_embed(ctx.guild))

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
