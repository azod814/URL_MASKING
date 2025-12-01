from flask import Flask, redirect, render_template_string
import threading
import requests
import random
import time
from colorama import Fore, Style, init

init(autoreset=True)

app = Flask(__name__)

# Store URL mappings
url_mapping = {}

# Loading page HTML
LOADING_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Redirecting...</title>
    <style>
        body {
            background: #000;
            color: #0f0;
            font-family: Arial, sans-serif;
            text-align: center;
            padding: 50px;
        }
        .box {
            border: 2px solid #0f0;
            padding: 20px;
            margin: 20px auto;
            width: 50%;
            border-radius: 10px;
        }
    </style>
</head>
<body>
    <div class="box">
        <h1>Redirecting...</h1>
        <p>Please wait while we take you to the destination.</p>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return "URL Masking Tool is running!"

@app.route('/<fake_url>')
def redirect_to_original(fake_url):
    original_url = url_mapping.get(fake_url)
    if original_url:
        return render_template_string(LOADING_PAGE) + f"""
        <script>
            setTimeout(function() {{
                window.location.href = "{original_url}";
            }}, 2000);
        </script>
        """
    else:
        return "Invalid masked URL!"

def start_flask():
    app.run(port=8000)

def is_url_registered(url):
    try:
        response = requests.get(f"http://{url}", timeout=5)
        return response.status_code == 200
    except:
        return False

def suggest_fake_urls(original_url):
    suggestions = []
    fake_bases = ["Y0u", "F4ke", "N3w", "DummY", "T3st"]
    domains = ["tube", "book", "gram", "site", "page"]
    for base in fake_bases:
        for domain in domains:
            fake_url = f"{base}{domain}.com"
            if not is_url_registered(fake_url):
                suggestions.append(fake_url)
    return suggestions[:5]  # Return top 5 suggestions

def main():
    print(Fore.CYAN + """
    ===================================
    🔗 URL Masking Tool (Education Only)
    ===================================
    """ + Style.RESET_ALL)

    # Start Flask in a thread
    threading.Thread(target=start_flask, daemon=True).start()
    print(Fore.GREEN + "🛠️ Flask server started on port 8000.")
    print(Fore.YELLOW + "🔗 Now run in a new terminal: ngrok http 8000")
    print(Fore.MAGENTA + "🌐 Ngrok will provide your public URL.\n")

    while True:
        print(Fore.CYAN + "\nOptions:")
        print(Fore.GREEN + "1. Create a new masked URL")
        print(Fore.BLUE + "2. List all masked URLs")
        print(Fore.RED + "3. Exit")
        choice = input(Fore.YELLOW + "Choose an option (1/2/3): " + Style.RESET_ALL)

        if choice == "1":
            print(Fore.CYAN + "\n🔗 Enter the original URL (e.g., https://youtube.com):")
            original_url = input(Fore.GREEN + "> " + Style.RESET_ALL)
            print(Fore.CYAN + "\n🤖 Analyzing and suggesting fake URLs...")
            time.sleep(2)
            suggestions = suggest_fake_urls(original_url.split("//")[-1].split("/")[0])
            if not suggestions:
                print(Fore.RED + "❌ No unregistered fake URLs found. Try manually.")
                fake_url = input(Fore.CYAN + "🎭 Enter your fake URL (e.g., Y0utube): " + Style.RESET_ALL)
            else:
                print(Fore.GREEN + "\n💡 Suggested fake URLs (unregistered):")
                for i, url in enumerate(suggestions, 1):
                    print(f"{Fore.YELLOW}{i}. {url}")
                choice = input(Fore.CYAN + "\nSelect a suggestion (1-5) or enter your own: " + Style.RESET_ALL)
                fake_url = suggestions[int(choice)-1] if choice.isdigit() and 1 <= int(choice) <= 5 else input(Fore.CYAN + "🎭 Enter your fake URL: " + Style.RESET_ALL)

            print(Fore.CYAN + "\n🔍 Checking if fake URL is unregistered...")
            time.sleep(1)
            if not is_url_registered(fake_url):
                ngrok_url = input(Fore.YELLOW + "🌐 Enter your ngrok URL (e.g., https://abc123.ngrok.io): " + Style.RESET_ALL)
                masked_url = f"{ngrok_url}/{fake_url}"
                url_mapping[fake_url] = original_url
                print(Fore.GREEN + f"\n✅ Success! Your masked URL is ready:")
                print(Fore.MAGENTA + f"🔗 Masked URL: {masked_url}")
                print(Fore.CYAN + f"💡 When someone visits {masked_url}, they will be redirected to {original_url}")
                print(Fore.YELLOW + "📋 Copy this URL and test it on your phone!")
            else:
                print(Fore.RED + f"❌ Error: '{fake_url}' is already registered. Try another.")

        elif choice == "2":
            print(Fore.CYAN + "\n📋 Masked URLs:")
            for fake, original in url_mapping.items():
                print(Fore.MAGENTA + f"🔗 {fake} → {original}")

        elif choice == "3":
            print(Fore.RED + "Exiting...")
            break

        else:
            print(Fore.RED + "Invalid choice!")

if __name__ == "__main__":
    main()
