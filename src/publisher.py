import os
import subprocess
from datetime import datetime
import re

class Publisher:
    def __init__(self, config, db: 'Database' = None):
        self.repo_path = config['repo_path']
        self.branch = 'main'  # or gh-pages for some setups
        self.db = db

    def publish_article(self, filename, content, category='pet-care'):
        # Ensure posts directory exists
        posts_dir = os.path.join(self.repo_path, '_posts', category)
        os.makedirs(posts_dir, exist_ok=True)
        filepath = os.path.join(posts_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        # Git operations
        try:
            subprocess.run(['git', 'add', filepath], cwd=self.repo_path, check=True, capture_output=True)
            subprocess.run(['git', 'commit', '-m', f'Add article {filename}'], cwd=self.repo_path, check=True, capture_output=True)
            result = subprocess.run(['git', 'push', 'origin', self.branch], cwd=self.repo_path, check=True, capture_output=True, text=True)
            commit_sha_match = re.search(r'[a-f0-9]{7,40}', result.stdout)
            commit_sha = commit_sha_match.group(0) if commit_sha_match else None
            if self.db:
                # Get keyword from filename to link article
                kw = filename.replace('.md', '').replace('-', '_')
                from .database import get_or_create_keyword
                kw_id = get_or_create_keyword(self.db, kw)
                self.db.add_article(kw_id, filename, title='TBD', tokens=0)
                self.db.log_publish(article_id=None, commit_sha=commit_sha, status='success')
            print(f"[OK] Published {filename}")
            return commit_sha
        except subprocess.CalledProcessError as e:
            error_msg = f"Git error: {e.stderr if e.stderr else str(e)}"
            if self.db:
                self.db.record_error()
                self.db.log('publisher', 'publish_failed', error_msg, level='error')
            print(f"[ERROR] {error_msg}")
            raise