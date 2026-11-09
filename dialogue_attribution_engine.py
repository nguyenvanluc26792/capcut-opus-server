# -*- coding: utf-8 -*-
"""
Dialogue Attribution Engine
High-precision deterministic dialogue parsing & role assignment for Vietnamese literature.
Pure Python standard library (re, dataclasses, typing). 0 MB VRAM, < 5ms execution latency.
"""

import re
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple, Any

@dataclass
class Segment:
    index: int
    text: str
    role: str               # "narrator" | "male" | "female"
    is_dialogue: bool       # True if the segment is spoken dialogue
    confidence: float       # 0.0 to 1.0
    attribution_rule: str   # "explicit_tag" | "para_continuation" | "continuity_turn" | "safe_fallback" | "narration"
    speaker_tag: str = ""   # e.g. "hắn cười nói", "nàng khẽ đáp"
    para_index: int = 0

class DialogueAttributionEngine:
    # Vietnamese speech verbs indicating dialogue attribution
    SPEECH_VERBS = [
        r'nói', r'bảo', r'hỏi', r'đáp', r'trả lời', r'thì thào', r'thì thầm',
        r'quát', r'gầm', r'hét', r'than', r'thở dài', r'cười', r'mỉm cười',
        r'nhếch mép', r'lẩm bẩm', r'nhủ', r'nghĩ', r'nghĩ thầm', r'thốt lên',
        r'kêu lên', r'lên tiếng', r'hô', r'hạ lệnh', r'cất tiếng', r'giải thích',
        r'nhắc nhở', r'cảnh cáo', r'van xin', r'cầu xin', r'gật đầu',
        r'lắc đầu', r'tiếp tục', r'trêu chọc', r'hỏi dồn', r'nạt', r'quát lớn'
    ]

    # Subject indicators for Male characters
    MALE_SUBJECTS = [
        r'hắn', r'chàng', r'huynh', r'đệ', r'anh', r'ông', r'lão', r'tiểu tử',
        r'sư phụ', r'phụ thân', r'thầy', r'ca ca', r'nam tử', r'nam nhân',
        r'thiếu gia', r'công tử', r'chàng trai', r'người đàn ông', r'hán tử',
        r'đại ca', r'tiểu ca', r'hoàng thượng', r'vương gia', r'tướng quân',
        r'thiếu niên', r'thanh niên', r'tráng sĩ', r'đại hán', r'lão giả',
        r'lão đầu', r'sư huynh', r'sư đệ', r'sư thúc', r'sư bá', r'tiểu hòa thượng'
    ]

    # Subject indicators for Female characters
    FEMALE_SUBJECTS = [
        r'nàng', r'cô', r'muội', r'tỷ', r'em', r'bà', r'tiểu thư', r'nha đầu',
        r'mẫu thân', r'sư muội', r'nữ tử', r'nữ nhân', r'thiếu nữ', r'cô nương',
        r'cô gái', r'người đàn bà', r'phu nhân', r'tỷ tỷ', r'nương nương',
        r'hoàng hậu', r'công chúa', r'quận chúa', r'mỹ phụ', r'lão bà',
        r'sư tỷ', r'nha hoàn', r'thị nữ', r'tiểu cô nương'
    ]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        verbs_pattern = r'(?:' + r'|'.join(self.SPEECH_VERBS) + r')'
        male_pattern = r'(?:' + r'|'.join(self.MALE_SUBJECTS) + r')'
        female_pattern = r'(?:' + r'|'.join(self.FEMALE_SUBJECTS) + r')'

        # Regex patterns to detect reporting tags:
        # 1. Pre-speech: "Hắn khẽ mỉm cười nói:" or "Nàng hỏi:"
        self.re_pre_male = re.compile(
            rf'\b({male_pattern})\b[^\n,.:;]*?\b{verbs_pattern}\b\s*[:\s]*$',
            re.IGNORECASE | re.UNICODE
        )
        self.re_pre_female = re.compile(
            rf'\b({female_pattern})\b[^\n,.:;]*?\b{verbs_pattern}\b\s*[:\s]*$',
            re.IGNORECASE | re.UNICODE
        )

        # 2. Post-speech: "... - hắn nói." or "...” - nàng đáp."
        self.re_post_male = re.compile(
            rf'[-–—―]?\s*(?:(?:lại|liền|khẽ|bèn|tức giận)\s+)?\b({male_pattern})\b[^\n,.:;]*?\b{verbs_pattern}\b',
            re.IGNORECASE | re.UNICODE
        )
        self.re_post_female = re.compile(
            rf'[-–—―]?\s*(?:(?:lại|liền|khẽ|bèn|tức giận)\s+)?\b({female_pattern})\b[^\n,.:;]*?\b{verbs_pattern}\b',
            re.IGNORECASE | re.UNICODE
        )

        # General subject matcher
        self.re_male_word = re.compile(rf'\b({male_pattern})\b', re.IGNORECASE | re.UNICODE)
        self.re_female_word = re.compile(rf'\b({female_pattern})\b', re.IGNORECASE | re.UNICODE)

    def normalize_text(self, text: str) -> str:
        """Normalizes varied quotes, hyphens, and whitespace."""
        if not text:
            return ""
        # Standardize quotation marks
        text = re.sub(r'[\u201C\u201D\u201E\u201F\u00AB\u00BB\u300C\u300D\u300E\u300F]', '"', text)
        # Standardize dashes
        text = re.sub(r'[\u2014\u2015\u2013\u2012]', '—', text)
        return text

    def _detect_tag_gender(self, tag_text: str) -> Tuple[Optional[str], float, str]:
        """Analyzes a reporting speech tag and determines speaker gender."""
        clean_tag = tag_text.strip()
        if not clean_tag:
            return None, 0.0, ""

        # Check explicit pre/post patterns
        if self.re_pre_female.search(clean_tag) or self.re_post_female.search(clean_tag):
            return "female", 0.95, clean_tag
        if self.re_pre_male.search(clean_tag) or self.re_post_male.search(clean_tag):
            return "male", 0.95, clean_tag

        # Fallback keyword match in tag
        has_female = bool(self.re_female_word.search(clean_tag))
        has_male = bool(self.re_male_word.search(clean_tag))
        if has_female and not has_male:
            return "female", 0.85, clean_tag
        if has_male and not has_female:
            return "male", 0.85, clean_tag

        return None, 0.0, ""

    def parse_text(self, raw_text: str) -> List[Segment]:
        """
        Parses full raw chapter text into an ordered list of attributed Segments.
        Maintains paragraph continuity and two-party alternation state.
        """
        normalized = self.normalize_text(raw_text)
        paragraphs = [p.strip() for p in normalized.split('\n') if p.strip()]

        segments: List[Segment] = []
        seg_index = 0

        # State machine registers
        last_dialogue_role: Optional[str] = None
        turn_history: List[str] = []
        narrative_interlude_count = 0

        for para_idx, para in enumerate(paragraphs):
            # Parse paragraph into sub-clauses (dialogue vs narration)
            para_segments = self._decompose_paragraph(para, para_idx)
            if not para_segments:
                continue

            para_has_dialogue = any(s['is_dialogue'] for s in para_segments)

            if not para_has_dialogue:
                narrative_interlude_count += 1
                if narrative_interlude_count >= 2:
                    # Reset turn history and speaker register after long narrative break
                    last_dialogue_role = None
                    turn_history.clear()
            else:
                narrative_interlude_count = 0

            # Determine dominant dialogue role for this paragraph if explicitly tagged
            para_established_role: Optional[str] = None
            para_rule = "narration"

            # 1. First pass: look for explicit tags in this paragraph
            for item in para_segments:
                if item['is_dialogue'] and item.get('tag_gender'):
                    para_established_role = item['tag_gender']
                    para_rule = "explicit_tag"
                    break

            # 2. If no explicit tag in paragraph, check Two-Party Continuity
            if para_has_dialogue and not para_established_role:
                if last_dialogue_role:
                    # Alternate between male and female if in ongoing exchange
                    alt_role = "female" if last_dialogue_role == "male" else "male"
                    para_established_role = alt_role
                    para_rule = "continuity_turn"
                else:
                    # Safe degradation to narrator
                    para_established_role = "narrator"
                    para_rule = "safe_fallback"

            # 3. Assign roles to each segment in the paragraph
            current_speaker = para_established_role or "narrator"

            for item in para_segments:
                text = item['text'].strip()
                if not text:
                    continue

                if item['is_dialogue']:
                    # Use explicit tag on segment if different from paragraph default
                    seg_role = item.get('tag_gender') or current_speaker
                    rule = "explicit_tag" if item.get('tag_gender') else para_rule
                    confidence = 0.95 if rule == "explicit_tag" else (0.80 if rule == "continuity_turn" else 0.50)

                    segments.append(Segment(
                        index=seg_index,
                        text=text,
                        role=seg_role,
                        is_dialogue=True,
                        confidence=confidence,
                        attribution_rule=rule,
                        speaker_tag=item.get('tag_text', ''),
                        para_index=para_idx
                    ))
                    if seg_role in ("male", "female"):
                        last_dialogue_role = seg_role
                        turn_history.append(seg_role)
                else:
                    # Pure narration segment
                    segments.append(Segment(
                        index=seg_index,
                        text=text,
                        role="narrator",
                        is_dialogue=False,
                        confidence=1.0,
                        attribution_rule="narration",
                        speaker_tag="",
                        para_index=para_idx
                    ))
                seg_index += 1

        return segments

    def _decompose_paragraph(self, para: str, para_idx: int) -> List[Dict[str, Any]]:
        """
        Decomposes a single paragraph into ordered units of Dialogue and Narration.
        Supports:
        - Quoted dialogue: "..."
        - Dash dialogue: — ... or - ...
        - Interjected tags: "Quote 1" - tag - "Quote 2"
        """
        results: List[Dict[str, Any]] = []

        # Case 1: Paragraph uses quotes: "..."
        if '"' in para:
            parts = re.split(r'(".*?")', para)
            for i, part in enumerate(parts):
                part = part.strip()
                if not part:
                    continue

                if part.startswith('"') and part.endswith('"') and len(part) >= 2:
                    dialogue_content = part[1:-1].strip()
                    if not dialogue_content:
                        continue

                    # Look ahead and behind for speech reporting tags
                    pre_text = parts[i - 1].strip() if i > 0 else ""
                    post_text = parts[i + 1].strip() if i + 1 < len(parts) else ""

                    tag_gender, conf, tag_matched = self._detect_tag_gender(pre_text)
                    if not tag_gender:
                        tag_gender, conf, tag_matched = self._detect_tag_gender(post_text)

                    results.append({
                        'is_dialogue': True,
                        'text': dialogue_content,
                        'tag_gender': tag_gender,
                        'tag_text': tag_matched
                    })
                else:
                    # Narration text outside quotes
                    results.append({
                        'is_dialogue': False,
                        'text': part,
                        'tag_gender': None,
                        'tag_text': ''
                    })
            return results

        # Case 2: Paragraph starts with dialogue dash: — or -
        dash_match = re.match(r'^\s*([—–-]\s*)(.+)$', para)
        if dash_match:
            rest = dash_match.group(2).strip()
            # Check for post-dialogue tag split: e.g. "Đi thôi. - Hắn nói." or "Ta không phục! — Thiếu niên quát lớn."
            tag_split = re.split(r'(\s*[-–—―]\s+[A-Za-zÀ-ỹ].*)$', rest, maxsplit=1)
            if len(tag_split) >= 2:
                dialogue_text = tag_split[0].strip()
                narr_text = tag_split[1].strip()
                tag_gender, conf, tag_matched = self._detect_tag_gender(narr_text)

                results.append({
                    'is_dialogue': True,
                    'text': dialogue_text,
                    'tag_gender': tag_gender,
                    'tag_text': tag_matched
                })
                clean_narr = re.sub(r'^[—–-]\s*', '', narr_text).strip()
                if clean_narr:
                    results.append({
                        'is_dialogue': False,
                        'text': clean_narr,
                        'tag_gender': None,
                        'tag_text': ''
                    })
            else:
                # Whole dashed line is dialogue
                results.append({
                    'is_dialogue': True,
                    'text': rest,
                    'tag_gender': None,
                    'tag_text': ''
                })
            return results

        # Case 3: Pure narration paragraph without quotes or opening dash
        results.append({
            'is_dialogue': False,
            'text': para,
            'tag_gender': None,
            'tag_text': ''
        })
        return results
