import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
import yaml

class StructuredLogger:
    def __init__(self, config: Dict[str, Any], db: 'Database'):
        self.config = config
        self.db = db
        self.log_dir = 'logs'
        os.makedirs(self.log_dir, exist_ok=True)

    def _write_json_log(self, entry: Dict[str, Any]):
        """Write JSON log to daily file."""
        date_str = datetime.now().strftime('%Y-%m-%d')
        log_file = os.path.join(self.log_dir, f'{date_str}.jsonl')
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry) + '\n')
        except Exception as e:
            pass  # logging failure shouldn't crash the app

    def log(self, level: str, module: str, message: str, **kwargs):
        entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level.upper(),
            'module': module,
            'message': message,
            **kwargs
        }
        # Write to file
        self._write_json_log(entry)
        # Also write to database audit log
        try:
            self.db.log(module, message, json.dumps(kwargs) if kwargs else '', level.lower())
        except:
            pass
        # Send critical alerts to Discord
        if level.upper() in ('ERROR', 'CRITICAL', 'WARNING'):
            self._send_discord_alert(entry)

    def info(self, module: str, message: str, **kwargs):
        self.log('info', module, message, **kwargs)

    def warning(self, module: str, message: str, **kwargs):
        self.log('warning', module, message, **kwargs)

    def error(self, module: str, message: str, **kwargs):
        self.log('error', module, message, **kwargs)

    def critical(self, module: str, message: str, **kwargs):
        self.log('critical', module, message, **kwargs)

    def _send_discord_alert(self, entry: Dict[str, Any]):
        webhook_url = self.config.get('discord_webhook_url') or os.getenv('DISCORD_WEBHOOK_URL')
        if not webhook_url:
            return
        try:
            import requests
            emoji = "❌" if entry['level'] == 'ERROR' else "⚠️" if entry['level'] == 'WARNING' else "ℹ️"
            content = f"{emoji} **{entry['level']}** in `{entry['module']}`\n{entry['message']}"
            if 'exception' in entry:
                content += f"\n```\n{entry['exception'][:500]}\n```"
            data = {"content": content, "username": "Income Bot Alert"}
            requests.post(webhook_url, json=data, timeout=5)
        except Exception:
            pass  # Discord failure shouldn't cascade