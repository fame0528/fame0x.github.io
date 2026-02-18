#!/usr/bin/env python3
import os
import json
import subprocess
from datetime import datetime, timedelta
import yaml

def load_config(config_path='config.yaml'):
    if os.path.exists(config_path):
        with open(config_path) as f:
            return yaml.safe_load(f)
    return {}

def check_github_pages(repo_path):
    result = {"name": "GitHub Pages", "status": "UNKNOWN"}
    try:
        posts_dir = os.path.join(repo_path, '_posts')
        if os.path.isdir(posts_dir):
            files = [f for f in os.listdir(posts_dir) if f.endswith('.md')]
            if files:
                mtimes = [os.path.getmtime(os.path.join(posts_dir, f)) for f in files]
                newest = max(mtimes)
                if datetime.now().timestamp() - newest < 7*86400:
                    result["status"] = "GREEN"
                    result["details"] = f"{len(files)} posts, latest recent"
                else:
                    result["status"] = "YELLOW"
                    result["details"] = f"{len(files)} posts, none in 7 days"
            else:
                result["status"] = "YELLOW"
                result["details"] = "No posts yet"
        else:
            result["status"] = "RED"
            result["details"] = "No _posts directory"
    except Exception as e:
        result["status"] = "RED"
        result["details"] = str(e)
    return result

def check_affiliate_links(repo_path):
    result = {"name": "Affiliate Links", "status": "UNKNOWN"}
    try:
        posts_dir = os.path.join(repo_path, '_posts')
        if not os.path.isdir(posts_dir):
            result["status"] = "RED"
            result["details"] = "No posts dir"
            return result
        files = [os.path.join(posts_dir, f) for f in os.listdir(posts_dir) if f.endswith('.md')]
        total = len(files)
        if total == 0:
            result["status"] = "YELLOW"
            result["details"] = "No posts to check"
            return result
        count = 0
        for fp in files:
            with open(fp, 'r', encoding='utf-8') as f:
                content = f.read()
                if '[AMAZON_LINK' in content or 'amazon.' in content:
                    count += 1
        ratio = count / total
        if ratio > 0.8:
            result["status"] = "GREEN"
            result["details"] = f"{count}/{total} posts have affiliate links"
        else:
            result["status"] = "YELLOW"
            result["details"] = f"Only {count}/{total} posts have affiliate links"
    except Exception as e:
        result["status"] = "RED"
        result["details"] = str(e)
    return result

def check_recent_activity(repo_path):
    result = {"name": "Recent Activity", "status": "UNKNOWN"}
    try:
        cmd = ['git', 'log', '--since="7 days ago"', '--oneline']
        out = subprocess.check_output(cmd, cwd=repo_path, stderr=subprocess.STDOUT, text=True)
        lines = out.strip().split('\n')
        if lines and lines[0]:
            result["status"] = "GREEN"
            result["details"] = f"{len(lines)} commits in 7 days"
        else:
            result["status"] = "YELLOW"
            result["details"] = "No recent commits"
    except Exception as e:
        result["status"] = "RED"
        result["details"] = f"Git error: {e}"
    return result

def run_health_check():
    config = load_config()
    repo_path = config.get('repo_path', os.getcwd())
    results = [
        check_github_pages(repo_path),
        check_affiliate_links(repo_path),
        check_recent_activity(repo_path),
    ]
    return results

if __name__ == '__main__':
    results = run_health_check()
    print("=== HEALTH CHECK ===")
    for r in results:
        symbol = "✅" if r['status'] == 'GREEN' else "⚠️" if r['status'] == 'YELLOW' else "❌"
        print(f"{symbol} {r['name']}: {r['details']}")
    report = {
        "timestamp": datetime.now().isoformat(),
        "checks": results
    }
    with open('health_status.json', 'w') as f:
        json.dump(report, f, indent=2)
    print("\nReport saved to health_status.json")