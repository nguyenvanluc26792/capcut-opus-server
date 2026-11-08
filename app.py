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
    target_vid = str(voice_id).replace("capcut_", "")
    
    # Chuẩn hóa voice id: các voice cũ không còn được ByteDance hỗ trợ trực tiếp -> map sang giọng chuẩn
    if 'dsp' in target_vid or '421' in target_vid:
        target_vid = 'vi_female_huong' if '421' in target_vid else 'BV074_streaming'
    
    clean_text = re.sub(r'[\s\u00A0\u1680\u2000-\u200A\u2028\u2029\u202F\u205F\u3000\uFEFF\u2014\u2013-]*[,\uff0c\u3001\ufe50][\s\u00A0\u1680\u2000-\u200A\u2028\u2029\u202F\u205F\u3000\uFEFF\u2014\u2013-]*(?:\u2026|\.{3})?', ', ', text)
    clean_text = re.sub(r' {2,}', ' ', clean_text).strip()
    
    last_err = None
    # Thử gọi voice yêu cầu; nếu thất bại thì tự fallback sang BV074_streaming hoặc vi_female_huong
    for attempt in range(3):
        try:
            res = _capcut_ns['doc_lo']([clean_text], target_vid)
            if not res or not res[0]:
                fallback_vid = 'vi_female_huong' if 'female' in target_vid or '074' in target_vid else 'BV075_streaming'
                if target_vid != fallback_vid:
                    res = _capcut_ns['doc_lo']([clean_text], fallback_vid)
            if not res or not res[0]:
                raise Exception("CapCut did not return audio URL")
            audio_url = res[0]
            resp = requests.get(audio_url, timeout=15)
            resp.raise_for_status()
            if len(resp.content) > 300:
                return resp.content
        except Exception as e:
            last_err = e
            time.sleep(0.2 * (attempt + 1))
    raise last_err or Exception("Failed to generate CapCut audio after 3 attempts")

def convert_to_opus_48k(audio_bytes):
    try:
        import subprocess
        proc = subprocess.Popen(
            ["ffmpeg", "-y", "-i", "pipe:0", "-ar", "48000", "-c:a", "libopus", "-b:a", "48k", "-f", "ogg", "pipe:1"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        out, _ = proc.communicate(input=audio_bytes, timeout=12)
        if proc.returncode == 0 and len(out) > 300:
            return out
    except Exception:
        pass
    return audio_bytes

@app.route("/", methods=["GET"])
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "service": "CapCut OPUS 48kHz Online Server 24/7"})

