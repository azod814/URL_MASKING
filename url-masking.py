from flask import Flask, request, render_template_string
import random, string, threading, socket, os, csv, time
from pyngrok import ngrok

app = Flask(__name__)
url_mapping = {}
log_file = "clicks_log.csv"

# ============================
# BANNER
# ============================
def banner():
    print(r"""
 ███╗   ███╗ █████╗ ███████╗██╗  ██╗███████╗██╗  ██╗███████╗██████╗ 
 ████╗ ████║██╔══██╗██╔════╝██║ ██╔╝██╔════╝██║ ██╔╝██╔════╝██╔══██╗
 ██╔████╔██║███████║███████╗█████╔╝ █████╗  █████╔╝ █████╗  ██████╔╝
 ██║╚██╔╝██║██╔══██║╚════██║██╔═██╗ ██╔══╝  ██╔═██╗ ██╔══╝  ██╔══██╗
 ██║ ╚═╝ ██║██║  ██║███████║██║  ██╗███████╗██║  ██╗███████╗██║  ██║
 ╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝

               SAFE URL MASKER (Port 8000 Version)
---------------------------------------------------------------------
    """)

# ============================
# UTILITIES
# ============================
def gen_token(n=10):
    return ''.join(random.choice(string.ascii_lowercase+string.digits) for _ in range(n))

def domain_from_url(url):
    if "://" in url:
        url = url.split("://",1)[1]
    return url.split("/")[0].split(":")[0].lower()

def domain_resolves(d):
    try:
        socket.gethostbyname(d)
        return True
    except:
        return False

def rand_suffix(n=3):
    return ''.join(random.choice(string.ascii_lowercase+string.digits) for _ in range(n))

def suggest_fake_names(base_sld, max_s=6):
    sld = base_sld
    cand = set()

    for i in range(len(sld)):
        cand.add(sld[:i] + '-' + sld[i:])
        cand.add(sld + rand_suffix(2))

    for _ in range(max_s * 2):
        cand.add(sld + rand_suffix(2))

    final = []
    for c in list(cand):
        dom = c + ".com"
        final.append((dom, domain_resolves(dom)))
        if len(final) >= max_s:
            break

    final.sort(key=lambda x: (x[1], x[0]))
    return final[:max_s]

def ensure_log_header():
    if not os.path.exists(log_file):
        with open(log_file, "w", newline='') as f:
            csv.writer(f).writerow(["timestamp", "token", "remote_addr", "original"])

def log_click(token, remote):
    ensure_log_header()
    with open(log_file, "a", newline='') as f:
        csv.writer(f).writerow([
            time.strftime("%Y-%m-%d %H:%M:%S"),
            token,
            remote,
            url_mapping[token]["original"]
        ])

# ============================
# FLASK LANDING PAGE
# ============================
@app.route('/r/<token>')
def landing(token):
    info = url_mapping.get(token)
    if not info:
        return "Not found", 404

    orig = info["original"]
    label = info.get("label") or ""

    try:
        log_click(token, request.remote_addr)
    except:
        pass

    html = '''
    <!doctype html>
    <html>
      <head>
        <meta charset="utf-8">
        <title>Opening…</title>
        <style>
          body{font-family:Arial;background:#0f172a;color:white;
               display:flex;align-items:center;justify-content:center;height:100vh;}
          .box{background:#1e293b;padding:30px;border-radius:12px;text-align:center;
               box-shadow:0 10px 30px rgba(0,0,0,0.4);max-width:380px;}
          .label{font-size:30px;color:#22c55e;font-weight:bold;margin-bottom:10px;}
          .loader{width:45px;height:45px;border:5px solid rgba(255,255,255,0.2);
                  border-top-color:white;border-radius:50%;margin:15px auto;
                  animation:spin 1s linear infinite;}
          @keyframes spin{to{transform:rotate(360deg);}}
          .orig{background:#d1fae5;color:#065f46;padding:8px 12px;border-radius:6px;
                font-weight:bold;margin-top:12px;display:inline-block;}
        </style>
        <meta http-equiv="refresh" content="1.4;url={{orig}}">
      </head>
      <body>
        <div class="box">
          <div class="label">{{label}}</div>
          <div>Opening… please wait</div>
          <div class="loader"></div>
          <div class="orig">{{orig}}</div>
        </div>
      </body>
    </html>
    '''

    return render_template_string(html, orig=orig, label=label)

# ============================
# MASKING FLOW
# ============================
def mask_flow(public_url):
    while True:
        os.system('clear')
        banner()

        print("1) Enter ORIGINAL URL:")
        original = input("> ").strip()

        print("\n2) Enter FAKE display label:")
        fake_enter = input("> ").strip()

        fake_choice = None

        if fake_enter:
            sld = domain_from_url(fake_enter)
            suggestions = suggest_fake_names(sld, 5)

            print("\nSuggested fake names:")
            for i,(d,r) in enumerate(suggestions,start=1):
                print(f" [{i}] {d} ({'TAKEN' if r else 'FREE'})")
            print(" [0] Use exactly my input")

            sel = input("Choose (0-5): ").strip()
            if sel.isdigit():
                sel = int(sel)
                if sel == 0:
                    fake_choice = fake_enter
                elif 1 <= sel <= len(suggestions):
                    fake_choice = suggestions[sel-1][0]
                else:
                    fake_choice = fake_enter
            else:
                fake_choice = fake_enter
        else:
            fake_choice = ""

        print("\nOriginal:", original)
        print("Fake Label:", fake_choice)
        conf = input("Confirm? (y/n): ").strip().lower()
        if conf != "y":
            input("Cancelled. Press Enter…")
            continue

        token = gen_token()
        url_mapping[token] = {
            "original": original,
            "label": fake_choice,
            "created": time.time()
        }

        final = public_url.rstrip('/') + "/r/" + token

        print("\nFINAL MASKED LINK:\n")
        print("+" + "-"*(len(final)+6) + "+")
        print("|  " + final + "  |")
        print("+" + "-"*(len(final)+6) + "+")
        print("\nShare this link.")
        input("\nPress Enter…")
        return

# ============================
# MAIN MENU + STARTUP
# ============================
def main():
    os.system('clear')
    banner()

    print("Starting NGROK on port 8000…")
    public = None
    try:
        public = ngrok.connect(8000).public_url
    except:
        print("Auto ngrok failed. Start manually:\n    ngrok http 8000")
        public = input("Paste ngrok URL: ").strip()

    print("\nNGROK URL:", public)

    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=8000, debug=False, use_reloader=False)).start()

    while True:
        os.system('clear')
        banner()
        print("NGROK:", public)
        print("\n1) Create Masked URL")
        print("2) Exit")
        ch = input("> ").strip()

        if ch == "1":
            mask_flow(public)
        elif ch == "2":
            os._exit(0)
        else:
            input("Invalid. Press Enter…")


if __name__ == "__main__":
    main()
