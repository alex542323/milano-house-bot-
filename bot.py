import requests, json

TELEGRAM_TOKEN = "7977881088:AAEr1JHIEdvd-kiXFyONscQg4HJkqzBr4bA"
CHAT_ID = "660849220"

def test_send():
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": "Test message from bot_test_telegram.py - if you see this, Telegram works.",
        "disable_web_page_preview": True
    }
    try:
        resp = requests.post(url, json=payload, timeout=15)
        print("status_code:", resp.status_code)
        try:
            print("response:", json.dumps(resp.json(), indent=2, ensure_ascii=False))
        except Exception:
            print("response text:", resp.text)
    except Exception as e:
        print("request exception:", e)

if __name__ == '__main__':
    test_send()
