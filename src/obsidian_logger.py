import os
import json
from datetime import datetime
import yaml

def log_to_obsidian(vault_path=None, entry=None, category='IncomeBot'):
    if not vault_path:
        try:
            with open('config.yaml') as f:
                cfg = yaml.safe_load(f)
                vault_path = cfg.get('obsidian_vault_path')
        except:
            vault_path = os.getenv('OBSIDIAN_VAULT_PATH')
    if not vault_path:
        print("No Obsidian vault path configured")
        return False
    base_dir = os.path.join(vault_path, category)
    os.makedirs(base_dir, exist_ok=True)
    date_str = datetime.now().strftime('%Y-%m-%d')
    filepath = os.path.join(base_dir, f'{date_str}.md')
    timestamp = datetime.now().strftime('%H:%M')
    content = f"## {timestamp}\n\n{entry}\n\n---\n\n"
    with open(filepath, 'a', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Logged to Obsidian: {filepath}")
    return True

if __name__ == '__main__':
    log_to_obsidian(entry="Test log from Income Bot")