import requests
import os

def send_discord(webhook_url=None, content=None):
    if not webhook_url:
        webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
        if not webhook_url:
            try:
                import yaml
                with open('config.yaml') as f:
                    cfg = yaml.safe_load(f)
                    webhook_url = cfg.get('discord_webhook_url')
            except:
                pass
    if not webhook_url:
        print("No Discord webhook URL configured")
        return False
    data = {"content": content, "username": "Income Bot"}
    try:
        resp = requests.post(webhook_url, json=data, timeout=10)
        if resp.status_code == 204:
            print("✅ Discord notification sent")
            return True
        else:
            print(f"❌ Discord error: {resp.status_code} {resp.text}")
            return False
    except Exception as e:
        print(f"❌ Discord exception: {e}")
        return False

if __name__ == '__main__':
    send_discord(content="Health check: 🟢 All systems go")