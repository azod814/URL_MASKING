# url_masker_updated.py
from flask import Flask, request, render_template_string
import random, string, threading, socket, os, csv, time
from pyngrok import ngrok

app = Flask(__name__)
url_mapping = {}
log_file = "clicks_log.csv"

def display_banner():
    banner = r"""
              █    ██  ██▀███   ██▓                          
             ██  ▓██▒▓██ ▒ ██▒▓██▒                          
            ▓██  ▒██░▓██ ░▄█ ▒▒██░                          
            ▓▓█  ░██░▒██▀▀█▄  ▒██░                          
            ▒▒█████▓ ░██▓ ▒██▒░██████▒                      
            ░▒▓▒ ▒ ▒ ░ ▒▓ ░▒▓░░ ▒░▓  ░                      
            ░░▒░ ░ ░   ░▒ ░ ▒░░ ░ ▒  ░                      
             ░░░ ░ ░   ░░   ░   ░ ░                         
               ░        ░         ░  ░                      
                                                            
 ███▄ ▄███▓ ▄▄▄        ██████  ██ ▄█▀ ██▓ ███▄    █   ▄████ 
▓██▒▀█▀ ██▒▒████▄    ▒██    ▒  ██▄█▒ ▓██▒ ██ ▀█   █  ██▒ ▀█▒
▓██    ▓██░▒██  ▀█▄  ░ ▓██▄   ▓███▄░ ▒██▒▓██  ▀█ ██▒▒██░▄▄▄░
▒██    ▒██ ░██▄▄▄▄██   ▒   ██▒▓██ █▄ ░██░▓██▒  ▐▌██▒░▓█  ██▓
▒██▒   ░██▒ ▓█   ▓██▒▒██████▒▒▒██▒ █▄░██░▒██░   ▓██░░▒▓███▀▒
░ ▒░   ░  ░ ▒▒   ▓▒█░▒ ▒▓▒ ▒ ░▒ ▒▒ ▓▒░▓  ░ ▒░   ▒ ▒  ░▒   ▒ 
░  ░      ░  ▒   ▒▒ ░░ ░▒  ░ ░░ ░▒ ▒░ ▒ ░░ ░░   ░ ▒░  ░   ░ 
░      ░     ░   ▒   ░  ░  ░  ░ ░░ ░  ▒ ░   ░   ░ ░ ░ ░   ░ 
       ░         ░  ░      ░  ░  ░    ░           ░       ░ 
            URL Masking Tool (Version 3.0)
          Created by [Your Name Here]
    """
    print("\033[92m" + banner + "\033[0m")

def generate_random_string(length=8):
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(length))

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
    except Exception:
        local_ip = "127.0.0.1"
    finally:
        s.close()
    return local_ip

# ---------- simple domain utilities ----------
def domain_from_url(url):
    try:
        if "://" in url:
            url = url.split("://",1)[1]
        domain = url.split("/")[0]
        domain = domain.split(":")[0]
        return domain.lower()
    except:
        return url.lower()

def domain_resolves(domain):
    try:
        socket.gethostbyname(domain)
        return True
    except:
        return False

# ----------------- suggestion helpers -----------------
HOMOGLYPH_MAP = {
    'a': ['@','4'], 'b':['8'], 'e':['3'], 'i':['1','!'],
    'l':['1','|'],'o':['0'],'s':['5','$'],'t':['7']
}
COMMON_PREFIXES = ['my','the','go','get','try']
COMMON_SUFFIXES = ['app','site','now','hub','online']

def homoglyph_variants(s):
    out = set()
    for i,ch in enumerate(s):
        if ch in HOMOGLYPH_MAP:
            for rep in HOMOGLYPH_MAP[ch]:
                out.add(s[:i] + rep + s[i+1:])
    return out

def insert_variants(s):
    out = set()
    for i in range(len(s)):
        out.add(s[:i] + '-' + s[i:])
        out.add(s[:i] + s[i] + s[i:])
    for p in COMMON_PREFIXES:
        out.add(p + s)
    for suf in COMMON_SUFFIXES:
        out.add(s + suf)
    for i in range(len(s)-1):
        lst = list(s)
        lst[i], lst[i+1] = lst[i+1], lst[i]
        out.add(''.join(lst))
    return out

def generate_suggestions_from(base_domain, max_s=8):
    od = base_domain
    if od.startswith("www."): od = od[4:]
    sld = od.split(".")[0]
    cand = set()
    cand.update(homoglyph_variants(sld))
    cand.update(insert_variants(sld))
    for _ in range(4):
        cand.add(sld + generate_random_string(2))
    final = []
    for c in list(cand)[:max_s*3]:
        final.append(c + ".com")
    # check DNS quickly
    checked = []
    for d in final:
        checked.append((d, domain_resolves(d)))
    # prefer non-resolving (available)
    checked.sort(key=lambda x: (x[1], x[0]))  # False (not resolving) first
    return checked[:max_s]

# ---------------- logging ----------------
def ensure_log_header():
    if not os.path.exists(log_file):
        with open(log_file,'w',newline='') as f:
            csv.writer(f).writerow(["timestamp","token","remote_addr","original_url"])

def log_click(token, remote_addr):
    ensure_log_header()
    with open(log_file,'a',newline='') as f:
        csv.writer(f).writerow([time.strftime("%Y-%m-%d %H:%M:%S"), token, remote_addr, url_mapping[token]["original"]])

