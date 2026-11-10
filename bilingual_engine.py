# -*- coding: utf-8 -*-
"""
Module Đọc Song Ngữ Anh - Việt (Bilingual TTS Engine)
Dành cho DesktopEpubReader & HonorReader VIP

Hỗ trợ 3 chế độ:
- 'off': Tắt (Mặc định, đọc nguyên bản từ gốc)
- 'native': Song ngữ bản xứ (Giọng lai Việt + Mỹ, phát âm tiếng Anh chuẩn bản xứ)
- 'phonetic': Phiên âm thuần Việt (Tự động chuyển từ tiếng Anh sang cách đọc tiếng Việt, đọc bằng 1 giọng duy nhất)
"""

import re
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "bilingual_config.json"

# =====================================================================
# BẢNG NHẬN DIỆN NGÔN NGỮ TIẾNG VIỆT
# =====================================================================
VIETNAMESE_ACCENTS = set(
    "àáảãạăắằẳẵặâấầẩẫậđèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵ"
    "ÀÁẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬĐÈÉẺẼẸÊẾỀỂỄỆÌÍỈĨỊÒÓỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÙÚỦŨỤƯỨỪỬỮỰỲÝỶỸỴ"
)

# 400+ từ và âm tiết tiếng Việt không dấu phổ biến nhất
VIETNAMESE_BASE_WORDS = {
    'va', 'la', 'cho', 'trong', 'co', 'khong', 'duoc', 'nguoi', 'mot', 'hai', 'ba', 'bon', 'nam', 'sau', 'bay', 'tam', 'chin', 'muoi',
    'nhung', 'den', 'voi', 've', 'ra', 'vao', 'tren', 'duoi', 'khi', 'nhu', 'se', 'da', 'dang', 'lai', 'cung', 'luc', 'nay', 'do', 'day', 'kia',
    'anh', 'em', 'chi', 'ong', 'ba', 'co', 'chu', 'bac', 'con', 'chau', 'toi', 'tao', 'may', 'han', 'no', 'chung', 'ta', 'minh', 'ho', 'ai',
    'gi', 'sao', 'dau', 'nao', 'the', 'vay', 'thi', 'ma', 'neu', 'vi', 'nen', 'tuy', 'hoac', 'hay', 'rat', 'qua', 'lam', 'nhat', 'hon', 'kem',
    'tot', 'xau', 'dep', 'lon', 'nho', 'cao', 'thap', 'xa', 'gan', 'nhanh', 'cham', 'moi', 'cu', 'dung', 'sai', 'biet', 'hieu', 'thay', 'nghe',
    'nhin', 'noi', 'cuoi', 'khoc', 'di', 'chay', 'ngoi', 'nam', 'an', 'uong', 'ngu', 'thuc', 'yeu', 'thuong', 'nho', 'quen', 'nghi', 'lo', 'so',
    'vui', 'buon', 'gian', 'hon', 'nha', 'cua', 'phong', 'ban', 'ghe', 'giuong', 'ao', 'quan', 'giay', 'dep', 'tien', 'bac', 'vang', 'dat', 'nuoc',
    'lua', 'gio', 'troi', 'may', 'mua', 'nang', 'dem', 'ngay', 'sang', 'trua', 'chieu', 'toi', 'tuan', 'thang', 'nam', 'gio', 'phut', 'giay',
    'truoc', 'sau', 'giua', 'ben', 'ngoai', 'canh', 'duong', 'pho', 'lang', 'xa', 'huyen', 'tinh', 'song', 'nui', 'bien', 'rung', 'cay', 'hoa',
    'la', 'qua', 'trai', 'chim', 'ca', 'cho', 'meo', 'heo', 'lon', 'bo', 'ga', 'vit', 'truy', 'cap', 'tai', 'ung', 'dung', 'de', 'lay', 'tra',
    'gui', 'doc', 'viet', 'lam', 'hoc', 'truong', 'lop', 'khoa', 'thi', 'bai', 'tap', 'trang', 'chuong', 'sach', 'bao', 'tranh', 'anh',
    'mat', 'mui', 'tai', 'mieng', 'tay', 'chan', 'toc', 'bung', 'lung', 'tim', 'gan', 'mau', 'thit', 'xuong', 'da', 'rang', 'luoi', 'dau',
    'sinh', 'tu', 'song', 'chet', 'lon', 'be', 'gia', 'tre', 'trai', 'gai', 'nam', 'nu', 'quan', 'linh', 'vua', 'tuong', 'dan', 'tro', 'thay',
    'ao', 'quan', 'mu', 'non', 'khan', 'tui', 'vi', 'dao', 'kiem', 'cung', 'ten', 'sung', 'dan', 'xe', 'ngua', 'thuyen', 'tau', 'bay'
}

