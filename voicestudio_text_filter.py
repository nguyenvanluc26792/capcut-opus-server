# -*- coding: utf-8 -*-
"""
Bộ lọc chuẩn hóa & chống lớ tiếng cho VoiceStudio TTS.
Xử lý các nguyên nhân gây đọc lơ lớ / vấp nhịp ở truyện dịch/convert:
1. Chuẩn hóa Unicode NFC (gộp dấu thanh rời).
2. Hạ chữ viết hoa toàn bộ (ALL CAPS tiếng Việt) tránh AI đánh vần kiểu tiếng Anh.
3. Sửa lỗi viết hoa sai ngữ pháp giữa câu (vd: 'Tiễn Vô Dụng Lắc đầu nói' -> 'Tiễn Vô Dụng, lắc đầu nói').
4. Ngắt nhịp nhẹ giữa tên riêng dài và cụm hành động.
5. Chuyển ký hiệu, số đếm và từ tiếng Anh sang âm đọc thuần Việt qua bilingual_engine.
6. Chèn nhịp lấy hơi cho câu dài.
"""

import re
import unicodedata

try:
    import bilingual_engine as bilingual
except Exception:
    bilingual = None

VI_NUM_UNITS = ["không", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]

# Tập từ phổ thông tiếng Việt (động từ, phó từ, tính từ, liên từ, đại từ...)
# rất hay bị phần mềm convert viết hoa nhầm sau tên nhân vật hoặc giữa câu.
COMMON_LOWERCASE_AFTER_NAME = {
    # Động từ hành động / biểu cảm / lời nói
    "lắc", "gật", "cười", "khóc", "nói", "hỏi", "đáp", "quát", "hét", "gào",
    "thét", "thở", "nhìn", "liếc", "trừng", "híp", "cau", "nhíu", "khịt", "hừ",
    "nghĩ", "thầm", "bước", "đi", "chạy", "bay", "nhảy", "đứng", "ngồi", "nằm",
    "quỳ", "rút", "vung", "đánh", "chém", "đâm", "đấm", "đá", "chụp", "bắt",
    "nắm", "cầm", "giơ", "vươn", "nâng", "hạ", "thu", "mở", "đóng", "quay",
    "xoay", "ngẩng", "cúi", "vẫy", "chỉ", "lau", "xoa", "vỗ", "búng", "ném",
    "quăng", "kéo", "đẩy", "ôm", "cõng", "đỡ", "né", "tránh", "chặn", "phá",
    "giết", "trảm", "oanh", "hấp", "nuốt", "uống", "ăn", "ngủ", "tỉnh", "nghe",
    "thấy", "biết", "hiểu", "muốn", "cần", "phải", "nên", "chịu", "dám", "làm",
    "ra", "vào", "lên", "xuống", "sang", "qua", "lại", "về", "tới", "đến",
    # Phó từ / trạng từ / tính từ / liên từ
    "khẽ", "nhẹ", "vội", "liền", "chợt", "bỗng", "đột", "lập", "tức", "như",
    "cũng", "đều", "lại", "còn", "vẫn", "đã", "đang", "sẽ", "không", "chẳng",
    "chưa", "thế", "nhưng", "mà", "nếu", "tuy", "dù", "vì", "bởi", "cho",
    "khi", "lúc", "sau", "trước", "trong", "ngoài", "trên", "dưới", "giữa",
    "lạnh", "ấm", "run", "sợ", "kinh", "ngạc", "giận", "vui", "buồn", "mỉm",
    "nhếch", "ngơ", "sững", "im", "lặng", "thản", "nhiên", "nghiêm", "túc",
    "hắn", "nàng", "ngươi", "ta", "nó", "y", "mọi", "những", "các", "một",
    "bị", "được", "là", "có", "thật", "rất", "quá", "hơi", "vô", "cực",
}

# Các từ viết tắt tiếng Anh hợp lệ được giữ nguyên dạng IN HOA (để bilingual xử lý)
ENGLISH_ACRONYM_WHITELIST = {
    "AI", "VIP", "HP", "MP", "PK", "NPC", "GM", "XP", "EXP", "LV", "BOSS",
    "UI", "UX", "ID", "PC", "CPU", "GPU", "RAM", "SSD", "HDD", "USB",
    "WIFI", "OK", "TV", "MC", "PR", "CEO", "CT", "FPS", "RPG", "MMO",
}

