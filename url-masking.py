from flask import Flask, request, render_template_string
import random
import string

app = Flask(__name__)

def generate_random_string(length=8):
    """Generate a random string for unique URLs."""
    letters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(letters) for _ in range(length))

HTML_FORM = """
<!DOCTYPE html>
<html>
<head>
    <title>Advanced URL Masker</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        h1 {
            color: #333;
            text-align: center;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        input[type="text"] {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-sizing: border-box;
        }
        button {
            background-color: #4CAF50;
            color: white;
            padding: 12px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            width: 100%;
            font-size: 16px;
        }
        button:hover {
            background-color: #45a049;
        }
        .output {
            margin-top: 20px;
            padding: 15px;
            background-color: #e9f7ef;
            border-radius: 4px;
            border-left: 4px solid #4CAF50;
        }
        .masked-url {
            word-break: break-all;
            font-family: monospace;
            background-color: #fff;
            padding: 10px;
            border-radius: 4px;
            border: 1px solid #ddd;
        }
        .suggestions {
            margin-top: 15px;
            padding: 10px;
            background-color: #fff8e1;
            border-radius: 4px;
            border-left: 4px solid #ffc107;
        }
        .suggestions p {
            margin: 5px 0;
        }
    </style>
</head>
<body>
    <h1>Advanced URL Masker</h1>
    <form method="POST">
        <div class="form-group">
            <label for="original_url">Original URL (e.g., https://hello.com):</label>
            <input type="text" id="original_url" name="original_url" placeholder="https://hello.com" required>
        </div>
        <div class="form-group">
            <label for="fake_url">Fake URL (e.g., https://example.com):</label>
            <input type="text" id="fake_url" name="fake_url" placeholder="https://example.com" required>
        </div>
        <button type="submit">Generate Unique Masked URL</button>
    </form>

    {% if masked_url %}
    <div class="output">
        <h3>Your Unique Masked URL:</h3>
        <div class="masked-url">
            <a href="{{ masked_url }}" target="_blank">{{ masked_url }}</a>
        </div>
        <p><strong>Note:</strong> This URL will show the fake URL but redirect to the original URL.</p>
    </div>
    {% endif %}

    {% if suggestions %}
    <div class="suggestions">
        <h3>Suggestions for Modification:</h3>
        {% for suggestion in suggestions %}
        <p>✅ {{ suggestion }}</p>
        {% endfor %}
    </div>
    {% endif %}
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def home():
    masked_url = None
    suggestions = []
    if request.method == "POST":
        original_url = request.form.get("original_url")
        fake_url = request.form.get("fake_url")

        if original_url and fake_url:
            # Add http:// if missing
            if not original_url.startswith(('http://', 'https://')):
                original_url = 'http://' + original_url
            if not fake_url.startswith(('http://', 'https://')):
                fake_url = 'http://' + fake_url

            # Generate a unique random string for the URL
            random_string = generate_random_string()
            masked_url = f"http://your-server-ip:5000/{random_string}?fake={fake_url}&original={original_url}"

            # Generate suggestions
            suggestions.append(f"Try using a shorter fake URL like: {fake_url.split('//')[1].split('/')[0].split('.')[0]},com")
            suggestions.append(f"For better results, use HTTPS: {original_url.replace('http://', 'https://')}")

    return render_template_string(HTML_FORM, masked_url=masked_url, suggestions=suggestions)

@app.route("/<random_string>")
def redirect_with_random(random_string):
    fake_url = request.args.get("fake")
    original_url = request.args.get("original")

    if original_url:
        return f"""
        <html>
            <head>
                <title>Redirecting to {fake_url}</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        text-align: center;
                        margin-top: 50px;
                    }}
                    h1 {{
                        color: #333;
                    }}
                </style>
            </head>
            <body>
                <h1>Redirecting to {fake_url}...</h1>
                <p>You will be redirected to the original URL shortly.</p>
                <script>
                    setTimeout(function() {{
                        window.location.href = "{original_url}";
                    }}, 2000);
                </script>
            </body>
        </html>
        """
    else:
        return "Invalid URL", 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
