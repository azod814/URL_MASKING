# save as masker.py
from flask import Flask, request, render_template_string, redirect, make_response, url_for
import random
import string
import threading
import socket
import os
from pyngrok import ngrok

app = Flask(__name__)
url_mapping = {}

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

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

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

def setup_ngrok():
    try:
        ngrok_tunnel = ngrok.connect(5000)
        public_url = ngrok_tunnel.public_url  # e.g. http://abcd-1234.ngrok.io
        print(f"\n\033[92m[+]\033[0m Ngrok Tunnel Created: \033[96m{public_url}\033[0m")
        return public_url
    except Exception as e:
        print(f"\n\033[91m[-]\033[0m Failed to setup Ngrok: {e}")
        return None

@app.route('/r/<token>')
def redirect_token(token):
    """
    Loader page then redirect to stored original URL (safe redirect).
    """
    original = url_mapping.get(token)
    if not original:
        return "URL not found or expired.", 404

    # Loader + JS redirect (replace so page is not kept in history)
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
          .info{position:absolute;top:20px;left:20px;font-size:13px;color:#666;}
        </style>
        <script>
          setTimeout(function(){
            window.location.replace("{{ original }}");
          }, 1500);
        </script>
      </head>
      <body>
        <div class="loader"></div>
      </body>
    </html>
    '''
    return render_template_string(html, original=original)

def mask_url_flow(public_url):
    clear_screen()
    display_banner()
    print(f"\n\033[92m[+]\033[0m Ngrok URL (share this base): \033[96m{public_url}\033[0m")
    print("\n\033[92m[+]\033[0m Enter the Original URL (target) (e.g., https://example.com/page):")
    original_url = input("\033[93m> \033[0m").strip()
    print("\n\033[92m[+]\033[0m Enter the Fake display URL text (optional, for showing to you only):")
    fake_display = input("\033[93m> \033[0m").strip()

    if not original_url.startswith(('http://','https://')):
        original_url = 'http://' + original_url

    token = generate_random_string(10)
    url_mapping[token] = original_url

    # Working masked link that actually forwards
    working_masked_link = f"{public_url}/r/{token}"

    # Cosmetic fake string (can't be used to actually spoof browser address)
    fake_shown = fake_display.rstrip('/') + '/' + token if fake_display else working_masked_link

    print("\n\033[92m[+]\033[0m Working Masked Link (share this):")
    print(f"\033[96m{working_masked_link}\033[0m")
    print("\n\033[93m[!]\033[0m NOTE: The address bar will show your ngrok domain. If you want the browser to display another domain")
    print("  you must own that domain and point it (CNAME) to your tunnel / use a custom domain feature.")
    print(f"\n  Display (cosmetic): {fake_shown}")
    input("\n\033[92m[+]\033[0m Press Enter to continue...")

def main_menu(public_url):
    while True:
        clear_screen()
        display_banner()
        print(f"\n\033[92m[+]\033[0m Your Ngrok URL: \033[96m{public_url}\033[0m")
        print("\n\033[92m[+]\033[0m Select an option:")
        print("\033[93m[01]\033[0m Mask a URL")
        print("\033[93m[02]\033[0m Exit")
        choice = input("\n\033[93m> \033[0m").strip()
        if choice in ("1","01"):
            mask_url_flow(public_url)
        elif choice in ("2","02"):
            print("\n\033[92m[+]\033[0m Exiting...")
            os._exit(0)
        else:
            print("\n\033[91m[-]\033[0m Invalid option. Try again.")
            input("\n\033[92m[+]\033[0m Press Enter to continue...")

if __name__ == "__main__":
    print("\033[92m[+]\033[0m Setting up Ngrok...")
    public_url = setup_ngrok()
    if not public_url:
        print("\033[91m[-]\033[0m Could not setup Ngrok. Falling back to local IP.")
        public_url = f"http://{get_local_ip()}:5000"

    # run flask in background thread (no reloader)
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)).start()
    main_menu(public_url)
