"""
Quick test script to verify Telegram bot configuration
Run this with: python test_telegram.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from django.conf import settings
import requests

def test_telegram():
    bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
    chat_id = getattr(settings, 'TELEGRAM_ADMIN_CHAT_ID', '')
    
    print("Testing Telegram Bot Configuration...")
    print(f"Bot Token: {'Set' if bot_token else 'NOT SET'}")
    print(f"Chat ID: {chat_id if chat_id else 'NOT SET'}")
    print()
    
    if not bot_token or not chat_id:
        print("❌ ERROR: Bot token or Chat ID is missing!")
        print("Please set TELEGRAM_BOT_TOKEN and TELEGRAM_ADMIN_CHAT_ID in settings.py")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            'chat_id': str(chat_id),
            'text': '🧪 Test message from Exam Platform! If you see this, Telegram integration is working! ✅'
        }
        response = requests.post(url, data=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print("✅ SUCCESS! Test message sent to Telegram!")
                print("Check your Telegram - you should see the test message.")
                return True
            else:
                print(f"❌ ERROR: Telegram API returned error: {result.get('description', 'Unknown error')}")
                return False
        else:
            print(f"❌ ERROR: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {e}")
        return False

if __name__ == '__main__':
    test_telegram()