VIETNAMESE_DIACRITICS_RE = re.compile(
    r"[àáảãạăắằẳẵặâấầẩẫậđèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵ"
    r"ÀÁẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬĐÈÉẺẼẸÊẾỀỂỄỆÌÍỈĨỊÒÓỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÙÚỦŨỤƯỨỪỬỮỰỲÝỶỸỴ]"
)

VOICESTUDIO_LOANWORDS_MAP = {
    r"\bgame\b": "gêm",
    r"\bgamer\b": "gê-mơ",
    r"\bboss\b": "bốt",
    r"\bapp\b": "áp",
    r"\bok\b|\bokay\b": "ô-kê",
    r"\bvip\b": "víp",
    r"\bmc\b": "em-xi",
    r"\bfan\b": "phen",
    r"\bteam\b": "tim",
    r"\btop\b": "tốp",
    r"\blevel\b": "cấp độ",
    r"\blv\b": "cấp",
    r"\bno\.(?=\s*\d)": "số ",
    r"\bstatus\b": "trạng thái",
    r"\blivestream\b": "lai-chim",
    r"\bstreamer\b": "xờ-tri-mơ",
    r"\byoutube\b": "du-túp",
    r"\btiktok\b": "tóp-tóp",
    r"\bfacebook\b": "phây-bút",
    r"\bzalo\b": "da-lô",
    r"\bgoogle\b": "gú-gồ",
    r"\bsystem\b": "hệ thống",
    r"\bhost\b": "hốt",
    r"\bmaster\b": "mác-xờ-tơ",
    r"\bnpc\b": "en-pi-xi",
    r"\bpro\b": "pờ-rô",
    r"\bnoob\b": "núp",
    r"\bguild\b": "bang hội",
    r"\bskill\b": "kỹ năng",
    r"\bitem\b": "vật phẩm",
    r"\bquest\b": "nhiệm vụ",
    r"\bbug\b": "bọ",
    r"\bserver\b": "máy chủ",
    r"\bonline\b": "trực tuyến",
    r"\boffline\b": "ngoại tuyến",
    r"\bauto\b": "tự động",
    r"\bhot\b": "hót",
    r"\bview\b": "lượt xem",
    r"\blike\b": "thích",
    r"\bcomment\b": "bình luận",
    r"\bshare\b": "chia sẻ",
    r"\bvideo\b": "vi-đê-ô",
    r"\baudio\b": "âm thanh",
    r"\bclip\b": "cờ-líp",
    r"\bchat\b": "chát",
    r"\bcheck\b": "kiểm tra",
    r"\btest\b": "thử nghiệm",
    r"\bspam\b": "xì-pam",
    r"\bhack\b": "hách",
    r"\bcheat\b": "chít",
    r"\bcombo\b": "com-bô",
    r"\bbuff\b": "búp",
    r"\bnerf\b": "nớp",
    r"\brank\b": "xếp hạng",
    r"\blogin\b": "đăng nhập",
    r"\blogout\b": "đăng xuất",
    r"\bpass\b|\bpassword\b": "mật khẩu",
    r"\bemail\b": "hòm thư",
    r"\blink\b": "đường dẫn",
    r"\bcode\b": "mã",
    r"\bdata\b": "dữ liệu",
    r"\bchip\b": "chíp",
    r"\bsim\b": "xim",
    r"\bpin\b": "pin",
    r"\bshow\b": "sô",
    r"\bstar\b": "ngôi sao",
    r"\bidol\b": "thần tượng",
    r"\bdebut\b": "ra mắt",
    r"\bcomeback\b": "trở lại",
    r"\bhit\b": "hít",
    r"\btrend\b": "xu hướng",
    r"\bdrama\b": "thị phi",
    r"\bpr\b": "quảng bá",
    r"\btrailer\b": "đoạn giới thiệu",
    r"\bspoil\b": "tiết lộ",
    r"\banti\b": "chống",
    r"\bchapter\b|\bchap\b": "chương",
    r"\bvol\b|\bvolume\b": "tập",
    r"\bhero\b": "anh hùng",
    r"\bvillain\b": "kẻ ác",
    r"\bmain\b": "nhân vật chính",
    r"\bplot\b": "cốt truyện",
    r"\bending\b": "kết thúc",
    r"\bjack\b": "Giắc",
    r"\balice\b": "A-lít",
    r"\btom\b": "Tôm",
    r"\bmike\b": "Mai-cơn",
    r"\bdavid\b": "Đa-vít",
    r"\bjohn\b": "Giôn",
    r"\bmary\b": "Me-ri",
    r"\bpeter\b": "Pi-tơ",
    r"\bharry\b": "Ha-ri",
    r"\bpotter\b": "Pót-tơ",
    r"\blucifer\b": "Lu-xi-phơ",
    r"\bsatan\b": "Xa-tăng",
    r"\bzeus\b": "Dớt",
    r"\bodin\b": "Ô-đin",
    r"\bthor\b": "Tho",
    r"\bloki\b": "Lô-ki",
    r"(?<=\d)\s*km/h\b": " ki-lô-mét trên giờ",
    r"(?<=\d)\s*m/s\b": " mét trên giây",
    r"(?<=\d)\s*km\b": " ki-lô-mét",
    r"(?<=\d)\s*m\b": " mét",
    r"(?<=\d)\s*cm\b": " xăng-ti-mét",
    r"(?<=\d)\s*mm\b": " mi-li-mét",
    r"(?<=\d)\s*kg\b": " ki-lô-gam",
    r"(?<=\d)\s*g\b": " gam",
    r"(?<=\d)\s*ml\b": " mi-li-lít",
    r"(?<=\d)\s*l\b": " lít",
    r"(?<=\d)\s*k\b": " nghìn",
    r"(?<=\d)\s*tr\b": " triệu",
    r"(?<=\d)\s*%\b": " phần trăm",
}


