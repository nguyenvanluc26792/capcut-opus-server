import os
import sys
import io
import re
import time
import marshal
import requests
from math import gcd
from pathlib import Path
from flask import Flask, request, jsonify, send_file, Response

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

app = Flask(__name__)

# Cho phép CORS để app từ điện thoại hay trình duyệt đều gọi được
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response

# 1. Nạp module CapCut gốc
BASE_DIR = Path(__file__).resolve().parent
CAPCUT_MODULE_PATH = BASE_DIR / "decomp_tts_service.bin"
_capcut_ns = {'__file__': 'tts_service.py'}

if CAPCUT_MODULE_PATH.exists():
    try:
        _code = marshal.loads(CAPCUT_MODULE_PATH.read_bytes())
        exec(_code, _capcut_ns)
        print("[OK] CapCut TTS Module loaded successfully!")
    except Exception as e:
        print(f"[ERROR] Failed to load decomp_tts_service.bin: {e}")
else:
    print("[WARN] decomp_tts_service.bin not found!")

def generate_capcut_audio(text, voice_id):
    if 'doc_lo' not in _capcut_ns:
        raise Exception("CapCut module not initialized")
    target_vid = voice_id
    if 'dsp' in str(target_vid) or '421' in str(target_vid):
        target_vid = 'vi_female_huong' if '421' in str(target_vid) else 'BV074_streaming'
    
    clean_text = re.sub(r'[\s\u00A0\u1680\u2000-\u200A\u2028\u2029\u202F\u205F\u3000\uFEFF\u2014\u2013-]*[,\uff0c\u3001\ufe50][\s\u00A0\u1680\u2000-\u200A\u2028\u2029\u202F\u205F\u3000\uFEFF\u2014\u2013-]*(?:\u2026|\.{3})?', ', ', text)
    clean_text = re.sub(r' {2,}', ' ', clean_text).strip()
    
    last_err = None
    for attempt in range(3):
        try:
            res = _capcut_ns['doc_lo']([clean_text], target_vid)
            if not res or not res[0]:
                if target_vid != 'BV074_streaming':
                    res = _capcut_ns['doc_lo']([clean_text], 'BV074_streaming')
            if not res or not res[0]:
                raise Exception("CapCut did not return audio URL")
            audio_url = res[0]
            resp = requests.get(audio_url, timeout=12)
            resp.raise_for_status()
            if len(resp.content) > 300:
                return resp.content
        except Exception as e:
            last_err = e
            time.sleep(0.2 * (attempt + 1))
    raise last_err or Exception("Failed to generate CapCut audio after 3 attempts")

def convert_to_opus_48k(audio_bytes):
    # Cách 1: Dùng ffmpeg (siêu nhanh, chuẩn xác tuyệt đối 48kHz OPUS, nhẹ CPU)
    try:
        import subprocess
        proc = subprocess.Popen(
            ["ffmpeg", "-y", "-i", "pipe:0", "-ar", "48000", "-c:a", "libopus", "-b:a", "48k", "-f", "ogg", "pipe:1"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        out, _ = proc.communicate(input=audio_bytes, timeout=10)
        if proc.returncode == 0 and len(out) > 300:
            return out
    except Exception as e:
        pass

    # Cách 2: Dùng soundfile & scipy (dự phòng)
    try:
        import soundfile as sf
        import numpy as np
        from scipy.signal import resample_poly

        data, orig_sr = sf.read(io.BytesIO(audio_bytes))
        target_sr = 48000
        if orig_sr != target_sr:
            g = gcd(orig_sr, target_sr)
            up = target_sr // g
            down = orig_sr // g
            data_48k = resample_poly(data, up, down).astype(np.float32)
        else:
            data_48k = data.astype(np.float32)

        out_buf = io.BytesIO()
        sf.write(out_buf, data_48k, target_sr, format='OGG', subtype='OPUS')
        opus_data = out_buf.getvalue()
        if opus_data and len(opus_data) > 300:
            return opus_data
    except Exception as e:
        print(f"[OPUS Transcode Error]: {e}")
    return audio_bytes  # Fallback trả về MP3 gốc nếu lỗi nén

@app.route("/", methods=["GET"])
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "service": "CapCut OPUS 48kHz Online Server 24/7"})

@app.route("/api/ota/version", methods=["GET"])
def ota_version():
    manifest_path = BASE_DIR / "static" / "ota_manifest.json"
    if manifest_path.exists():
        return Response(manifest_path.read_text(encoding="utf-8"), mimetype="application/json")
    return jsonify({"error": "Manifest not found"}), 404

@app.route("/static/<path:filename>", methods=["GET"])
def serve_static(filename):
    static_file = BASE_DIR / "static" / filename
    if static_file.exists():
        return send_file(static_file)
    return jsonify({"error": "File not found"}), 404

@app.route("/api/tts", methods=["POST", "OPTIONS"])
def api_tts():
    if request.method == "OPTIONS":
        return Response("", status=200)

    try:
        req = request.get_json(force=True, silent=True) or {}
        text = req.get("text", "").strip()
        if not text:
            return jsonify({"error": "Empty text"}), 400

        voice_id = req.get("voice_id") or req.get("voice") or "BV421_vivn_streaming"
        dialogue_role = req.get("dialogue_role") or "narration"

        # LOGIC PHÂN VAI CAPCUT CHUẨN:
        # 1. Dẫn truyện: Nhỏ Ngọt Ngào (BV421_vivn_streaming) / Nữ Phổ Thông (vi_female_huong)
        # 2. Thoại Nam: Nam Trầm Ấm (BV075_streaming)
        # 3. Thoại Nữ: Review Phim (multi_female_richgirl_uranus_bigtts)
        is_quote = bool(re.match(r'^\s*[""“«「『\-–—―]', text) or re.search(r'[""“«「『][^"”»」』]+[""”»」』]', text))
        if dialogue_role == "female":
            target_vid = "multi_female_richgirl_uranus_bigtts"
        elif dialogue_role == "male" or (is_quote and dialogue_role != "narration"):
            target_vid = "BV075_streaming"
        else:
            target_vid = voice_id

        # Sinh âm thanh từ CapCut
        raw_mp3 = generate_capcut_audio(text, target_vid)
        
        # Nén thời gian thực sang chuẩn OPUS 48kHz
        opus_data = convert_to_opus_48k(raw_mp3)

        return send_file(
            io.BytesIO(opus_data),
            mimetype="audio/ogg; codecs=opus",
            as_attachment=False
        )

    except Exception as e:
        print(f"[TTS Error]: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