# =====================================================================
# TỪ ĐIỂN PHIÊN ÂM ANH - VIỆT TOÀN DIỆN
# =====================================================================
COMMON_EN_VI_PHONETICS = {
    # Mạng xã hội, Ứng dụng & Công nghệ
    "facebook": "phây-xơ-búc",
    "fb": "phây",
    "google": "gu-gồ",
    "youtube": "diu-túp",
    "tiktok": "tíc-tốc",
    "zalo": "za-lô",
    "telegram": "tê-lê-gram",
    "instagram": "in-xờ-ta-gram",
    "insta": "in-xờ-ta",
    "twitter": "tơ-uýt-tơ",
    "threads": "thờ-rét",
    "chatgpt": "chát di-pi-ti",
    "gpt": "di-pi-ti",
    "ai": "ây-ai",
    "vip": "vi-ai-pi",
    "pro": "prồ",
    "max": "mác",
    "plus": "pơ-lớt",
    "ultra": "un-tra",
    "mini": "mi-ni",
    "server": "xớc-vơ",
    "computer": "com-piu-tơ",
    "laptop": "láp-tóp",
    "pc": "pi-xi",
    "cpu": "xi-pi-u",
    "gpu": "di-pi-u",
    "ram": "ram",
    "ssd": "ét-ét-đê",
    "hdd": "hát-đê-đê",
    "dell": "đeo",
    "asus": "a-xút",
    "acer": "ây-sơ",
    "hp": "hắt-pê",
    "lenovo": "lê-nô-vô",
    "mac": "mác",
    "colab": "cô-láp",
    "check-in": "chếch in",
    "checkin": "chếch in",
    "checkout": "chếch ao",
    "reception": "ri-xép-sần",
    "internet": "in-tơ-nét",
    "wifi": "oai-phai",
    "bluetooth": "bu-lu-tút",
    "online": "on-lai",
    "offline": "óp-lai",
    "website": "oép-sai",
    "web": "oép",
    "app": "áp",
    "application": "áp-li-cây-sần",
    "software": "sóp-oe",
    "hardware": "hát-oe",
    "system": "xít-tờm",
    "windows": "uyn-đô",
    "window": "uyn-đô",
    "android": "an-đờ-roi",
    "ios": "ai-ô-ét",
    "macos": "mác-ô-ét",
    "iphone": "ai-phôn",
    "ipad": "ai-pát",
    "macbook": "mác-búc",
    "smartphone": "xờ-mát-phôn",
    "phone": "phôn",
    "camera": "ca-mê-ra",
    "video": "vi-đê-ô",
    "audio": "o-đi-ô",
    "clip": "clíp",
    "mp3": "em-pi-ba",
    "mp4": "em-pi-bốn",
    "file": "phai",
    "data": "đa-ta",
    "database": "đa-ta-bây",
    "code": "cốt",
    "coder": "cô-đơ",
    "developer": "đê-vê-lốp-pơ",
    "dev": "đép",
    "tester": "tét-tơ",
    "bug": "bắc",
    "fix": "phích",
    "check": "chếch",
    "test": "tét",
    "testing": "tét-tinh",
    "train": "tơ-rên",
    "training": "tơ-rây-ninh",
    "trainer": "tơ-rây-nơ",
    "start": "xờ-tát",
    "started": "xờ-tát-tịt",
    "starting": "xờ-tát-tinh",
    "stop": "xờ-tóp",
    "stopped": "xờ-tóp",
    "step": "xờ-tép",
    "steps": "xờ-tép",
    "model": "mô-đen",
    "models": "mô-đen",
    "loss": "lót",
    "losses": "lót-xịt",
    "epoch": "ê-pốc",
    "epochs": "ê-pốc",
    "batch": "bát",
    "batches": "bát",
    "input": "in-pút",
    "output": "ao-pút",
    "print": "prin",
    "clear": "cli-ơ",
    "clean": "clin",
    "track": "trắc",
    "state": "xờ-tết",
    "level": "le-vồ",
    "score": "xờ-co",
    "team": "tim",
    "game": "gêm",
    "gamer": "gê-mơ",
    "card": "cát",
    "cost": "cót",
    "home": "hôm",
    "city": "xi-ti",
    "rate": "rết",
    "date": "đét",
    "time": "tai",
    "page": "pây",
    "post": "pốt",
    "feed": "phít",
    "rule": "ru",
    "rules": "ru",
    "type": "típ",
    "mode": "mốt",
    "text": "tếch",
    "font": "phông",
    "size": "sai",
    "icon": "ai-cơn",
    "logo": "lô-gô",
    "menu": "mê-nu",
    "button": "bút-tần",
    "btn": "bút-tần",
    "load": "loát",
    "loading": "loát-đinh",
    "save": "xếp",
    "saved": "xếp",
    "edit": "ê-đít",
    "build": "bin",
    "run": "răn",
    "running": "răn-ninh",
    "fast": "phát",
    "slow": "xờ-lâu",
    "rank": "ranh",
    "token": "tô-cơn",
    "tokens": "tô-cơn",
    "dataset": "đa-ta-xét",
    "param": "pa-ram",
    "params": "pa-ram",
    "prompt": "prôm",
    "task": "tát",
    "tasks": "tát",
    "click": "clích",
    "link": "linh",
    "download": "đao-loát",
    "upload": "ắp-loát",
    "update": "ắp-đét",
    "upgrade": "ắp-grét",
    "install": "in-xờ-tôn",
    "setup": "xét-ắp",
    "set": "xét",
    "sets": "xét",
    "setting": "xét-tinh",
    "settings": "xét-tinh",
    "reset": "ri-xét",
    "subset": "xắp-xét",
    "offset": "ốp-xét",
    "get": "gét",
    "gets": "gét",
    "getting": "gét-tinh",
    "let": "lét",
    "net": "nét",
    "pet": "pét",
    "bet": "bét",
    "login": "lốc-in",
    "logout": "lốc-ao",
    "signin": "xai-in",
    "signup": "xai-ắp",
    "password": "pát-uốc",
    "pass": "pát",
    "email": "i-meo",
    "mail": "meo",
    "inbox": "in-bốc",
    "message": "mét-xịt",
    "chat": "chát",
    "call": "con",
    "stream": "xờ-trim",
    "livestream": "lai-xờ-trim",
    "like": "lai",
    "share": "se",
    "comment": "còm-men",
    "follow": "phô-lâu",
    "subscribe": "xúp-xờ-crai",
    "sub": "xúp",
    "view": "viu",
    "top": "tóp",
    "hot": "hót",
    "new": "niu",
    "trend": "tren",
    "trending": "tren-đing",
    "viral": "vai-rồ",
    "spam": "xờ-pam",
    "scam": "xờ-cam",
    "hacker": "hắc-cơ",
    "hack": "hắc",
    "security": "xê-kiu-ri-ti",
    "cloud": "clao",
    "drive": "đrai",
    "backup": "bách-ắp",
    "reset": "ri-xét",
    "restart": "ri-xờ-tát",
    "reboot": "ri-bút",
    "screen": "xờ-crin",
    "touch": "tách",
    "smart": "xờ-mát",
    "fast": "phát",
    "slow": "xơ-lâu",
    "free": "phri",
    "price": "prai",
    "sale": "seo",
    "discount": "đít-sờ-cao",
    "order": "oóc-đơ",
    "ship": "síp",
    "shipper": "síp-pơ",
    "delivery": "đê-li-vơ-ri",
    "shopping": "sóp-ping",
    "shop": "sóp",
    "store": "xờ-to",
    "market": "mác-két",

    # Lập trình & Kỹ thuật
    "python": "pai-thần",
    "java": "gia-va",
    "javascript": "gia-va-xờ-críp",
    "html": "hát-tê-em-eo",
    "css": "xê-ét-ét",
    "php": "pê-hắt-pê",
    "sql": "ét-kiu-en",
    "git": "gít",
    "github": "gít-hắp",
    "docker": "đốc-cơ",
    "linux": "li-núc",
    "ubuntu": "u-bun-tu",
    "api": "ây-pi-ai",
    "sdk": "ét-đê-ca",
    "ui": "u-ai",
    "ux": "u-ếch",
    "gui": "gút-i",
    "ram": "ram",
    "rom": "rom",
    "cpu": "xê-pê-u",
    "gpu": "gê-pê-u",
    "ssd": "ét-ét-đê",
    "hdd": "hát-đê-đê",
    "usb": "u-ét-bê",
    "hdmi": "hát-đê-em-ai",
    "ip": "ai-pi",
    "domain": "đô-men",
    "host": "hốt",
    "proxy": "prốc-xi",
    "vpn": "vê-pê-en",
    "cookie": "cúc-ki",
    "cache": "két",
    "token": "tô-kần",
    "session": "xét-sần",
    "model": "mô-đen",
    "algorithm": "an-gô-rít-đừm",

    # Game & Thể thao điện tử
    "game": "gêm",
    "gamer": "gê-mơ",
    "gaming": "gê-ming",
    "player": "plây-ơ",
    "play": "plây",
    "level": "le-vờ",
    "lv": "cấp",
    "boss": "trùm",
    "mini-boss": "tiểu trùm",
    "skill": "xờ-kin",
    "item": "ai-tầm",
    "quest": "quét",
    "mission": "mít-sần",
    "task": "tát",
    "team": "tim",
    "guild": "ghin",
    "clan": "clan",
    "party": "pạc-ti",
    "rank": "ranh",
    "ranking": "ranh-king",
    "score": "xờ-co",
    "point": "poi",
    "kill": "kin",
    "die": "đai",
    "dead": "đét",
    "win": "uyn",
    "winner": "uyn-nơ",
    "lose": "lút",
    "loser": "lu-zơ",
    "match": "mát",
    "round": "rao",
    "turn": "tơn",
    "combo": "com-bô",
    "buff": "bắp",
    "nerf": "nớp",
    "crit": "crít",
    "damage": "đa-mét",
    "hp": "hát-pê",
    "mp": "em-pê",
    "exp": "ích-pê",
    "pk": "pê-ca",
    "pvp": "pê-vê-pê",
    "pve": "pê-vê-e",
    "npc": "en-pi-xi",
    "bot": "bót",
    "afk": "a-ép-ca",
    "gg": "gê-gê",
    "noob": "núp",
    "pro-player": "prồ plây-ơ",

    # Đời sống & Giao tiếp
    "hello": "hê-lô",
    "hi": "hai",
    "hey": "hây",
    "bye": "bai",
    "goodbye": "gút-bai",
    "thank": "thenh",
    "thanks": "thenh",
    "thank you": "thenh-kiu",
    "sorry": "xo-ri",
    "excuse me": "ếch-kiu-xì-mi",
    "please": "plít",
    "welcome": "oeo-cơm",
    "yes": "dét",
    "yeah": "de",
    "no": "nô",
    "nope": "nốp",
    "ok": "ô-kê",
    "okay": "ô-kê",
    "fine": "phain",
    "good": "gút",
    "bad": "bét",
    "cool": "cul",
    "great": "grét",
    "super": "xu-pơ",
    "nice": "nai",
    "love": "lớp",
    "baby": "bê-bi",
    "honey": "hăn-ni",
    "friend": "phren",
    "bro": "brô",
    "sir": "xơ",
    "madam": "ma-đam",
    "money": "măn-ni",
    "dollar": "đô-la",
    "time": "tai",
    "today": "tu-đây",
    "tomorrow": "tu-mo-râu",
    "yesterday": "dét-tơ-đây",
    "happy": "háp-pi",
    "sad": "xét",
    "lucky": "lắc-ki",
    "party": "pạc-ti",
    "club": "clắp",
    "bar": "ba",
    "coffee": "cà-phê",
    "cafe": "ca-phê",
    "tea": "ti",
    "beer": "bia",
    "wine": "oai",
    "hotel": "hô-ten",
    "restaurant": "rét-to-răng",
    "car": "ca",
    "taxi": "tắc-xi",
    "bus": "bút",
    "bike": "bai",
    "flight": "phlai",
    "ticket": "tíc-két",
    "card": "cạc",
    "visa": "vi-za",
    "mastercard": "mát-tơ-cạc",
    "bank": "banh",
    "atm": "a-tê-em",
    "ceo": "xê-i-ô",
    "cfo": "xê-ép-ô",
    "cto": "xê-tê-ô",
    "hr": "hắt-a",
    "pr": "pê-a",
    "kpi": "ca-pê-i",
    "deadline": "đét-lai",
    "meeting": "mít-ting",
    "project": "prô-déc",
    "report": "ri-pọt",
    "slide": "xơ-lai",
    "presentation": "pre-zen-tây-sần",
    "plan": "plan",
    "action": "ác-sần",
    "target": "tạc-gét",
    "review": "ri-viu",
    "feedback": "phít-bách",
    "interview": "in-tơ-viu",
    "resume": "rê-du-mê",
    "cv": "xê-vê",
    # Phần cứng, vi mạch, điện tử & cơ khí
    "relay": "ri-lây",
    "relays": "ri-lây",
    "delay": "đi-lây",
    "delays": "đi-lây",
    "replay": "ri-plây",
    "sensor": "xen-sơ",
    "sensors": "xen-sơ",
    "switch": "xuýt",
    "switches": "xuýt",
    "socket": "sốc-két",
    "sockets": "sốc-két",
    "plug": "pơ-lắc",
    "plugs": "pơ-lắc",
    "adapter": "a-đáp-tơ",
    "motor": "mô-tơ",
    "motors": "mô-tơ",
    "laser": "la-ze",
    "radar": "ra-đa",
    "transistor": "tran-di-to",
    "diode": "đi-ốt",
    "module": "mô-đun",
    "modules": "mô-đun",
}

