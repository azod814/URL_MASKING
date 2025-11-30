from flask import Flask, request, render_template_string
import random, string, threading, socket, os, csv, time
from pyngrok import ngrok

app = Flask(__name__)
url_mapping = {}
log_file = "clicks_log.csv"


# =============================
# COLOR UTIL
# =============================
class C:
    G = "\033[92m"
    B = "\033[94m"
    Y = "\033[93m"
    R = "\033[91m"
    W = "\033[97m"
    C = "\033[96m"
    P = "\033[95m"
    END = "\033[0m"
    BOLD = "\033[1m"


# =============================
# BANNER
# =============================
def banner():
    print(C.C + C.BOLD + r"""
 ███╗   ███╗ █████╗ ███████╗██╗  ██╗███████╗██╗  ██╗███████╗██████╗ 
 ████╗ ████║██╔══██╗██╔════╝██║ ██╔╝██╔════╝██║ ██╔╝██╔════╝██╔══██╗
 ██╔████╔██║███████║███████╗█████╔╝ █████╗  █████╔╝ █████╗  ██████╔╝
 ██║╚██╔╝██║██╔══██║╚════██║██╔═██╗ ██╔══╝  ██╔═██╗ ██╔══╝  ██╔══██╗
 ██║ ╚═╝ ██║██║  ██║███████║██║  ██╗███████╗██║  ██╗███████╗██║  ██║
 ╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝

                   SAFE MASKED URL TOOL — PREMIUM 2.0
--------------------------------------------------------------------
""" + C.END)


# =============================
# UTIL
# =============================
def gen_token(n=10):
    return "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(n))


def domain_from_url(url):
    if "://" in url:
        url = url.split("://")[1]
    return url.split("/")[0].split(":")[0]


def domain_resolves(d):
    try:
        socket.gethostbyname(d)
        return True
    except:
        return False


def rand_suffix(n=3):
    return "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(n))


def suggest_fake_names(base_sld, max_s=6):
    sld = base_sld
    cand = set()

    for i in range(len(sld)):
        cand.add(sld[:i] + '-' + sld[i:])
        cand.add(sld + rand_suffix(2))

    suggestions = []
    for c in list(cand):
        dom = c + ".com"
        suggestions.append((dom, domain_resolves(dom)))
        if len(suggestions) >= max_s:
            break

    suggestions.sort(key=lambda x: (x[1], x[0]))
    return suggestions[:max_s]


# =============================
# FLASK LANDING PAGE UI (improved)
# =============================
@app.route('/r/<token>')
def landing(token):
    info = url_mapping.get(token)
    if not info:
        return "Not found", 404

    original = info["original"]
    label = info.get("label", "")

    html = f'''
    <html>
    <head>
        <title>Opening…</title>
        <meta http-equiv="refresh" content="1.5; url={original}">
        <style>
            body {{
                background:#0f172a;
                color:white;
                font-family:Arial;
                display:flex;
                justify-content:center;
                align-items:center;
                height:100vh;
            }}
            .card {{
                background:#1e293b;
                padding:30px;
                border-radius:12px;
                width:330px;
                text-align:center;
                box-shadow:0 10px 35px rgba(0,0,0,0.45);
            }}
            .label {{
                font-size:28px;
                font-weight:bold;
                color:#22c55e;
                margin-bottom:10px;
            }}
            .loader {{
                width:45px;
                height:45px;
                border:5px solid rgba(255,255,255,0.25);
                border-top-color:#fff;
                border-radius:50%;
                margin:15px auto;
                animation:spin 1s linear infinite;
            }}
            @keyframes spin {{
                to {{ transform:rotate(360deg); }}
            }}
            .orig {{
                background:#d1fae5;
                color:#065f46;
                padding:7px 10px;
                border-radius:6px;
                font-weight:bold;
                margin-top:12px;
                display:inline-block;
            }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="label">{label}</div>
            <div>Opening… please wait</div>
            <div class="loader"></div>
            <div class="orig">{original}</div>
        </div>
    </body>
    </html>
    '''

    return html


# =============================
# MASK FLOW
# =============================
def mask_flow(public_url):
    while True:
        os.system('clear')
        banner()

        print(C.Y + "Enter ORIGINAL URL:" + C.END)
        original = input(C.C + "> " + C.END).strip()

        print(C.Y + "\nEnter FAKE display label/domain:" + C.END)
        fake_enter = input(C.C + "> " + C.END).strip()

        sld = domain_from_url(fake_enter)
        suggestions = suggest_fake_names(sld, 5)

        print(C.G + "\nSuggestions:\n" + C.END)
        for i, (d, r) in enumerate(suggestions, start=1):
            print(f" {C.C}[{i}]{C.END} {d}  ({'TAKEN' if r else C.G+'FREE'+C.END})")
        print(C.C + " [0]" + C.END + " Use exact input")

        sel = input(C.Y + "Choose: " + C.END).strip()

        if sel.isdigit():
            sel = int(sel)
            if sel == 0:
                fake_label = fake_enter
            elif 1 <= sel <= len(suggestions):
                fake_label = suggestions[sel-1][0]
            else:
                fake_label = fake_enter
        else:
            fake_label = fake_enter

        print(C.G + "\nOriginal:" + C.END, original)
        print(C.G + "Fake label:" + C.END, fake_label)

        confirm = input(C.Y + "Confirm? (y/n): " + C.END).lower()
        if confirm != "y":
            continue

        token = gen_token()
        url_mapping[token] = {"original": original, "label": fake_label}

        final_url = public_url.rstrip('/') + "/r/" + token

        print(C.G + C.BOLD + "\nYOUR FINAL MASKED URL:\n" + C.END)
        box = "+" + "-"*(len(final_url)+6) + "+"
        print(C.C + box)
        print("|  " + final_url + "  |")
        print(box + C.END)

        input(C.Y + "\nPress Enter…" + C.END)
        return


# =============================
# MAIN
# =============================
def main():
    os.system("clear")
    banner()

    print(C.G + "Starting ngrok on port 8000…" + C.END)

    try:
        public = ngrok.connect(8000).public_url
    except:
        print(C.R + "Auto ngrok failed!" + C.END)
        public = input(C.Y + "Paste your ngrok URL: " + C.END)

    print(C.G + "\nNGROK: " + C.C + public + C.END)

    threading.Thread(target=lambda: app.run(
        host="0.0.0.0", port=8000, debug=False, use_reloader=False
    )).start()

    while True:
        os.system('clear')
        banner()
        print(C.G + "NGROK: " + C.C + public + C.END)
        print("\n1) Create Masked URL")
        print("2) Exit")

        ch = input("> ").strip()
        if ch == "1":
            mask_flow(public)
        elif ch == "2":
            os._exit(0)


if __name__ == "__main__":
    main()
