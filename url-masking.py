from flask import Flask, request, render_template_string
import random, string, threading, socket, os, csv, time
from pyngrok import ngrok

app = Flask(__name__)
url_mapping = {}
log_file = "clicks_log.csv"

class C:
    G = "\033[92m"
    B = "\033[94m"
    Y = "\033[93m"
    R = "\033[91m"
    W = "\033[97m"
    C_ = "\033[96m"
    P = "\033[95m"
    END = "\033[0m"
    BOLD = "\033[1m"

def banner():
    print(C.C_ + C.BOLD + r"""
 ███╗   ███╗ █████╗ ███████╗██╗  ██╗███████╗██╗  ██╗███████╗██████╗ 
 ████╗ ████║██╔══██╗██╔════╝██║ ██╔╝██╔════╝██║ ██╔╝██╔════╝██╔══██╗
 ██╔████╔██║███████║███████╗█████╔╝ █████╗  █████╔╝ █████╗  ██████╔╝
 ██║╚██╔╝██║██╔══██║╚════██║██╔═██╗ ██╔══╝  ██╔═██╗ ██╔══╝  ██╔══██╗
 ██║ ╚═╝ ██║██║  ██║███████║██║  ██╗███████╗██║  ██╗███████╗██║  ██║
 ╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝

                 URL AWARENESS MASKER (Port 8000)
--------------------------------------------------------------------
""" + C.END)

def gen_token(n=10):
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(n))

def domain_from_url(url):
    if "://" in url:
        url = url.split("://", 1)[1]
    return url.split("/")[0].split(":")[0].lower()

def domain_resolves(d):
    try:
        socket.gethostbyname(d)
        return True
    except:
        return False

def rand_suffix(n=3):
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(n))

def suggest_fake_names(base_text, max_s=6):
    base = base_text
    if "://" in base:
        base = base.split("://",1)[1]
    base = base.split("/")[0]
    base = base.replace("www.", "")
    sld = base.split(".")[0]
    if not sld:
        sld = "site"
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

@app.route('/r/<token>')
def landing(token):
    info = url_mapping.get(token)
    if not info:
        return "Not found", 404
    original = info["original"]
    label = info.get("label") or ""
    try:
        log_click(token, request.remote_addr)
    except:
        pass
    html = """
    <!doctype html>
    <html>
      <head>
        <meta charset="utf-8">
        <title>URL Awareness Demo</title>
        <meta name="viewport" content="width=device-width,initial-scale=1">
        <style>
          body {{
            margin:0;
            background:#020617;
            font-family:system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            color:#e5e7eb;
            display:flex;
            align-items:center;
            justify-content:center;
            min-height:100vh;
          }}
          .card {{
            background:radial-gradient(circle at top,#1d283a,#020617 55%);
            padding:32px 28px;
            border-radius:18px;
            box-shadow:0 20px 60px rgba(0,0,0,0.65);
            max-width:480px;
            width:90%;
            text-align:center;
            border:1px solid rgba(148,163,184,0.35);
          }}
          .badge {{
            display:inline-flex;
            align-items:center;
            gap:6px;
            font-size:11px;
            text-transform:uppercase;
            letter-spacing:0.12em;
            padding:4px 10px;
            border-radius:999px;
            background:rgba(15,118,110,0.12);
            color:#5eead4;
            margin-bottom:12px;
          }}
          .badge-dot {{
            width:7px;
            height:7px;
            border-radius:999px;
            background:#22c55e;
          }}
          .fake {{
            font-size:28px;
            font-weight:800;
            margin-bottom:6px;
            color:#22c55e;
            word-break:break-all;
          }}
          .subtitle {{
            font-size:13px;
            color:#9ca3af;
            margin-bottom:18px;
          }}
          .loader {{
            width:46px;
            height:46px;
            border-radius:999px;
            border:5px solid rgba(148,163,184,0.35);
            border-top-color:#e5e7eb;
            margin:0 auto 16px auto;
            animation:spin 1s linear infinite;
          }}
          @keyframes spin {{ to {{ transform:rotate(360deg); }} }}
          .original-box {{
            background:rgba(15,23,42,0.9);
            border-radius:10px;
            padding:10px 12px;
            text-align:left;
            border:1px dashed rgba(148,163,184,0.6);
            font-size:12px;
            color:#e5e7eb;
            word-break:break-all;
          }}
          .label-small {{
            font-size:11px;
            text-transform:uppercase;
            letter-spacing:0.16em;
            color:#64748b;
            margin-bottom:4px;
          }}
          .note {{
            margin-top:12px;
            font-size:11px;
            color:#6b7280;
          }}
          .note span {{
            color:#f97316;
            font-weight:600;
          }}
        </style>
        <meta http-equiv="refresh" content="1.6; url={{ original }}">
      </head>
      <body>
        <div class="card">
          <div class="badge">
            <div class="badge-dot"></div>
            URL awareness demo
          </div>
          <div class="fake">{{ label }}</div>
          <div class="subtitle">This is what the link looked like… but it actually opens the URL below.</div>
          <div class="loader"></div>
          <div class="label-small">Actual destination</div>
          <div class="original-box">{{ original }}</div>
          <div class="note">
            Always double-check the real domain before entering passwords. 
            <span>This page will now redirect safely.</span>
          </div>
        </div>
      </body>
    </html>
    """
    return render_template_string(html, original=original, label=label)

