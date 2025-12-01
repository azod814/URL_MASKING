# url_masker.py — Final Premium Version (Banner + Spinner Landing)
# Requirements:
#   pip install flask pyngrok

from flask import Flask, request, render_template_string
import random, string, threading, socket, os, csv, time, traceback
from pyngrok import ngrok

app = Flask(__name__)
url_mapping = {}
log_file = "clicks_log.csv"

# -------------------------
# ASCII BANNER
# -------------------------
def banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("\033[96m" + r"""
 ███╗   ███╗ █████╗ ███████╗██╗  ██╗███████╗██╗  ██╗███████╗██████╗ 
 ████╗ ████║██╔══██╗██╔════╝██║ ██╔╝██╔════╝██║ ██╔╝██╔════╝██╔══██╗
 ██╔████╔██║███████║███████╗█████╔╝ █████╗  █████╔╝ █████╗  ██████╔╝
 ██║╚██╔╝██║██╔══██║╚════██║██╔═██╗ ██╔══╝  ██╔═██╗ ██╔══╝  ██╔══██╗
 ██║ ╚═╝ ██║██║  ██║███████║██║  ██╗███████╗██║  ██╗███████╗██║  ██║
 ╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝

                \033[92mSAFE URL AWARENESS TOOL — SPINNER MODE\033[96m
 --------------------------------------------------------------------
    """ + "\033[0m")


# -------------------------
# UTILITIES
# -------------------------
def gen_token(n=10):
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(n))

def domain_from_url(url):
    if not url:
        return ""
    if "://" in url:
        url = url.split("://", 1)[1]
    return url.split("/")[0].split(":")[0].lower()

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

    suggestions = []
    for c in list(cand):
        dom = c + ".com"
        suggestions.append((dom, False))
        if len(suggestions) >= max_s:
            break

    return suggestions


# -------------------------
# SAFE LOGGING
# -------------------------
def ensure_log_header():
    try:
        if not os.path.exists(log_file):
            with open(log_file, "w", newline='') as f:
                csv.writer(f).writerow(["time", "token", "ip", "original"])
    except:
        pass

def safe_log_click(token, ip):
    try:
        ensure_log_header()
        with open(log_file, "a", newline='') as f:
            csv.writer(f).writerow([
                time.strftime("%Y-%m-%d %H:%M:%S"),
                token,
                ip,
                url_mapping[token]["original"]
            ])
    except:
        pass


# -------------------------
# LANDING PAGE — PURE SPINNER
# -------------------------
@app.route('/r/<token>')
def landing(token):
    try:
        info = url_mapping.get(token)
        if not info:
            return "Invalid link or expired.", 404

        original = info["original"]

        try:
            safe_log_click(token, request.remote_addr)
        except:
            pass

        html = '''
        <!doctype html>
        <html>
          <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width,initial-scale=1">
            <title>Loading…</title>

            <!-- Auto redirect -->
            <meta http-equiv="refresh" content="1.5; url={{ original }}">

            <style>
              html,body{height:100%;margin:0;background:#000;}
              .wrap{height:100%;display:flex;align-items:center;justify-content:center;flex-direction:column;}

              .spinner{
                width:72px;height:72px;border-radius:50%;
                border:8px solid rgba(255,255,255,0.08);
                border-top-color:#fff;
                animation:spin 1s linear infinite;
              }
              @keyframes spin{to{transform:rotate(360deg)}}

              .txt{
                color:#999;margin-top:16px;
                font-family:system-ui,Arial;font-size:13px;
              }
            </style>

            <script>
              setTimeout(function(){
                try{ window.location.replace("{{ original }}"); }catch(e){}
              },1500);
            </script>
          </head>
          <body>
            <div class="wrap">
              <div class="spinner"></div>
              <div class="txt">Loading…</div>
            </div>
          </body>
        </html>
        '''
        return render_template_string(html, original=original)

    except Exception:
        return "<pre>" + traceback.format_exc() + "</pre>", 500


# -------------------------
# CREATE MASKED LINK (CONSOLE FLOW)
# -------------------------
def mask_flow(public_url):
    while True:
        banner()
        print("STEP 1: Enter ORIGINAL URL (real destination):")
        original = input("> ").strip()
        if not original:
            input("Original URL empty. Press Enter…")
            continue

        print("\nSTEP 2: Enter FAKE-style URL text (lookalike label):")
        fake_in = input("> ").strip() or "example.com"

        print("\nGenerating suggestions…")
        sugg = suggest_fake_names(fake_in, 6)

        print("\nSUGGESTIONS:")
        for i,(dom,_) in enumerate(sugg,1):
            print(f" [{i}] {dom}")
        print(" [0] Use exactly:", fake_in)

        ch = input("\nChoose label index (0-6): ").strip()
        if ch.isdigit():
            ch = int(ch)
            if ch == 0:
                label = fake_in
            elif 1 <= ch <= len(sugg):
                label = sugg[ch-1][0]
            else:
                label = fake_in
        else:
            label = fake_in

        print("\nSUMMARY:")
        print("  Original →", original)
        print("  Fake Label →", label)

        ok = input("\nCreate final masked link? (y/N): ").lower()
        if ok != "y":
            input("Cancelled. Press Enter…")
            continue

        token = gen_token(12)
        url_mapping[token] = {
            "original": original,
            "label": label,
            "created": time.time()
        }

        final = public_url.rstrip("/") + "/r/" + token
        bar = "+" + "-"*(len(final)+6) + "+"

        print("\nFINAL LINK:")
        print(bar)
        print("|  " + final + "  |")
        print(bar)

        input("\nPress Enter to continue…")
        return


# -------------------------
# MENU
# -------------------------
def menu(public_url):
    while True:
        banner()
        print("NGROK Public URL:", public_url or "(not detected)")
        print("\n1) Create Masked Awareness Link")
        print("2) Show Saved Mappings")
        print("3) Exit")

        ch = input("> ").strip()
        if ch == "1":
            mask_flow(public_url)
        elif ch == "2":
            banner()
            if not url_mapping:
                print("No mappings created yet.")
            else:
                for t,info in url_mapping.items():
                    print("\nTOKEN:", t)
                    print(" Original:", info["original"])
                    print(" Fake Label:", info["label"])
                    print(" Created:", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(info["created"])))
            input("\nPress Enter…")
        elif ch == "3":
            os._exit(0)
        else:
            input("Invalid. Press Enter…")


# -------------------------
# START APP + NGROK
# -------------------------
def start():
    banner()
    print("Starting ngrok on port 8000…\n")

    public = None
    try:
        tunnel = ngrok.connect(8000)
        public = tunnel.public_url
        print("Auto-ngrok started →", public)
    except Exception as e:
        print("Auto-ngrok failed:", e)
        public = input("Paste ngrok forwarding URL manually:\n> ").strip()

    ensure_log_header()

    threading.Thread(
        target=lambda: app.run(
            host="0.0.0.0",
            port=8000,
            debug=False,
            use_reloader=False
        )
    ).start()

    time.sleep(1)
    menu(public)


if __name__ == "__main__":
    start()
