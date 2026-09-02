import os
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests

# --- DUMMY HTTP SERVER FOR RENDER ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is active")

def run_health_check_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

# Start background thread for Render health check
threading.Thread(target=run_health_check_server, daemon=True).start()

# --- YOUR TELEGRAM BOT CODE ---
BOT_TOKEN = "8920477645:AAEzi5AEGhmbO2GIcW83x9CCTEfSvL9sbLo" 
CHANNEL_ID = "@Evalex_academy"
WEB_APP_URL = "https://exam-frontend-m8id.vercel.app/"

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def is_channel_member(user_id: int) -> bool:
    url = f"{API_URL}/getChatMember"
    try:
        res = requests.get(url, params={"chat_id": CHANNEL_ID, "user_id": user_id}, timeout=5).json()
        if res.get("ok"):
            status = res["result"]["status"]
            return status in ["creator", "administrator", "member"]
        return False
    except Exception:
        return False

def send_message(chat_id: int, text: str, reply_markup: dict = None):
    url = f"{API_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    requests.post(url, json=payload)

def edit_message(chat_id: int, message_id: int, text: str, reply_markup: dict = None):
    url = f"{API_URL}/editMessageText"
    payload = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "Markdown"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    requests.post(url, json=payload)

def answer_callback(callback_query_id: str):
    url = f"{API_URL}/answerCallbackQuery"
    requests.post(url, json={"callback_query_id": callback_query_id})

def get_gatekeeper_payload(user_id: int, first_name: str):
    if is_channel_member(user_id):
        text = (
            f"👋 **Hello, {first_name}!**\n\n"
            "🎓 **Evalex Academy**\n"
            "**Final UAT Model Examination Portal**\n\n"
            "Welcome to the Final UAT Model examination simulation.\n\n"
            "📝 **Total Questions:** 100 (45 Quantitative, 55 Verbal & Analytical)\n"
            "⏱ **Duration:** 2 Hours 30 Minutes\n"
            "🎯 **Pass Mark:** 50%\n\n"
            "Tap the button below to begin!"
        )
        keyboard = {
            "inline_keyboard": [
                [{"text": " Start Exam", "web_app": {"url": WEB_APP_URL}}]
            ]
        }
        return text, keyboard
    else:
        text = (
            f"👋 **Hello, {first_name}!**\n\n"
            "⚠️ **Access Restricted!**\n\n"
            "You must join `@Evalex_academy` to access the Final UAT Model Exam. "
            "Join the channel and tap **Verify Membership**."
        )
        keyboard = {
            "inline_keyboard": [
                [{"text": "📢 Join @Evalex_academy", "url": "https://t.me/Evalex_academy"}],
                [{"text": "🔄 Verify Membership", "callback_data": "check_again"}]
            ]
        }
        return text, keyboard

def main():
    offset = 0
    while True:
        try:
            url = f"{API_URL}/getUpdates"
            res = requests.get(url, params={"offset": offset, "timeout": 10}, timeout=15).json()
            
            if res.get("ok"):
                for update in res["result"]:
                    offset = update["update_id"] + 1
                    
                    if "message" in update and "text" in update.get("message", {}):
                        msg = update["message"]
                        if msg["text"].startswith("/start"):
                            user_id = msg["from"]["id"]
                            first_name = msg["from"].get("first_name") or msg["from"].get("username") or "Candidate"
                            
                            text, keyboard = get_gatekeeper_payload(user_id, first_name)
                            send_message(msg["chat"]["id"], text, keyboard)
                    
                    elif "callback_query" in update:
                        cb = update["callback_query"]
                        user_id = cb["from"]["id"]
                        first_name = cb["from"].get("first_name") or cb["from"].get("username") or "Candidate"
                        
                        answer_callback(cb["id"])
                        
                        if cb.get("data") == "check_again":
                            text, keyboard = get_gatekeeper_payload(user_id, first_name)
                            chat_id = cb["message"]["chat"]["id"]
                            message_id = cb["message"]["message_id"]
                            edit_message(chat_id, message_id, text, keyboard)
                            
        except Exception:
            time.sleep(2)

if __name__ == "__main__":
    main()