def mask_flow(public_url):
    while True:
        os.system('clear')
        banner()
        print(C.Y + "Step 1 — Enter ORIGINAL URL (where user will really go):" + C.END)
        original = input(C.C_ + "> " + C.END).strip()
        if not original:
            input(C.R + "Empty URL. Press Enter to retry…" + C.END)
            continue

        print()
        print(C.Y + "Step 2 — Enter FAKE-style text (what the link looked like):" + C.END)
        fake_input = input(C.C_ + "> " + C.END).strip()
        if not fake_input:
            fake_input = "example.com"

        print()
        print(C.Y + "Step 3 — Generating suggestions based on your fake input…" + C.END)
        suggestions = suggest_fake_names(fake_input, max_s=5)
        print()
        print(C.G + "Suggestions (for display only, NOT real domains):" + C.END)
        for i, (d, r) in enumerate(suggestions, start=1):
            status = (C.R + "TAKEN" + C.END) if r else (C.G + "FREE" + C.END)
            print(f"  {C.C_}[{i}]{C.END} {d}   {status}")
        print(f"  {C.C_}[0]{C.END} Use exactly what you typed: {fake_input}")

        choice = input(C.Y + f"\nChoose which label to SHOW on the awareness page (0-{len(suggestions)}): " + C.END).strip()
        if choice.isdigit():
            idx = int(choice)
            if idx == 0:
                final_label = fake_input
            elif 1 <= idx <= len(suggestions):
                final_label = suggestions[idx-1][0]
            else:
                final_label = fake_input
        else:
            final_label = fake_input

        print()
        print(C.G + "Summary:" + C.END)
        print("  " + C.Y + "Original (real destination):" + C.END, original)
        print("  " + C.Y + "Fake-looking label to show:" + C.END, final_label)
        conf = input(C.Y + "\nCreate awareness link with this config? (y/n): " + C.END).strip().lower()
        if conf != "y":
            input(C.R + "Cancelled. Press Enter to restart…" + C.END)
            continue

        token = gen_token(10)
        url_mapping[token] = {
            "original": original,
            "label": final_label,
            "created": time.time()
        }
        final_url = public_url.rstrip('/') + "/r/" + token

        box = "+" + "-"*(len(final_url)+6) + "+"
        print()
        print(C.G + C.BOLD + "Your FINAL awareness URL (share this):" + C.END)
        print(C.C_ + box)
        print("|  " + final_url + "  |")
        print(box + C.END)
        print()
        print(C.Y + "When someone opens this, they'll first see the fake label big," + C.END)
        print(C.Y + "and the REAL destination below, then it auto-redirects." + C.END)
        input("\nPress Enter to go back to menu…")
        return

def main_menu(public_url):
    while True:
        os.system('clear')
        banner()
        print(C.G + "Ngrok public URL: " + C.C_ + public_url + C.END)
        print()
        print("1) Create new awareness / masked URL")
        print("2) Show current mappings")
        print("3) Exit")
        choice = input(C.Y + "> " + C.END).strip()
        if choice == "1":
            mask_flow(public_url)
        elif choice == "2":
            os.system('clear')
            banner()
            if not url_mapping:
                print(C.R + "No mappings yet." + C.END)
            else:
                print(C.G + "Current mappings:\n" + C.END)
                for t, info in url_mapping.items():
                    print(f"Token: {t}")
                    print(f"  Original: {info['original']}")
                    print(f"  Label:    {info.get('label')}")
                    print()
            input("Press Enter to return…")
        elif choice == "3":
            os._exit(0)
        else:
            input(C.R + "Invalid option. Press Enter…" + C.END)

def start():
    os.system('clear')
    banner()
    print(C.G + "Starting ngrok on port 8000…" + C.END)
    try:
        tunnel = ngrok.connect(8000)
        public_url = tunnel.public_url
    except Exception as e:
        print(C.R + f"Auto ngrok failed: {e}" + C.END)
        public_url = input(C.Y + "Start `ngrok http 8000` manually, then paste the forwarding URL here: " + C.END).strip()
    print()
    print(C.G + "Using public URL: " + C.C_ + public_url + C.END)
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=8000, debug=False, use_reloader=False)).start()
    main_menu(public_url)

if __name__ == "__main__":
    start()
