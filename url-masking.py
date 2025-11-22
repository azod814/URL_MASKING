from flask import Flask, request, redirect, render_template_string
import random
import string
import os
import time
import threading

app = Flask(__name__)

# Temporary storage for URLs
url_mapping = {}

def generate_random_string(length=8):
    letters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(letters) for _ in range(length))

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def display_banner():
    banner = r"""
  __  __   _____   _____   _   _   _____   __  __
 |  \/  | |_   _| |_   _| | \ | | |_   _| |  \/  |
 | \  / |   | |     | |   |  \| |   | |   | \  / |
 | |\/| |   | |     | |   | . ` |   | |   | |\/| |
 | |  | |  _| |_   _| |_  | |\  |  _| |_  | |  | |
 |_|  |_| |_____| |_____| |_| \_| |_____| |_|  |_|

            URL Masking Tool (Version 1.0)
          Created by [Your Name Here]

[+] Select an option:
[01] Mask a URL
[02] Exit
    """
    print(banner)

def mask_url():
    clear_screen()
    display_banner()
    print("\n[+] Enter the Original URL (e.g., http://instagram.com):")
    original_url = input("> ").strip()
    print("\n[+] Enter the Fake URL (e.g., http://youtube.com):")
    fake_url = input("> ").strip()

    if not original_url.startswith(('http://', 'https://')):
        original_url = 'http://' + original_url
    if not fake_url.startswith(('http://', 'https://')):
        fake_url = 'http://' + fake_url

    random_path = generate_random_string()
    masked_url = f"http://{request.host.split(':')[0]}:5000/{random_path}"

    url_mapping[random_path] = {
        "original": original_url,
        "fake": fake_url
    }

    print(f"\n[+] Your Masked URL: {masked_url}")
    print("[+] This URL will show the fake URL but redirect to the original URL.")
    input("\n[+] Press Enter to continue...")

@app.route("/")
def home():
    return """
<!DOCTYPE html>
<html>
<head>
    <title>URL Masking Tool</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            margin-top: 50px;
            color: white;
            background-color: black;
        }
    </style>
</head>
<body>
    <h1>URL Masking Tool</h1>
    <p>Use the terminal interface to mask URLs.</p>
</body>
</html>
"""

@app.route("/<random_path>")
def redirect_to_original(random_path):
    url_data = url_mapping.get(random_path)
    if url_data:
        return f"""
<html>
<head>
    <title>Redirecting to {url_data['fake']}</title>
    <meta http-equiv="refresh" content="2; url={url_data['original']}">
    <style>
        body {{
            font-family: Arial, sans-serif;
            text-align: center;
            margin-top: 50px;
            background-color: black;
            color: #00ff00;
        }}
    </style>
</head>
<body>
    <h1>Redirecting to {url_data['fake']}...</h1>
    <p>You will be redirected to the original URL in 2 seconds.</p>
</body>
</html>
"""
    else:
        return "URL not found or expired.", 404

def main_menu():
    while True:
        clear_screen()
        display_banner()
        choice = input("\n> ").strip()

        if choice == "1":
            mask_url()
        elif choice == "2":
            print("\n[+] Exiting...")
            os._exit(0)
        else:
            print("\n[-] Invalid option. Try again.")
            time.sleep(1)

if __name__ == "__main__":
    # Start Flask server in a separate thread
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=5000, debug=False)).start()
    main_menu()
