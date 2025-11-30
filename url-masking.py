# url_masker_full.py
from flask import Flask, request, render_template_string
import random, string, threading, socket, os, csv, time
from pyngrok import ngrok

app = Flask(__name__)
url_mapping = {}   # token -> {original, created_at, fake_display}
log_file = "clicks_log.csv"

# ---------------- Banner (as requested, not removed) ----------------
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
# --------------------------------------------------------------------

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

# ------------------ Fake-domain generation logic --------------------
HOMOGLYPH_MAP = {
    'a': ['@', '4'],
    'b': ['8'],
    'e': ['3'],
    'i': ['1','!'],
    'l': ['1','|'],
    'o': ['0'],
    's': ['5','$'],
    't': ['7'],
    'c': ['<','('],
    'g': ['9']
}

COMMON_PREFIXES = ['my', 'the', 'go', 'get', 'try', 'online']
COMMON_SUFFIXES = ['app','site','online','hub','now','info']

def domain_from_url(url):
    # crude extract domain (without scheme and path)
    try:
        if "://" in url:
            url = url.split("://",1)[1]
        domain = url.split("/")[0]
        # remove port if any
        domain = domain.split(":")[0]
        return domain.lower()
    except:
        return url.lower()

def homoglyph_variants(domain):
    # replace some characters with homoglyphs
    base = domain
    variants = set()
    for i, ch in enumerate(base):
        if ch in HOMOGLYPH_MAP:
            for rep in HOMOGLYPH_MAP[ch]:
                v = base[:i] + rep + base[i+1:]
                variants.add(v)
    return variants

def insert_remove_variants(domain):
    variants = set()
    # insert random char at random positions (letters/numbers)
    for i in range(len(domain)):
        variants.add(domain[:i] + '-' + domain[i:])  # add dash
        variants.add(domain[:i] + domain[i] + domain[i:])  # duplicate char
    # add prefix/suffix
    for p in COMMON_PREFIXES:
        variants.add(p + domain)
    for s in COMMON_SUFFIXES:
        variants.add(domain + s)
    # swap adjacent
    for i in range(len(domain)-1):
        lst = list(domain)
        lst[i], lst[i+1] = lst[i+1], lst[i]
        variants.add(''.join(lst))
    return variants

def generate_suggestions(original_domain, max_suggestions=10):
    # remove www.
    od = original_domain
    if od.startswith("www."):
        od = od[4:]
    od = od.split(".")[0]  # work on SLD only
    candidates = set()
    candidates.update(homoglyph_variants(od))
    candidates.update(insert_remove_variants(od))
    # combine with suffix .com
    final = []
    for c in candidates:
        final.append(c + ".com")
        final.append("www." + c + ".com")
    # add few random short ones
    for _ in range(5):
        final.append(od + generate_random_string(2) + ".com")
    # dedupe and limit
    final = list(dict.fromkeys(final))
    # Check DNS to see if it resolves (naive availability check)
    checked = []
    for dom in final:
        if len(checked) >= max_suggestions*3:
            break
        available = not domain_resolves(dom)
        checked.append( (dom, available) )
    # prefer not-resolving ones first
    checked.sort(key=lambda x: (not x[1], x[0]))  # True available => False sorts first; invert
    suggestions = checked[:max_suggestions]
    # Return as list of dicts
    return [{"domain": d, "resolves": (not a)} for d,a in suggestions]

def domain_resolves(domain):
    try:
        # try to resolve; if resolves, consider it taken (approx)
        socket.gethostbyname(domain)
        return True
    except Exception:
        return False
# --------------------------------------------------------------------

# ---------------- Logging clicks ----------------
def ensure_log_header():
    if not os.path.exists(log_file):
        with open(log_file, 'w', newline='') as f:
            w = csv.writer(f)
            w.writerow(["timestamp","token","remote_addr","original_url"])

def log_click(token, remote_addr):
    ensure_log_header()
    with open(log_file, 'a', newline='') as f:
        w = csv.writer(f)
        w.writerow([time.strftime("%Y-%m-%d %H:%M:%S"), token, remote_addr, url_mapping[token]["original"]])

