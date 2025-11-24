from flask import Flask, request, render_template_string, redirect
import random
import string
import threading
import socket
import os
from pyngrok import ngrok
import time

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
   __  __   _____   _____   _   _   _____   __  __   _____   _____   _____
  |  \/  | |_   _| |_   _| | \ | | |_   _| |  \/  | |_   _| |_   _| |  __ \
  | \  / |   | |     | |   |  \| |   | |   | \  / |   | |     | |   | |__) |
  | |\/| |   | |     | |   | . ` |   | |   | |\/| |   | |     | |   |  ___/
  | |  | |  _| |_   _| |_  | |\  |  _| |_  | |  | |  _| |_   _| |_  | |
  |_|  |_| |_____| |_____| |_| \_| |_____| |_|  |_| |_____| |_____| |_|

          ██╗   ██╗███╗   ██╗██████╗ ██╗      ██████╗ ███████╗██████╗
          ██║   ██║████╗  ██║██╔══██╗██║     ██╔════╝ ██╔════╝██╔══██╗
          ██║   ██║██╔██╗ ██║██║  ██║██║     ██║  ███╗█████╗  ██████╔╝
          ██║   ██║██║╚██╗██║██║  ██║██║     ██║   ██║██╔══╝  ██╔══██╗
          ╚██████╔╝██║ ╚████║██████╔╝███████╗╚██████╔╝███████╗██║  ██║
           ╚═════╝ ╚═╝  ╚═══╝╚═════╝ ╚══════╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝

            URL Masking Tool (Version 3.0)
          Created by [Your Name Here]
    """
    print("\033[92m" + banner + "\033[0m")

def setup_ngrok():
    try:
        ngrok_tunnel = ngrok.connect(5000)
        public_url = ngrok_tunnel.public_url
        print(f"\n\033[92m[+]\033[0m Ngrok Tunnel Created: \033[96m{public_url}\033[0m")
        return public_url
    except Exception as e:
        print(f"\n\033[91m[-]\033[0m Failed to setup Ngrok: {e}")
        return None

def mask_url(public_url):
    clear_screen()
    display_banner()
    print("\n\033[92m[+]\033[0m Enter the Original URL (e.g., http://instagram.com):")
    original_url = input("\033[93m> \033[0m").strip()
    print("\n\033[92m[+]\033[0m Enter the Fake URL (e.g., http://youtube.com):")
    fake_url = input("\033[93m> \033[0m").strip()

    if not original_url.startswith(('http://', 'https://')):
        original_url = 'http://' + original_url
    if not fake_url.startswith(('http://', 'https://')):
        fake_url = 'http://' + fake_url

    random_path = generate_random_string()
    fake_domain = fake_url.split('//')[1].split('/')[0]
    masked_url = f"{public_url}/{fake_domain}?path={random_path}"

    url_mapping[random_path] = original_url

    print(f"\n\033[92m[+]\033[0m Your Public Masked URL: \033[96m{masked_url}\033[0m")
    print("\033[92m[+]\033[0m This URL will show the fake URL but redirect to the original URL.")
    input("\n\033[92m[+]\033[0m Press Enter to continue...")

@app.route("/")
def home():
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>URL Masking Tool</title>
    <style>
        body {
            font-family: 'Courier New', monospace;
            background-color: #0f0f0f;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            color: #00ff00;
        }
        .container {
            background-color: #1a1a1a;
            padding: 30px;
            border-radius: 5px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.5);
            text-align: center;
            max-width: 500px;
            width: 100%;
            border: 1px solid #00ff00;
        }
        h1 {
            color: #00ff00;
            text-shadow: 0 0 5px #00ff00;
        }
        p {
            color: #aaaaaa;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>URL MASKING TOOL</h1>
        <p>Use the terminal interface to mask URLs.</p>
    </div>
</body>
</html>
''')

@app.route('/<path:fake_domain>', methods=['GET'])
def fake_page(fake_domain):
    path = request.args.get('path')
    if path and path in url_mapping:
        return render_template_string(f'''
<!DOCTYPE html>
<html>
<head>
    <title>{fake_domain}</title>
    <meta http-equiv="refresh" content="2; url={url_mapping[path]}">
    <style>
        body {{
            font-family: 'Courier New', monospace;
            background-color: #0f0f0f;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            color: #00ff00;
        }}
        .fake-page {{
            text-align: center;
        }}
        .loader h1 {{
            color: #00ff00;
            text-shadow: 0 0 5px #00ff00;
        }}
        .loader p {{
            color: #aaaaaa;
        }}
    </style>
</head>
<body>
    <div class="fake-page">
        <div class="loader">
            <h1>Redirecting to {fake_domain}...</h1>
            <p>Please wait...</p>
        </div>
    </div>
</body>
</html>
''')
    return "URL not found or expired.", 404

def main_menu(public_url):
    while True:
        clear_screen()
        display_banner()
        print(f"\n\033[92m[+]\033[0m Your Ngrok URL: \033[96m{public_url}\033[0m")
        print("\n\033[92m[+]\033[0m Select an option:")
        print("\033[93m[01]\033[0m Mask a URL")
        print("\033[93m[02]\033[0m Exit")
        choice = input("\n\033[93m> \033[0m").strip()

        if choice == "1":
            mask_url(public_url)
        elif choice == "2":
            print("\n\033[92m[+]\033[0m Exiting...")
            exit(0)
        else:
            print("\n\033[91m[-]\033[0m Invalid option. Try again.")
            time.sleep(1)

if __name__ == "__main__":
    print("\033[92m[+]\033[0m Setting up Ngrok...")
    public_url = setup_ngrok()
    if not public_url:
        print("\033[91m[-]\033[0m Could not setup Ngrok. Falling back to local IP.")
        public_url = f"http://{get_local_ip()}:5000"

    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=5000, debug=False)).start()
    main_menu(public_url)