def int_to_vietnamese_words(n):
    if n < 0:
        return "âm " + int_to_vietnamese_words(-n)
    if n < 10:
        return VI_NUM_UNITS[n]
    if n < 20:
        if n == 10:
            return "mười"
        if n == 15:
            return "mười lăm"
        return "mười " + VI_NUM_UNITS[n % 10]
    if n < 100:
        ten = n // 10
        unit = n % 10
        ten_str = (
            "hai" if ten == 2 else "ba" if ten == 3 else "bốn" if ten == 4 else
            "năm" if ten == 5 else "sáu" if ten == 6 else "bảy" if ten == 7 else
            "tám" if ten == 8 else "chín"
        ) + " mươi"
        if unit == 0:
            return ten_str
        elif unit == 1:
            return ten_str + " mốt"
        elif unit == 4:
            return ten_str + " tư"
        elif unit == 5:
            return ten_str + " lăm"
        else:
            return ten_str + " " + VI_NUM_UNITS[unit]
    if n < 1000:
        hundred = n // 100
        rem = n % 100
        h_str = VI_NUM_UNITS[hundred] + " trăm"
        if rem == 0:
            return h_str
        elif rem < 10:
            return h_str + " lẻ " + VI_NUM_UNITS[rem]
        else:
            return h_str + " " + int_to_vietnamese_words(rem)
    if n < 1000000:
        thousand = n // 1000
        rem = n % 1000
        t_str = int_to_vietnamese_words(thousand) + " nghìn"
        if rem == 0:
            return t_str
        elif rem < 100:
            return (
                t_str + " không trăm lẻ " + VI_NUM_UNITS[rem]
                if rem < 10
                else t_str + " không trăm " + int_to_vietnamese_words(rem)
            )
        else:
            return t_str + " " + int_to_vietnamese_words(rem)
    if n < 1000000000:
        million = n // 1000000
        rem = n % 1000000
        m_str = int_to_vietnamese_words(million) + " triệu"
        if rem == 0:
            return m_str
        else:
            return m_str + " " + int_to_vietnamese_words(rem)
    return str(n)


def convert_digits_to_vietnamese_words(text):
    def replace_num(match):
        val_str = match.group(0)
        try:
            val = int(val_str)
            if 0 <= val <= 999999999:
                return int_to_vietnamese_words(val)
        except Exception:
            pass
        return val_str

    return re.sub(r"\b\d{1,9}\b", replace_num, text)