# --------------- flask loader & redirect ---------------
@app.route('/r/<token>')
def redirect_token(token):
    if token not in url_mapping:
        return "URL not found or expired.", 404
    original = url_mapping[token]["original"]
    try:
        log_click(token, request.remote_addr)
    except:
        pass
    html = '''
    <!doctype html>
    <html><head><meta charset="utf-8"><title>Loading...</title>
    <style>body{display:flex;align-items:center;justify-content:center;height:100vh;margin:0;font-family:Arial;background:#fff}
    .loader{width:48px;height:48px;border:5px solid rgba(0,0,0,0.1);border-radius:50%;border-top-color:#333;animation:spin 1s linear infinite}
    @keyframes spin{to{transform:rotate(360deg)}}
    </style>
    <script>setTimeout(function(){window.location.replace("{{ original }}");},1300);</script>
    </head><body><div class="loader"></div></body></html>
    '''
    return render_template_string(html, original=original)

# ---------------- ngrok setup ----------------
def setup_ngrok(port=5000):
    try:
        ng = ngrok.connect(port)
        public = ng.public_url
        print(f"\n\033[92m[+]\033[0m Ngrok Tunnel Created: \033[96m{public}\033[0m")
        return public
    except Exception as e:
        print(f"\n\033[91m[-]\033[0m Ngrok setup failed: {e}")
        return None

# ----------------- main mask flow (updated) -----------------
def mask_flow(public_url):
    os.system('cls' if os.name=='nt' else 'clear')
    display_banner()
    print(f"\n\033[92m[+]\033[0m Ngrok base: \033[96m{public_url}\033[0m\n")
    orig = input("\033[93mEnter ORIGINAL full URL (e.g., https://instagram.com/p/xyz): \033[0m").strip()
    if not orig:
        print("No URL provided.")
        input("Press Enter to continue...")
        return
    # Ask user if they want to manually enter a fake/cosmetic domain
    manual = input("\n\033[93mDo you want to ENTER your own FAKE domain to display? (y/n): \033[0m").strip().lower()
    fake_choice = None
    if manual == 'y':
        fake_candidate = input("\033[93mEnter your desired fake domain (example: instagram.com): \033[0m").strip().lower()
        if fake_candidate:
            fake_choice = fake_candidate
            if domain_resolves(fake_choice):
                print(f"\n\033[91m[!]\033[0m Warning: {fake_choice} resolves (likely registered). If you want a non-registered cosmetic name choose another.")
            else:
                print(f"\n\033[92m[+]\033[0m Note: {fake_choice} does not resolve (cosmetic). To make it live register & point DNS.")
    else:
        # generate suggestions from original domain
        dom = domain_from_url(orig)
        print(f"\nAnalyzing domain '{dom}' and generating suggestions...")
        suggestions = generate_suggestions_from(dom, max_s=8)
        print("\nSuggestions (domain -> RESOLVES?):")
        for i,(d,r) in enumerate(suggestions, start=1):
            status = "TAKEN" if r else "AVAILABLE/NOT-RESOLVING"
            print(f"[{i}] {d}   -> {status}")
        ch = input("\nChoose index (1-8) to use as cosmetic fake domain, or press Enter to skip: ").strip()
        if ch.isdigit():
            idx = int(ch)-1
            if 0 <= idx < len(suggestions):
                fake_choice = suggestions[idx][0]
                if suggestions[idx][1]:
                    print(f"\n\033[91m[!]\033[0m Note: {fake_choice} resolves (likely registered).")
                else:
                    print(f"\n\033[92m[+]\033[0m Selected {fake_choice} (not resolving).")
    # create token + mapping
    token = generate_random_string(10)
    url_mapping[token] = {"original": orig, "created_at": time.time(), "fake_display": fake_choice}
    working_link = f"{public_url}/r/{token}"
    # Highlighted output box (green)
    box_line = "+" + "-"*(len(working_link)+6) + "+"
    print("\n\n\033[1mFinal working masked link (copy & share this):\033[0m\n")
    print("\033[1;32m" + box_line)
    print("|  " + working_link + "  |")
    print(box_line + "\033[0m")
    if fake_choice:
        print(f"\n\033[93mCosmetic fake domain (text label):\033[0m {fake_choice}")
        print("\033[90mNote: To make the cosmetic domain actually resolve in browser, register it & point DNS to your host/ngrok.\033[0m")
    print("\n\033[96mTip:\033[0m Use this working link on any device while ngrok tunnel is active. Clicks logged in clicks_log.csv")
    input("\nPress Enter to continue...")

def main_menu(public_url):
    while True:
        os.system('cls' if os.name=='nt' else 'clear')
        display_banner()
        print(f"\n\033[92m[+]\033[0m Ngrok: \033[96m{public_url}\033[0m")
        print("\n1) Mask a URL")
        print("2) Show current mappings")
        print("3) Exit")
        ch = input("\nChoose: ").strip()
        if ch == '1':
            mask_flow(public_url)
        elif ch == '2':
            print("\nCurrent mappings (token -> original -> fake_display):\n")
            for t,info in url_mapping.items():
                print(f"{t} -> {info['original']}   (fake: {info.get('fake_display')})")
            input("\nPress Enter to continue...")
        elif ch == '3':
            print("Exiting.")
            os._exit(0)
        else:
            input("Invalid. Press Enter...")

if __name__ == "__main__":
    display_banner()
    print("\nStarting ngrok + Flask...")
    public_url = setup_ngrok(port=5000)
    if not public_url:
        print("\nFalling back to local IP.")
        public_url = f"http://{get_local_ip()}:5000"
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)).start()
    ensure_log_header()
    main_menu(public_url)