# --------------- Flask endpoint for redirect + loader --------------
@app.route('/r/<token>')
def redirect_token(token):
    if token not in url_mapping:
        return "URL not found or expired.", 404
    original = url_mapping[token]["original"]
    # log click
    try:
        log_click(token, request.remote_addr)
    except:
        pass
    html = '''
    <!doctype html>
    <html>
      <head>
        <meta charset="utf-8">
        <title>Loading...</title>
        <style>
          body{display:flex;align-items:center;justify-content:center;height:100vh;margin:0;font-family:Arial;background:#fff;}
          .loader{width:48px;height:48px;border:5px solid rgba(0,0,0,0.1);border-radius:50%;border-top-color:#333;animation:spin 1s linear infinite;}
          @keyframes spin{to{transform:rotate(360deg)}}
        </style>
        <script>
          setTimeout(function(){
            window.location.replace("{{ original }}");
          }, 1300);
        </script>
      </head>
      <body>
        <div class="loader"></div>
      </body>
    </html>
    '''
    return render_template_string(html, original=original)
# --------------------------------------------------------------------

def setup_ngrok():
    try:
        ngrok_tunnel = ngrok.connect(5000)
        public_url = ngrok_tunnel.public_url
        print(f"\n\033[92m[+]\033[0m Ngrok Tunnel Created: \033[96m{public_url}\033[0m")
        return public_url
    except Exception as e:
        print(f"\n\033[91m[-]\033[0m Failed to setup Ngrok: {e}")
        return None

def mask_flow(public_url):
    os.system('cls' if os.name == 'nt' else 'clear')
    display_banner()
    print(f"\n\033[92m[+]\033[0m Ngrok base URL: \033[96m{public_url}\033[0m\n")
    orig = input("\033[93mEnter original full URL (e.g., https://instagram.com/some/path): \033[0m").strip()
    if not orig:
        print("No URL entered.")
        input("Press Enter to continue...")
        return
    domain = domain_from_url(orig)
    print(f"\nAnalyzing domain: {domain} ...")
    suggestions = generate_suggestions(domain, max_suggestions=8)
    print("\nSuggested fake domains (DNS-resolve = True means domain resolves -> likely registered):\n")
    for i,s in enumerate(suggestions, start=1):
        flag = "TAKEN" if s["resolves"] else "AVAILABLE/NOT-RESOLVING"
        print(f"[{i}] {s['domain']}   -> {flag}")
    choice = input("\nChoose a fake domain index (1-8) or press Enter to skip and just create masked link: ").strip()
    fake_choice = None
    if choice.isdigit():
        idx = int(choice)-1
        if 0 <= idx < len(suggestions):
            fake_choice = suggestions[idx]["domain"]
    print("\nNow creating working masked link (this will use your ngrok domain and a token endpoint)...")
    token = generate_random_string(10)
    url_mapping[token] = {"original": orig, "created_at": time.time(), "fake_display": fake_choice}
    working_link = f"{public_url}/r/{token}"
    print("\n--- OUTPUT ---")
    print(f"Working masked link to share (this will redirect via loader):\n{working_link}")
    if fake_choice:
        print(f"\nCosmetic fake domain you selected (to show people as text): {fake_choice}")
        print("Note: To make the cosmetic domain actually resolve in browser, YOU MUST register it and point its DNS to your server/ngrok.")
    else:
        print("\nNo cosmetic fake selected. You can still share the working link above.")
    input("\nPress Enter to continue...")

def main_menu(public_url):
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
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
                fd = info.get("fake_display") or ""
                print(f"{t} -> {info['original']}  (fake: {fd})")
            input("\nPress Enter to continue...")
        elif ch == '3':
            print("Exiting.")
            os._exit(0)
        else:
            input("Invalid. Press Enter...")

if __name__ == "__main__":
    display_banner()
    print("\nStarting ngrok and Flask...")
    public_url = setup_ngrok()
    if not public_url:
        print("Falling back to local IP.")
        public_url = f"http://{get_local_ip()}:5000"
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)).start()
    ensure_log_header()
    main_menu(public_url)