def normalize_all_caps_vietnamese(text):
    """Chuyển chuỗi tiếng Việt viết IN HOA TOÀN BỘ (vd: 'CHẾT ĐI') về chữ thường có kiểm soát."""
    tokens = re.split(r"(\s+)", text)
    out = []
    is_sentence_start = True
    for tok in tokens:
        if not tok or tok.isspace():
            out.append(tok)
            continue

        m = re.match(r"^([^\w]*)(.*?)([^\w]*)$", tok, flags=re.UNICODE)
        if not m:
            out.append(tok)
            continue
        lead, core, trail = m.groups()
        alpha_only = "".join(c for c in core if c.isalpha())

        if (
            len(alpha_only) >= 2
            and alpha_only.isupper()
            and alpha_only.upper() not in ENGLISH_ACRONYM_WHITELIST
            and (VIETNAMESE_DIACRITICS_RE.search(alpha_only) or len(alpha_only) >= 2)
        ):
            # Giữ nguyên viết tắt tiếng Anh ngắn nếu nằm trong bilingual hoặc không có dấu Việt & > 1 phụ âm liên tiếp kiểu acronym
            is_vi_word = bool(VIETNAMESE_DIACRITICS_RE.search(alpha_only))
            if not is_vi_word and len(alpha_only) <= 4 and not re.search(r"[AEIOUY]", alpha_only):
                fixed_core = core
            elif is_vi_word or alpha_only.lower() in COMMON_LOWERCASE_AFTER_NAME:
                lowered = core.lower()
                fixed_core = lowered[0].upper() + lowered[1:] if is_sentence_start else lowered
            else:
                fixed_core = core
            out.append(lead + fixed_core + trail)
        else:
            out.append(tok)

        if any(p in trail for p in (".", "!", "?", ":", "\n", "…")):
            is_sentence_start = True
        elif alpha_only:
            is_sentence_start = False

    return "".join(out)


def _extract_word_parts(token):
    m = re.match(r"^([^\w]*)(.*?)([^\w]*)$", token, flags=re.UNICODE)
    if not m:
        return "", token, ""
    return m.groups()


def _is_titlecase_word(core):
    return bool(core) and core[0].isupper() and any(c.islower() for c in core[1:])


def _is_lowercase_word(core):
    return bool(core) and core[0].islower()


def fix_mid_sentence_capitalization_and_names(text):
    """
    Sửa lỗi viết hoa sai giữa câu (vd: 'Tiễn Vô Dụng Lắc đầu nói' -> 'Tiễn Vô Dụng, lắc đầu nói')
    và ngắt phẩy nhẹ giữa tên riêng >= 2 từ và cụm động từ dài để AI không đọc dính chữ bị lớ.
    """
    words = text.split()
    if len(words) < 2:
        return text

    parsed = [_extract_word_parts(w) for w in words]
    sentence_starts = [False] * len(words)
    at_start = True
    for i, (lead, core, trail) in enumerate(parsed):
        sentence_starts[i] = at_start
        if any(p in trail for p in (".", "!", "?", ":", "\n", "…")):
            at_start = True
        elif core:
            at_start = False

    lowered_indices = set()
    for i, (lead, core, trail) in enumerate(parsed):
        if sentence_starts[i] or not _is_titlecase_word(core):
            continue
        if lead and any(p in lead for p in (".", "!", "?", ":")):
            continue

        core_l = core.lower()
        if core_l not in COMMON_LOWERCASE_AFTER_NAME:
            continue

        prev_is_lower = i > 0 and _is_lowercase_word(parsed[i - 1][1]) and not parsed[i - 1][2]
        next_is_lower = i + 1 < len(parsed) and _is_lowercase_word(parsed[i + 1][1])

        # Nếu đứng sau chữ thường hoặc đứng ngay trước chữ thường (vd: 'Lắc đầu') -> chắc chắn viết hoa nhầm
        if prev_is_lower or next_is_lower:
            parsed[i] = (lead, core_l, trail)
            lowered_indices.add(i)

    # Tách nhịp phẩy nhẹ giữa cụm tên riêng (>= 2 từ TitleCase) và cụm hành động (>= 2 từ thường)
    # Ví dụ: 'Tiễn Vô Dụng lắc đầu nói' -> 'Tiễn Vô Dụng, lắc đầu nói'
    result_words = []
    i = 0
    while i < len(parsed):
        lead, core, trail = parsed[i]
        word_str = lead + core + trail
        result_words.append(word_str)

        # Kiểm tra xem tại vị trí i có phải là kết thúc cụm tên riêng >= 2 từ không
        if (
            not trail
            and _is_titlecase_word(core)
            and i >= 1
            and not parsed[i - 1][2]
            and _is_titlecase_word(parsed[i - 1][1])
            and i + 2 < len(parsed)
        ):
            next_lead, next_core, next_trail = parsed[i + 1]
            next2_core = parsed[i + 2][1]
            if (
                not next_lead
                and _is_lowercase_word(next_core)
                and _is_lowercase_word(next2_core)
                and ((i + 1) in lowered_indices or next_core in COMMON_LOWERCASE_AFTER_NAME)
            ):
                result_words[-1] = word_str + ","

        i += 1

    return " ".join(result_words)


