from flask import Flask, redirect, render_template_string
import threading
import requests

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
        response = requests.get(url, timeout=5)
        return response.status_code == 200
    except:
        return False

def main():
    print("""
    ===================================
    🔗 URL Masking Tool (Education Only)
    ===================================
    """)

    # Start Flask in a thread
    threading.Thread(target=start_flask, daemon=True).start()
    print("🛠️ Flask server started on port 8000.")
    print("🔗 Now run: ngrok http 8000")
    print("🌐 Your public URL will be provided by ngrok.\n")

    while True:
        print("\nOptions:")
        print("1. Create a new masked URL")
        print("2. List all masked URLs")
        print("3. Exit")
        choice = input("Choose an option (1/2/3): ")

        if choice == "1":
            original_url = input("🔗 Enter original URL (e.g., https://instagram.com): ")
            fake_url = input("🎭 Enter fake URL (e.g., Y0utube): ")
            fake_full_url = f"http://{fake_url}"

            if not is_url_registered(fake_full_url):
                masked_url = f"[YOUR_NGROK_URL]/{fake_url}"  # Replace with your ngrok URL
                url_mapping[fake_url] = original_url
                print(f"\n✅ Success! Your masked URL is ready:")
                print(f"🔗 Masked URL: {masked_url}")
                print(f"💡 When someone visits {masked_url}, they will be redirected to {original_url}")
                print(f"📋 Copy this URL and test it on your phone!")
            else:
                print(f"❌ Error: '{fake_full_url}' is already a registered URL. Try another fake URL.")

        elif choice == "2":
            print("\n📋 Masked URLs:")
            for fake, original in url_mapping.items():
                print(f"🔗 [YOUR_NGROK_URL]/{fake} → {original}")

        elif choice == "3":
            print("Exiting...")
            break

        else:
            print("Invalid choice!")

if __name__ == "__main__":
    main()
