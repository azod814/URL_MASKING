# fixed_masker8000.py
# Robust safe redirector with UI, suggestions and defensive error handling.
# Port: 8000
# Usage: pip install flask pyngrok
# Start ngrok: ngrok http 8000  (if auto-ngrok fails)

from flask import Flask, request, render_template_string
import random, string, threading, socket, os, csv, time, traceback
from pyngrok import ngrok

app = Flask(__name__)
url_mapping = {}
log_file = "clicks_log.csv"

# -------------------------
# Utilities
# -------------------------
def gen_token(n=10):
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(n))

def domain_from_url(url):
    if not url:
        return ""
    if "://" in url:
        url = url.split("://", 1)[1]
    return url.split("/")[0].split(":")[0].lower()

def domain_resolves(d):
    try:
        if not d:
            return False
        socket.gethostbyname(d)
        return True
    except:
        return False

def rand_suffix(n=3):
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(n))

def suggest_fake_names(base_text, max_s=6):
    base = base_text or "site"
    if "://" in base:
        base = base.split("://",1)[1]
    base = base.split("/")[0].replace("www.", "")
    sld = base.split(".")[0] or "site"
    cand = set()
    for i in range(len(sld)):
        cand.add(sld[:i] + '-' + sld[i:])
        cand.add(sld + rand_suffix(2))
    for _ in range(max_s * 2):
        cand.add(sld + rand_suffix(2))
    results = []
    for c in list(cand):
        dom = c + ".com"
        results.append((dom, domain_resolves(dom)))
        if len(results) >= max_s:
            break
    results.sort(key=lambda x: (x[1], x[0]))
    return results[:max_s]

def ensure_log_header():
    try:
        if not os.path.exists(log_file):
            with open(log_file, "w", newline='') as f:
                csv.writer(f).writerow(["timestamp","token","remote_addr","original"])
    except Exception as e:
        print("ensure_log_header error:", e)

def safe_log_click(token, remote):
    try:
        ensure_log_header()
        with open(log_file, "a", newline='') as f:
            csv.writer(f).writerow([time.strftime("%Y-%m-%d %H:%M:%S"), token, remote, url_mapping[token]["original"]])
    except Exception as e:
        # don't let logging break the handler
        print("log_click failed:", e)

# -------------------------
# Landing route (robust)
# -------------------------
@app.route('/r/<token>')
def landing(token):
    try:
        info = url_mapping.get(token)
        if not info:
            return "Not found (invalid/expired token).", 404

        original = info.get("original", "")
        label = info.get("label", "") or ""
        # Try logging but don't crash if it fails
        try:
            safe_log_click(token, request.remote_addr)
        except Exception as e:
            print("safe_log_click error:", e)

        # Nice UI with auto-redirect
        html = '''
        <!doctype html>
        <html>
          <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width,initial-scale=1">
            <title>URL Awareness — Opening</title>
            <meta http-equiv="refresh" content="1.5; url={{ original }}">
            <style>
              body{font-family:Inter,Arial,Helvetica,sans-serif;background:#071028;color:#e6eef8;margin:0;display:flex;align-items:center;justify-content:center;height:100vh}
              .card{background:linear-gradient(180deg,#082033 0%, #031428 100%);padding:28px;border-radius:14px;box-shadow:0 18px 60px rgba(2,6,23,.6);width:92%;max-width:540px;text-align:center;border:1px solid rgba(255,255,255,0.03)}
              .tag{display:inline-block;background:rgba(34,197,94,0.12);color:#bbf7d0;padding:6px 12px;border-radius:999px;font-weight:700;margin-bottom:12px;font-size:12px}
              .fake{font-size:28px;font-weight:800;color:#86efac;margin-bottom:8px;word-break:break-word}
              .sub{color:#9fb4c9;margin-bottom:18px}
              .loader{width:48px;height:48px;border-radius:999px;border:6px solid rgba(255,255,255,0.08);border-top-color:#fff;margin:10px auto;animation:spin 1s linear infinite}
              @keyframes spin{to{transform:rotate(360deg)}}
              .orig-box{background:rgba(255,255,255,0.03);padding:12px;border-radius:10px;border:1px dashed rgba(255,255,255,0.04);margin-top:12px;color:#dff4ff;word-break:break-word}
              .note{font-size:12px;color:#9fb4c9;margin-top:10px}
              a.link{color:#7dd3fc;text-decoration:none}
            </style>
          </head>
          <body>
            <div class="card">
              <div class="tag">URL Awareness Demo</div>
              <div class="fake">{{ label }}</div>
              <div class="sub">This is how the link LOOKED. The real destination is shown below.</div>
              <div class="loader"></div>
              <div class="orig-box">{{ original }}</div>
              <div class="note">If not redirected <a class="link" href="{{ original }}" target="_blank">click here</a>.</div>
            </div>
          </body>
        </html>
        '''
        return render_template_string(html, original=original, label=label)
    except Exception:
        tb = traceback.format_exc()
        print("Exception in /r/<token>:\n", tb)
        # return traceback to browser for debugging (safe for local/testing)
        return "<pre>Internal error:\n\n" + tb + "</pre>", 500