def insert_micro_pauses_for_long_sentences(text, max_words=18):
    clauses = re.split(r"([,;:\n])", text)
    processed_clauses = []
    conjunctions_pattern = re.compile(
        r"\s+\b(và|nhưng|mà|tuy nhiên|bởi vì|cho nên|do đó|thành ra|đột nhiên|bỗng nhiên|chợt|liền|lại|thì|nếu|dù cho|mặc dù)\b\s+",
        re.IGNORECASE,
    )
    for i in range(0, len(clauses), 2):
        part = clauses[i]
        words = part.split()
        if len(words) > max_words:
            new_part = conjunctions_pattern.sub(lambda m: ", " + m.group(1) + " ", part, count=2)
            processed_clauses.append(new_part)
        else:
            processed_clauses.append(part)
        if i + 1 < len(clauses):
            processed_clauses.append(clauses[i + 1])
    res = "".join(processed_clauses)
    return re.sub(r",\s*,", ",", res)


def normalize_text_for_voicestudio(text):
    if not text:
        return ""

    # 1. Chuẩn hóa Unicode NFC và gỡ bỏ ký tự ẩn / trang trí
    res = unicodedata.normalize("NFC", text)
    res = re.sub(r"[\u200b-\u200f\ufeff]", "", res)
    res = re.sub(r"[★☆◆◇●•※]+", " ", res)
    res = re.sub(r"[【\[]\s*([^】\]]+?)\s*[】\]]", r", \1, ", res)
    res = re.sub(r"\(\s*([^)]+?)\s*\)", r", \1, ", res)

    # 2. Loại bỏ dấu ngoặc kép và gạch ngang đầu dòng / đầu câu thoại
    res = re.sub(
        r"[\u201C\u201D\u201E\u201F\u00AB\u00BB\u2018\u2019\u201A\u201B\u0022\u0060\u2033\u2036\u300C\u300D\u300E\u300F\uFF02]+",
        "",
        res,
    )
    res = re.sub(r"^[\s\-–—―]+", "", res)
    res = re.sub(r":\s*[\-–—―]+\s*", ": ", res)
    res = re.sub(r"\s+[\-–—―]+\s+", ", ", res)

    # 3. Đổi chấm lửng ở giữa câu (khi sau vẫn là chữ) thành ngắt phẩy mềm
    res = re.sub(r"\s*(?:…|\.{2,})\s*(?=[a-zà-ỹA-ZÀ-Ỹ])", ", ", res)

    # 4. Chuẩn hóa chữ IN HOA toàn phần và lỗi viết hoa giữa câu
    res = normalize_all_caps_vietnamese(res)
    res = fix_mid_sentence_capitalization_and_names(res)

    # 5. Chuyển đổi ký hiệu toán học/so sánh -> lời đọc tiếng Việt
    if bilingual is not None:
        try:
            res = bilingual.convert_symbols_to_spoken_text(res)
        except Exception:
            pass

    # 6. Áp dụng từ điển từ vay mượn & đơn vị đo
    for pattern, replacement in VOICESTUDIO_LOANWORDS_MAP.items():
        res = re.sub(pattern, replacement, res, flags=re.IGNORECASE)

    # 7. Chuyển số thành chữ và phiên âm tiếng Anh còn sót
    res = convert_digits_to_vietnamese_words(res)
    if bilingual is not None:
        try:
            res = bilingual.transliterate_english_to_vietnamese(res)
        except Exception:
            pass

    # 8. Ngắt hơi nhẹ câu dài & dọn khoảng trắng, dấu phẩy
    res = insert_micro_pauses_for_long_sentences(res, max_words=16)
    res = re.sub(
        r"[\s\u00A0\u1680\u2000-\u200a\u202f\u205f\u3000—–-]*[,，、﹐][\s\u00A0\u1680\u2000-\u200a\u202f\u205f\u3000—–-]*(?:…|\.{3})?",
        ", ",
        res,
    )
    res = re.sub(r"^[,\s]+|[,\s]+$", "", res)
    return re.sub(r"\s+", " ", res).strip()