@app.route("/fix", methods=["GET"])
def fix_page():
    html = """<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sửa Lỗi LReader 1 Chạm</title>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #f8fafc; padding: 20px; text-align: center; }
  .card { max-width: 480px; margin: 30px auto; background: #1e293b; padding: 24px; border-radius: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }
  h1 { font-size: 1.25rem; color: #38bdf8; margin-bottom: 12px; }
  p { font-size: 0.92rem; line-height: 1.5; color: #cbd5e1; margin-bottom: 20px; }
  button { background: linear-gradient(135deg, #0284c7, #2563eb); color: white; border: none; padding: 14px 20px; border-radius: 10px; font-size: 1rem; font-weight: bold; cursor: pointer; width: 100%; transition: opacity 0.2s; }
  button:active { opacity: 0.8; }
  #status { margin-top: 18px; padding: 14px; border-radius: 10px; font-size: 0.9rem; text-align: left; line-height: 1.5; }
  .success { background: rgba(34, 197, 94, 0.15); color: #4ade80; border: 1px solid #22c55e; }
  .error { background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid #ef4444; }
  .loading { background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid #0284c7; }
</style>
</head>
<body>
<div class="card">
  <h1>🛠️ Cập Nhật & Sửa Lỗi Giọng Đọc LReader</h1>
  <p>Hệ thống sẽ nạp bản vá chuẩn <b>v1.6.225 (Build 410)</b> với 11 Giọng CapCut AI mượt mà vào máy bạn trong 1 giây.</p>
  <button id="btnFix" onclick="doFix()">BẤM ĐỂ CẬP NHẬT & SỬA LỖI NGAY</button>
  <div id="status" class="loading">⏳ Đang tự động kiểm tra app LReader trên máy...</div>
</div>
<script>
async function doFix() {
  const btn = document.getElementById('btnFix');
  const st = document.getElementById('status');
  btn.disabled = true;
  st.style.display = 'block';
  st.className = 'loading';
  st.innerHTML = '⏳ Bước 1/2: Đang tải bản vá v1.6.225 sạch lỗi từ Render...';

  try {
    const bundleRes = await fetch('/api/ota/bundle?t=' + Date.now());
    if (!bundleRes.ok) throw new Error('Không tải được mã nguồn từ Render');
    const htmlContent = await bundleRes.text();
    if (!htmlContent || htmlContent.length < 50000) throw new Error('Mã nguồn quá nhỏ');

    st.innerHTML = '⏳ Bước 2/2: Đang nạp bản vá vào app LReader trên máy bạn...';
    const localRes = await fetch('http://127.0.0.1:8765/api/ota/update', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ html_content: htmlContent })
    });
    const d = await localRes.json();
    if (d && d.success) {
      st.className = 'success';
      st.innerHTML = '🎉 <b>CẬP NHẬT THÀNH CÔNG RỰC RỠ!</b><br><br>Đã nạp bản vá <b>v1.6.225 (Build 410)</b>.<br><br>👉 <b>HÃY VUỐT TẮT APP LREADER VÀ MỞ LẠI:</b><br>11 giọng CapCut AI (Nam Trầm Ấm, Nữ Phổ Thông, Review Phim...) sẽ cất tiếng đọc mượt mà 100% không bao giờ rơi về Google TTS!';
      btn.style.display = 'none';
      return;
    } else {
      throw new Error((d && d.error) || 'Lỗi nạp');
    }
  } catch (err) {
    // Phương án 2: Gọi server_url
    try {
      st.innerHTML = '⏳ Đang thử phương án nạp tự động qua OkHttp máy...';
      const res2 = await fetch('http://127.0.0.1:8765/api/ota/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ server_url: 'https://capcut-opus-server.onrender.com' })
      });
      const d2 = await res2.json();
      if (d2 && d2.success) {
        st.className = 'success';
        st.innerHTML = '🎉 <b>CẬP NHẬT THÀNH CÔNG RỰC RỠ!</b><br><br>👉 Hãy vuốt tắt app LReader và mở lại để tận hưởng giọng CapCut AI!';
        btn.style.display = 'none';
        return;
      }
    } catch (_) {}

    st.className = 'error';
    st.innerHTML = '⚠️ <b>Chưa kết nối được với LReader</b> (' + err.message + ').<br><br><b>Cách xử lý:</b> Hãy mở app LReader lên trước (để app chạy nền), sau đó quay lại trang này bấm nút trên là xong ngay!';
    btn.disabled = false;
  }
}
window.onload = function() {
  setTimeout(doFix, 400);
};
</script>
</body>
</html>"""
    return Response(html, mimetype="text/html; charset=utf-8")

@app.route("/api/ota/version", methods=["GET"])
def ota_version():
    manifest_path = BASE_DIR / "static" / "ota_manifest.json"
    if manifest_path.exists():
        return Response(manifest_path.read_text(encoding="utf-8"), mimetype="application/json")
    return jsonify({"error": "Manifest not found"}), 404

@app.route("/api/ota/bundle", methods=["GET"])
@app.route("/api/ota/index.html", methods=["GET"])
def ota_bundle():
    bundle_path = BASE_DIR / "static" / "index.html"
    if bundle_path.exists():
        return send_file(bundle_path, mimetype="text/html; charset=utf-8")
    return jsonify({"error": "Bundle not found"}), 404

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

        voice_id = req.get("voice_id") or req.get("voice") or "vi_female_huong"
        dialogue_role = req.get("dialogue_role") or "narration"

        is_quote = bool(re.match(r'^\s*[""“«「『\-–—―]', text) or re.search(r'[""“«「『][^"”»」』]+[""”»」』]', text))
        if dialogue_role == "female":
            target_vid = "multi_female_richgirl_uranus_bigtts"
        elif dialogue_role == "male" or (is_quote and dialogue_role != "narration"):
            target_vid = "BV075_streaming"
        else:
            target_vid = voice_id

        # Sinh âm thanh từ CapCut
        raw_mp3 = generate_capcut_audio(text, target_vid)
        
        req_fmt = (req.get("format") or request.args.get("format") or "mp3").lower()
        if req_fmt == "opus":
            opus_data = convert_to_opus_48k(raw_mp3)
            return send_file(
                io.BytesIO(opus_data),
                mimetype="audio/ogg; codecs=opus",
                as_attachment=False
            )

        # Mặc định trả về MP3 chuẩn (audio/mpeg) - tương thích 100% với Web Audio API và mọi thiết bị Android
        return send_file(
            io.BytesIO(raw_mp3),
            mimetype="audio/mpeg",
            as_attachment=False
        )

    except Exception as e:
        print(f"[TTS Error]: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