# -------------------------
# Console flow (menu)
# -------------------------
def mask_flow(public_url):
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("\n=== CREATE AWARENESS LINK ===\n")
        original = input("1) Enter ORIGINAL full URL (where users should really land):\n> ").strip()
        if not original:
            input("Empty original. Press Enter to retry...")
            continue

        fake_input = input("\n2) Enter FAKE-looking text (how the link APPEARS, e.g. youtube.com):\n> ").strip()
        if not fake_input:
            fake_input = "example.com"

        print("\nGenerating suggestions based on your input...")
        suggestions = suggest_fake_names(fake_input, max_s=6)
        print("\nSuggestions (display-only):")
        for i, (d, r) in enumerate(suggestions, start=1):
            status = "TAKEN" if r else "FREE"
            print(f" [{i}] {d}   ({status})")
        print(" [0] Use exactly what I typed:", fake_input)

        sel = input("\nChoose label index to SHOW on landing page (0-{}): ".format(len(suggestions))).strip()
        if sel.isdigit():
            sel = int(sel)
            if sel == 0:
                chosen_label = fake_input
            elif 1 <= sel <= len(suggestions):
                chosen_label = suggestions[sel-1][0]
            else:
                chosen_label = fake_input
        else:
            chosen_label = fake_input

        print("\nPreview:")
        print(" Original (destination):", original)
        print(" Display label (on landing page):", chosen_label)
        conf = input("\nConfirm create awareness link? (y/N): ").strip().lower()
        if conf != 'y':
            input("Cancelled. Press Enter to restart...")
            continue

        token = gen_token(10)
        url_mapping[token] = {"original": original, "label": chosen_label, "created": time.time()}

        # build final link using provided public_url
        pub = public_url.rstrip('/') if public_url else None
        if not pub:
            print("\nNo public ngrok URL provided — start ngrok and paste forwarding URL now.")
            manual = input("Paste ngrok URL (or Enter to cancel): ").strip()
            if not manual:
                input("Cancelled. Press Enter...")
                return
            pub = manual.rstrip('/')

        final = pub + "/r/" + token
        border = "+" + "-"*(len(final)+6) + "+"
        print("\nFINAL AWARENESS LINK (share this):")
        print(border)
        print("|  " + final + "  |")
        print(border)
        print("\nOpen it in a browser to test the landing page -> it will auto-redirect to the original.")
        input("\nPress Enter to continue...")
        return

def show_mappings():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("\n=== CURRENT MAPPINGS ===\n")
    if not url_mapping:
        print("No mappings created yet.")
    else:
        for t, info in url_mapping.items():
            print(" Token:", t)
            print("  Original:", info.get("original"))
            print("  Label:   ", info.get("label"))
            print("  Created: ", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(info.get("created", 0))))
            print("-" * 36)
    input("\nPress Enter to return to menu...")

# -------------------------
# Start app + ngrok + menu
# -------------------------
def start_app():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("SAFE Awareness Masking Tool — port 8000\n")
    public = None
    try:
        # try auto-start ngrok
        tunnel = ngrok.connect(8000)
        public = tunnel.public_url
        print("Auto-ngrok started, public URL:", public)
    except Exception as e:
        print("Auto-ngrok failed (you can run ngrok manually):", e)
        manual = input("If ngrok is running, paste its forwarding URL here (or press Enter to skip): ").strip()
        public = manual if manual else None

    # Ensure logging file exists
    ensure_log_header()

    # Start Flask app in a thread
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=8000, debug=False, use_reloader=False)).start()

    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("SAFE Awareness Masking Tool")
        print("NGROK public:", public or "(not detected)")
        print("\n1) Create awareness link")
        print("2) Show mappings")
        print("3) Exit")
        ch = input("> ").strip()
        if ch == "1":
            mask_flow(public)
        elif ch == "2":
            show_mappings()
        elif ch == "3":
            print("Exiting.")
            os._exit(0)
        else:
            input("Invalid choice. Press Enter to continue...")

if __name__ == "__main__":
    start_app()