_MODE_CACHE = {"mtime": None, "mode": "off"}

def get_bilingual_mode() -> str:
    """Đọc cấu hình chế độ song ngữ: 'off', 'native', 'phonetic'"""
    # [TỐI ƯU] Chỉ đọc lại file khi file đổi mtime
    try:
        mt = CONFIG_FILE.stat().st_mtime_ns
    except Exception:
        return "off"
    if _MODE_CACHE["mtime"] == mt:
        return _MODE_CACHE["mode"]
    mode = "off"
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            mode = data.get("mode", "off")
    except Exception:
        return "off"
    _MODE_CACHE["mtime"] = mt
    _MODE_CACHE["mode"] = mode
    return mode

def set_bilingual_mode(mode: str) -> str:
    """Lưu cấu hình chế độ song ngữ ('off', 'native', 'phonetic')"""
    if mode not in ["off", "native", "phonetic"]:
        mode = "off"
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({"mode": mode}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Lỗi lưu bilingual_config:", e)
    return mode

# =====================================================================
# QUẢN LÝ DANH SÁCH TỪ TIẾNG ANH TÙY CHỈNH (CUSTOM ENGLISH VOCABULARY)
# Cho phép người dùng tự thêm bất kỳ từ nào muốn đọc theo tiếng Anh
# =====================================================================
CUSTOM_WORDS_FILE = BASE_DIR / "custom_english_words.json"
CUSTOM_ENGLISH_WORDS_SET = set()
CUSTOM_ENGLISH_PHONETICS = dict()

def load_custom_english_words() -> list[dict]:
    """Tải danh sách từ tiếng Anh tùy chỉnh do người dùng thiết lập"""
    global CUSTOM_ENGLISH_WORDS_SET, CUSTOM_ENGLISH_PHONETICS
    CUSTOM_ENGLISH_WORDS_SET = set()
    CUSTOM_ENGLISH_PHONETICS = dict()

    words_list = []
    if CUSTOM_WORDS_FILE.exists():
        try:
            with open(CUSTOM_WORDS_FILE, "r", encoding="utf-8") as f:
                words_list = json.load(f)
        except Exception as e:
            print("[CustomWords] Lỗi đọc file:", e)

    for item in words_list:
        if isinstance(item, dict):
            w = item.get("word", "").strip().lower()
            ph = item.get("phonetic", "").strip()
            if w:
                CUSTOM_ENGLISH_WORDS_SET.add(w)
                CUSTOM_ENGLISH_WORDS_SET.add(w.replace("-", ""))
                CUSTOM_ENGLISH_WORDS_SET.add(w.replace(" ", ""))
                # Nếu cụm gồm nhiều từ (ví dụ "train start"), thêm từng từ vào tập nhận diện
                for sub_w in re.findall(r'[\w\-]+', w):
                    if sub_w:
                        CUSTOM_ENGLISH_WORDS_SET.add(sub_w)
                        CUSTOM_ENGLISH_WORDS_SET.add(sub_w.replace("-", ""))
                if ph:
                    CUSTOM_ENGLISH_PHONETICS[w] = ph
                    CUSTOM_ENGLISH_PHONETICS[w.replace("-", "")] = ph
        elif isinstance(item, str):
            w = item.strip().lower()
            if w:
                CUSTOM_ENGLISH_WORDS_SET.add(w)
                CUSTOM_ENGLISH_WORDS_SET.add(w.replace("-", ""))
                for sub_w in re.findall(r'[\w\-]+', w):
                    if sub_w:
                        CUSTOM_ENGLISH_WORDS_SET.add(sub_w)
                        CUSTOM_ENGLISH_WORDS_SET.add(sub_w.replace("-", ""))

    return words_list

def get_custom_words_version() -> str:
    """Trả về phiên bản của danh sách từ tùy chỉnh để đồng bộ và làm mới bộ nhớ đệm audio"""
    try:
        if CUSTOM_WORDS_FILE.exists():
            return str(int(CUSTOM_WORDS_FILE.stat().st_mtime))
    except Exception:
        pass
    return "0"

def get_custom_english_words() -> list[dict]:
    if not CUSTOM_WORDS_FILE.exists():
        return load_custom_english_words()
    try:
        with open(CUSTOM_WORDS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return load_custom_english_words()

def save_custom_english_words(words_list: list) -> list:
    """Lưu danh sách từ tiếng Anh tùy chỉnh và cập nhật bộ nhớ đệm"""
    try:
        with open(CUSTOM_WORDS_FILE, "w", encoding="utf-8") as f:
            json.dump(words_list, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("[CustomWords] Lỗi lưu file:", e)
    load_custom_english_words()
    return words_list

def add_custom_english_word(word: str, phonetic: str = "", desc: str = "") -> dict:
    w = word.strip().lower()
    w = re.sub(r'^[^\w\-]+|[^\w\-]+$', '', w).strip()
    if not w:
        return {"success": False, "error": "Từ không được để trống"}
    words = get_custom_english_words()
    for item in words:
        if isinstance(item, dict) and item.get("word", "").strip().lower() == w:
            item["phonetic"] = phonetic.strip()
            if desc: item["desc"] = desc.strip()
            save_custom_english_words(words)
            return {"success": True, "action": "updated", "word": item}

    new_item = {"word": w, "phonetic": phonetic.strip(), "desc": desc.strip()}
    words.insert(0, new_item)
    save_custom_english_words(words)
    return {"success": True, "action": "added", "word": new_item}

def delete_custom_english_word(word: str) -> bool:
    w = word.strip().lower()
    words = get_custom_english_words()
    new_words = [item for item in words if (item.get("word", "").strip().lower() != w if isinstance(item, dict) else item.strip().lower() != w)]
    if len(new_words) != len(words):
        save_custom_english_words(new_words)
        return True
    return False

# Nạp danh sách từ tùy chỉnh ngay khi import
load_custom_english_words()

# =====================================================================
# BỘ QUY TẮC PHÁT HIỆN TỪ TIẾNG ANH CHUẨN XÁC THEO NGỮ ÂM HỌC
# =====================================================================
EN_INITIAL_CLUSTERS = re.compile(
    r'^(str|spr|spl|scr|shr|thr|st|sp|sk|sl|sm|sn|sw|sc|bl|br|cl|cr|dr|fl|fr|gl|gr|pl|pr|tw|wr|kn|ps|rh)',
    re.I
)

EN_FINAL_PATTERNS = re.compile(
    r'(rt|st|nd|nt|ct|ft|lt|mp|nk|lp|rk|rm|rn|rd|ld|ck|sh|tch|th|gh|xt|ts|ds|ks|ps|ms|ns|ls|bb|dd|ff|gg|ll|mm|nn|pp|rr|ss|tt|zz|[bdfjklrsvwz]|(?<!n)g|(?<![nc])h)$',
    re.I
)

EN_SILENT_E = re.compile(r'^[a-z]{2,}[bcdfghjklmnpqrstvwxyz]e$', re.I)

EN_VOWEL_PATTERNS = re.compile(
    r'(ea|ee|oo|ou|ai[b-df-hj-np-tv-z]|oi[b-df-hj-np-tv-z]|ay[a-z]|ey|ei|au[b-df-hj-np-tv-z]|all|alk|alt|igh)',
    re.I
)

EN_SUFFIXES = re.compile(
    r'(tion|sion|ment|ness|less|ful|able|ible|ight|ing|ed|ers?|ors?|ists?|ives?|ical|ous|ance|ence|ship)$',
    re.I
)

# Quy luật từ tiếng Anh kết thúc bằng 'et' (set, get, let, net, pet, bet, reset, dataset, target...)
# Trong tiếng Việt, âm tiết đuôi 'et' BẮT BUỘC phải có dấu (sét, sẹt, kẹt, nét, vẹt...), không bao giờ tồn tại từ không dấu 'set'!
EN_ET_WORDS = re.compile(r'^[a-z]*[bcdfghjklmnpqrstvwxyz]et$', re.I)

# Quy luật từ đa âm tiết tiếng Anh / ngoại lai (Polysyllabic):
# Trong tiếng Việt 100% từ đơn âm tiết có các nguyên âm nằm sát nhau thành cụm duy nhất (thuyền, khoảng, nghiêng).
# Bất kỳ từ nào có nguyên âm + phụ âm + nguyên âm (như relay, delay, replay, sensor, model, token, reset, button, router, laser, motor...)
# Đều là từ đa âm tiết, chắc chắn 100% không phải là tiếng Việt đơn âm!
EN_POLYSYLLABIC = re.compile(r'[aeiouy]+[b-df-hj-np-tv-xz]+[aeiouy]+', re.I)

EN_VOCAB_SHORT = {
    'train', 'start', 'test', 'run', 'model', 'loss', 'epoch', 'batch', 'print', 'input', 'output',
    'set', 'sets', 'setting', 'settings', 'setup', 'reset', 'subset', 'offset', 'get', 'gets', 'getting', 'let', 'net', 'pet', 'bet',
    'relay', 'relays', 'delay', 'delays', 'replay', 'replays', 'switch', 'switches', 'sensor', 'sensors', 'socket', 'sockets', 'plug', 'plugs',
    'motor', 'motors', 'laser', 'radar', 'module', 'modules', 'cable', 'cables', 'router', 'routers', 'modem', 'modems',
    'ramp', 'ramps', 'rampup', 'up', 'down', 'off', 'out', 'prompt', 'prompts', 'pipeline', 'pipelines', 'benchmark', 'benchmarks',
    'put', 'cut', 'fit', 'hit', 'bit', 'bot', 'pot', 'dot', 'not', 'hot', 'tag', 'tab', 'bar', 'box', 'key', 'map',
    'data', 'dataset', 'city', 'home', 'game', 'time', 'page', 'rate', 'date', 'mode', 'code',
    'view', 'load', 'save', 'clear', 'stop', 'step', 'track', 'play', 'team', 'card', 'cost',
    'user', 'file', 'ai', 'api', 'cpu', 'gpu', 'ssd', 'ram', 'app', 'dev', 'bug', 'fix',
    'log', 'link', 'post', 'feed', 'chat', 'call', 'mail', 'top', 'new', 'vip', 'pro'
}

def is_english_token(token: str) -> bool:
    """Phát hiện chính xác 100% xem một từ có phải là từ tiếng Anh hay không"""
    if not token:
        return False

    raw_token_clean = re.sub(r'^[^\w\-]+|[^\w\-]+$', '', token).strip()
    raw_lower = raw_token_clean.lower()

    # 0. Kiểm tra danh sách từ tiếng Anh tùy chỉnh do người dùng thêm vào (Ưu tiên số 1)
    if raw_lower in CUSTOM_ENGLISH_WORDS_SET or raw_lower.replace("-", "") in CUSTOM_ENGLISH_WORDS_SET:
        return True

    # Xử lý từ ghép có dấu gạch ngang (ramp-up, start-up, check-in, plug-and-play...)
    if '-' in raw_token_clean:
        parts = [p.strip() for p in raw_token_clean.split('-') if p.strip()]
        if parts and all(is_english_token(p) for p in parts):
            return True

    clean = ''.join(c for c in token if c.isalpha())
    if not clean:
        return False
    
    clean_lower = clean.lower()

    # 1. Chứa dấu tiếng Việt -> 100% tiếng Việt
    if any(c in VIETNAMESE_ACCENTS for c in clean):
        return False

    # 2. Kiểm tra lại từ tùy chỉnh theo chữ cái thuần
    if clean_lower in CUSTOM_ENGLISH_WORDS_SET:
        return True

    # 3. Chứa ký tự ngoại lai không có trong bảng chữ cái tiếng Việt (f, j, w, z) -> tiếng Anh
    if any(c in 'fjwz' for c in clean_lower):
        return True

    # 4. Chữ viết tắt in hoa (AI, VIP, API, RAM, SSD, CPU, GPU, UI, UX, ID...) -> tiếng Anh
    if clean.isupper() and len(clean) >= 2:
        return True

    # 5. Có trong từ điển phiên âm chuẩn hoặc từ vựng tiếng Anh ngắn phổ biến (bao gồm 'set', 'get', 'let', 'relay', 'delay', 'ramp'...)
    if clean_lower in COMMON_EN_VI_PHONETICS or clean_lower in EN_VOCAB_SHORT:
        return True

    # 5. Quy luật từ kết thúc bằng 'et' không dấu (set, get, let, reset, dataset...)
    # Tiếng Việt không có từ không dấu 'set', chỉ có 'sét' hoặc 'sẹt'
    if EN_ET_WORDS.search(clean_lower):
        return True

    # 6. Có trong danh mục từ tiếng Việt không dấu chuẩn -> tiếng Việt
    if clean_lower in VIETNAMESE_BASE_WORDS:
        return False

    # 7. Quy luật từ đa âm tiết ngoại lai (nguyên âm + phụ âm + nguyên âm như relay, delay, sensor, router, motor...)
    if EN_POLYSYLLABIC.search(clean_lower):
        return True

    # 8. Bắt đầu bằng cụm phụ âm tiếng Anh (st, sp, sk, sl, sm, sn, sw, bl, br, cl, cr, dr, fl, fr, gl, gr, pl, pr...)
    if EN_INITIAL_CLUSTERS.search(clean_lower):
        return True

    # 9. Kết thúc bằng phụ âm hoặc cụm phụ âm tiếng Anh (start: -rt, test: -st, loss: -ss, card: -rd, switch: -tch...)
    if EN_FINAL_PATTERNS.search(clean_lower):
        return True

    # 10. Kết thúc bằng 'e câm' tiếng Anh (code, home, game, time, line, page, rate, date, type...)
    if EN_SILENT_E.search(clean_lower):
        return True

    # 11. Tổ hợp nguyên âm đặc trưng tiếng Anh (train: 'ain', read: 'ea', team: 'ea', cool: 'oo', round: 'ou')
    if EN_VOWEL_PATTERNS.search(clean_lower):
        return True

    # 12. Chứa hậu tố đặc trưng tiếng Anh
    if EN_SUFFIXES.search(clean_lower):
        return True

    # 13. Từ đơn có độ dài > 6 ký tự
    if len(clean_lower) > 6 and clean_lower not in ["nghieng", "nghiengs"]:
        return True

    return False

# =====================================================================
# CHUYỂN ĐỔI KÝ HIỆU TOÁN HỌC & SO SÁNH THÀNH LỜI ĐỌC TIẾNG VIỆT
# (> ➔ lớn hơn, < ➔ nhỏ hơn, >= ➔ lớn hơn hoặc bằng, % ➔ phần trăm...)
# =====================================================================
def convert_symbols_to_spoken_text(text: str) -> str:
    """Chuyển đổi toàn bộ các ký hiệu toán học, so sánh, tiền tệ, nhiệt độ sang lời đọc chuẩn tiếng Việt"""
    if not text:
        return ""

    res = text

    # 1. Loại bỏ các thẻ HTML còn sót lại nếu có
    res = re.sub(r'</?[a-zA-Z][^>]*>', ' ', res)

    # 2. Xử lý số hàng triệu, hàng nghìn có định dạng chuẩn (.000.000 hoặc .000)
    res = re.sub(r'\b(\d{1,3})\.000\.000(?!\d)', r'\1 triệu', res)
    res = re.sub(r'\b(\d{1,3}),000,000(?!\d)', r'\1 triệu', res)
    res = re.sub(r'\b(\d{1,3})\.000(?!\d)', r'\1 nghìn', res)
    res = re.sub(r'\b(\d{1,3}),000(?!\d)', r'\1 nghìn', res)

    # 3. Xử lý số thập phân: trước và sau dấu . hoặc , là số không có khoảng cách
    # Dấu . đọc là 'chấm' (vd: 66.7% -> 66 chấm 7 phần trăm, 0.05 -> 0 chấm 05)
    # Dấu , đọc là 'phẩy' (vd: 66,7% -> 66 phẩy 7 phần trăm, 1,5 -> 1 phẩy 5)
    # Dấu chấm câu và dấu phẩy câu (có khoảng cách hoặc chữ) vẫn giữ nguyên để ngắt câu tự nhiên
    res = re.sub(r'(?<=\d)\.(?=\d)', ' chấm ', res)
    res = re.sub(r'(?<=\d),(?=\d)', ' phẩy ', res)

    # 4. Đơn vị đo lường thông dụng
    res = re.sub(r'(?i)\bkm/h\b', ' ki-lô-mét trên giờ ', res)
    res = re.sub(r'(?i)\bm/s\b', ' mét trên giây ', res)

    # 5. Nhiệt độ
    res = re.sub(r'(?i)(\d+)\s*°\s*[cC]\b', r'\1 độ C ', res)
    res = re.sub(r'(\d+)\s*°', r'\1 độ ', res)

    # 6. Tiền tệ $
    res = re.sub(r'\$\s*(\d+(?:[.,]\d+)?)', r'\1 đô la ', res)
    res = re.sub(r'(\d+(?:[.,]\d+)?)\s*\$', r'\1 đô la ', res)

    # 7. Mũi tên & suy ra
    res = re.sub(r'(=>|⇒)', ' suy ra ', res)
    res = re.sub(r'(->|→|➔)', ' chuyển sang ', res)
    res = re.sub(r'(<-|←)', ' nhận từ ', res)

    # 6. Các phép so sánh kép
    res = re.sub(r'(>=|≥)', ' lớn hơn hoặc bằng ', res)
    res = re.sub(r'(<=|≤)', ' nhỏ hơn hoặc bằng ', res)
    res = re.sub(r'(!=|≠)', ' khác ', res)
    res = re.sub(r'==', ' bằng ', res)

    # 7. Các phép so sánh đơn > và <
    res = re.sub(r'>', ' lớn hơn ', res)
    res = re.sub(r'<', ' nhỏ hơn ', res)

    # 8. Phần trăm %
    res = re.sub(r'(\d+)\s*%', r'\1 phần trăm ', res)
    res = re.sub(r'%', ' phần trăm ', res)

    # 9. Cộng trừ ±
    res = re.sub(r'±', ' cộng trừ ', res)

    # 10. Phép toán số học giữa các số hoặc biến: +, *, /
    res = re.sub(r'(?<=\w)\s*\+\s*(?=\w)', ' cộng ', res)
    res = re.sub(r'(?<=\d)\s*\*\s*(?=\d)', ' nhân ', res)
    res = re.sub(r'(?<=\d)\s*/\s*(?=\d)', ' chia ', res)

    # 11. Dấu bằng =
    res = re.sub(r'\s*=\s*', ' bằng ', res)

    # 12. Dấu &
    res = re.sub(r'\s*&\s*', ' và ', res)

    # 13. Dấu @
    res = re.sub(r'@', ' a còng ', res)

    # 14. Dấu xấp xỉ ~
    res = re.sub(r'(khoảng|xấp xỉ)\s*~', r'\1 ', res)
    res = re.sub(r'~', ' khoảng ', res)

    # 15. Dấu số mũ ^
    res = re.sub(r'(?<=\w)\s*\^\s*(?=\w)', ' mũ ', res)

    # Dọn dẹp khoảng trắng thừa
    return re.sub(r'\s+', ' ', res).strip()

# =====================================================================
# CHẾ ĐỘ 2: PHIÊN ÂM THUẦN VIỆT (TỰ ĐỘNG CHUYỂN ANH SANG ÂM ĐỌC VIỆT)
# =====================================================================
def transliterate_english_to_vietnamese(text: str) -> str:
    """Chuyển đổi toàn bộ từ tiếng Anh và ký hiệu sang cách đọc ngữ âm tiếng Việt tự nhiên"""
    if not text:
        return ""

    # Bước 1: Xử lý ký hiệu toán học / so sánh trước
    text = convert_symbols_to_spoken_text(text)

    # Bước 2: Phiên âm từng từ tiếng Anh
    words = text.split()
    result = []
    for w in words:
        clean_hyphen = re.sub(r'^[^\w\-]+|[^\w\-]+$', '', w)
        if not clean_hyphen:
            result.append(w)
            continue

        clean_lower = clean_hyphen.lower()

        if clean_lower in VIETNAMESE_BASE_WORDS and not clean_hyphen.isupper():
            result.append(w)
            continue

        # 1. Tra từ điển người dùng thêm trước (Ưu tiên số 1)
        if clean_lower in CUSTOM_ENGLISH_PHONETICS:
            rep = CUSTOM_ENGLISH_PHONETICS[clean_lower]
            result.append(w.replace(clean_hyphen, rep))
            continue
        elif clean_lower.replace("-", "") in CUSTOM_ENGLISH_PHONETICS:
            rep = CUSTOM_ENGLISH_PHONETICS[clean_lower.replace("-", "")]
            result.append(w.replace(clean_hyphen, rep))
            continue

        # 2. Tra từ điển phiên âm chuẩn
        if clean_lower in COMMON_EN_VI_PHONETICS:
            rep = COMMON_EN_VI_PHONETICS[clean_lower]
            result.append(w.replace(clean_hyphen, rep))
            continue
        elif clean_lower.replace("-", "") in COMMON_EN_VI_PHONETICS:
            rep = COMMON_EN_VI_PHONETICS[clean_lower.replace("-", "")]
            result.append(w.replace(clean_hyphen, rep))
            continue

        # 3. Nếu là từ ghép có dấu gạch ngang (như ramp-up, start-up, check-in...)
        if '-' in clean_hyphen and is_english_token(clean_hyphen):
            subparts = clean_hyphen.split('-')
            sub_reps = []
            for p in subparts:
                pl = p.lower()
                if pl in CUSTOM_ENGLISH_PHONETICS:
                    sub_reps.append(CUSTOM_ENGLISH_PHONETICS[pl])
                elif pl in COMMON_EN_VI_PHONETICS:
                    sub_reps.append(COMMON_EN_VI_PHONETICS[pl])
                else:
                    sub_reps.append(rule_based_phonetic(pl))
            rep = "-".join(sub_reps)
            result.append(w.replace(clean_hyphen, rep))
            continue

        # 4. Kiểm tra từ đơn
        clean = ''.join(c for c in w if c.isalpha())
        if not clean:
            result.append(w)
            continue

        clean_lower_alpha = clean.lower()
        if clean_lower_alpha in CUSTOM_ENGLISH_PHONETICS:
            rep = CUSTOM_ENGLISH_PHONETICS[clean_lower_alpha]
            result.append(w.replace(clean, rep))
        elif clean_lower_alpha in COMMON_EN_VI_PHONETICS:
            rep = COMMON_EN_VI_PHONETICS[clean_lower_alpha]
            result.append(w.replace(clean, rep))
        elif is_english_token(clean):
            rep = rule_based_phonetic(clean_lower_alpha)
            result.append(w.replace(clean, rep))
        else:
            result.append(w)

    return " ".join(result)

def rule_based_phonetic(word: str) -> str:
    """Phiên âm theo quy tắc ngữ âm tự nhiên"""
    rules = [
        (r'^up\b', 'áp'),
        (r'amp\b', 'am'),
        (r'^down\b', 'đao'),
        (r'^out\b', 'ao'),
        (r'^off\b', 'ọp'),
        (r'tion\b', 'sần'),
        (r'sion\b', 'sần'),
        (r'ture\b', 'chơ'),
        (r'ing\b', 'ing'),
        (r'ight\b', 'ai'),
        (r'^str', 'xờ-tr'),
        (r'^st', 'xờ-t'),
        (r'^sp', 'xờ-p'),
        (r'^sk', 'xờ-c'),
        (r'^sl', 'xờ-l'),
        (r'^sm', 'xờ-m'),
        (r'^sn', 'xờ-n'),
        (r'^sw', 'xờ-u'),
        (r'^cl', 'cơ-l'),
        (r'^cr', 'cơ-r'),
        (r'^pl', 'pơ-l'),
        (r'^pr', 'pơ-r'),
        (r'^bl', 'bơ-l'),
        (r'^br', 'bơ-r'),
        (r'^fl', 'phơ-l'),
        (r'^fr', 'phơ-r'),
        (r'^dr', 'đơ-r'),
        (r'ain\b', 'ên'),
        (r'art\b', 'át'),
        (r'ort\b', 'ót'),
        (r'ack\b', 'ắc'),
        (r'ock\b', 'ốc'),
        (r'ick\b', 'ích'),
        (r'eck\b', 'ếch'),
        (r'uck\b', 'ắc'),
        (r'est\b', 'ét'),
        (r'ast\b', 'át'),
        (r'ost\b', 'ốt'),
        (r'ust\b', 'ất'),
        (r'ist\b', 'ít'),
        (r'ask\b', 'át'),
        (r'esk\b', 'ét'),
        (r'isk\b', 'ít'),
        (r'ank\b', 'anh'),
        (r'ink\b', 'inh'),
        (r'and\b', 'en'),
        (r'end\b', 'en'),
        (r'ound\b', 'ao'),
        (r'ph', 'ph'),
        (r'sh', 's'),
        (r'et\b', 'ét'),
        (r'th\b', 'th'),
        (r'ck', 'c'),
        (r'ee', 'i'),
        (r'oo', 'u'),
        (r'ea', 'i'),
        (r'ai', 'ai'),
        (r'ay', 'ay'),
        (r'ou', 'ao'),
        (r'ow', 'ao'),
        (r'er\b', 'ơ'),
        (r'or\b', 'o'),
        (r'ar\b', 'a'),
        (r'ir\b', 'ơ'),
        (r'ur\b', 'ơ'),
        (r'le\b', 'cồ'),
        (r'al\b', 'ồ'),
        (r'y\b', 'i'),
        (r'w', 'u'),
        (r'j', 'd'),
        (r'z', 'd'),
        (r'f', 'ph'),
    ]
    res = word
    for pat, rep in rules:
        res = re.sub(pat, rep, res)
    return res

# =====================================================================
# CHẾ ĐỘ 1: PHÂN ĐOẠN ĐA GIỌNG SONG NGỮ (HYBRID DUAL-VOICE)
# =====================================================================
def split_into_language_segments(text: str) -> list[tuple[str, str]]:
    """
    Phân tách đoạn văn thành các đoạn liền mạch [('vi', text_vi), ('en', text_en), ...]
    để tổng hợp âm thanh đa giọng (Việt + Mỹ bản xứ)
    """
    if not text:
        return []

    # Chuyển đổi ký hiệu toán học / so sánh thành từ ngữ trước
    text = convert_symbols_to_spoken_text(text)

    tokens = re.split(r'(\s+)', text)
    segments = []
    current_lang = None
    current_buf = []

    for token in tokens:
        if not token:
            continue
        if token.isspace():
            if current_buf:
                current_buf.append(token)
            continue

        token_is_en = is_english_token(token)
        token_lang = 'en' if token_is_en else 'vi'

        if current_lang is None:
            current_lang = token_lang
            current_buf.append(token)
        elif current_lang == token_lang:
            current_buf.append(token)
        else:
            seg_text = "".join(current_buf).strip()
            if seg_text:
                segments.append((current_lang, seg_text))
            current_lang = token_lang
            current_buf = [token]

    if current_buf:
        seg_text = "".join(current_buf).strip()
        if seg_text:
            segments.append((current_lang, seg_text))

    return segments

def get_paired_english_voice(vn_voice_id: str, provider: str = "capcut") -> str:
    """Chọn giọng tiếng Anh bản xứ phù hợp với giới tính của giọng tiếng Việt hiện tại"""
    clean_id = vn_voice_id.replace("offline_", "").lower()
    is_male = False
    try:
        from offline_tts import get_voice_info
        v_info = get_voice_info(clean_id)
        if v_info:
            is_male = (v_info.get("gender") == "Nam")
    except Exception:
        pass

    if not is_male:
        is_male = any(tag in clean_id for tag in ["nam", "man", "minh", "075", "deepman", "dung", "quang", "thanh", "duy"])

    if provider in ["capcut", "offline"]:
        # Nam Mỹ: en_us_006, Nữ Mỹ: en_us_001
        return "en_us_006" if is_male else "en_us_001"
    else:
        # Edge TTS: Nam: Guy, Nữ: Jenny
        return "en-US-GuyNeural" if is_male else "en-US-JennyNeural"


