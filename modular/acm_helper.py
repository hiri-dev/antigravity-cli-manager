#!/usr/bin/env python3

import os
import sys
import json
import base64
import urllib.request
import urllib.parse

SEC_B64 = 'R0NTUFgtSzU4RldSNDg2TGRMSjFtTEI4c1hDNHo2cURBZg=='

def get_config(config_path, key, default):
    try:
        with open(config_path) as f:
            return json.load(f).get(key, default)
    except Exception:
        return default

def get_profile_quota(profile_path):
    try:
        with open(profile_path) as f:
            d = json.load(f)
            return f"{d.get('g_pct','')},{d.get('c_pct','')},{d.get('quota_percent','')}"
    except Exception:
        return ",,"

def query_quota(token, timeout):
    req = urllib.request.Request(
        'https://cloudcode-pa.googleapis.com/v1internal:retrieveUserQuotaSummary',
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'User-Agent': 'vscode/1.X.X (Antigravity/4.2.4)'
        },
        data=json.dumps({}).encode('utf-8'),
        method='POST'
    )
    with urllib.request.urlopen(req, timeout=timeout) as res:
        return json.loads(res.read().decode('utf-8'))

def refresh_quota(profile_path, timeout):
    try:
        with open(profile_path) as f:
            data = json.load(f)
    except Exception:
        return False

    access_token = data.get('token', {}).get('access_token')
    refresh_token = data.get('token', {}).get('refresh_token')

    if not access_token:
        return False

    quota_data = None
    try:
        quota_data = query_quota(access_token, timeout)
    except Exception:
        if refresh_token:
            try:
                req_refresh = urllib.request.Request(
                    'https://oauth2.googleapis.com/token',
                    data=urllib.parse.urlencode({
                        'client_id': '1071006060591-tmhssin2h21lcre235vtolojh4g403ep.apps.googleusercontent.com',
                        'client_secret': base64.b64decode(SEC_B64).decode('utf-8'),
                        'refresh_token': refresh_token,
                        'grant_type': 'refresh_token'
                    }).encode('utf-8'),
                    method='POST'
                )
                with urllib.request.urlopen(req_refresh, timeout=timeout) as res_ref:
                    ref_res_data = json.loads(res_ref.read().decode('utf-8'))
                    new_token = ref_res_data.get('access_token')
                    if new_token:
                        access_token = new_token
                        data['token']['access_token'] = new_token
                        try:
                            quota_data = query_quota(access_token, timeout)
                            with open(profile_path, 'w') as f:
                                json.dump(data, f)
                        except Exception:
                            pass
            except Exception:
                pass

    if not quota_data:
        return False

    try:
        g_pct = None
        c_pct = None
        
        for group in quota_data.get('groups', []):
            display_name = group.get('displayName', '').lower()
            weekly_frac = None
            fiveh_frac = None
            for b in group.get('buckets', []):
                w = b.get('window', '').lower()
                if w == 'weekly':
                    weekly_frac = b.get('remainingFraction')
                elif w == '5h':
                    fiveh_frac = b.get('remainingFraction')
                    
            if weekly_frac is None:
                weekly_frac = 1.0
            if fiveh_frac is None:
                fiveh_frac = 1.0
                
            pct = 0
            if weekly_frac > 0.001:
                pct = int(fiveh_frac * 100)
                
            if 'gemini' in display_name:
                g_pct = pct
            elif 'claude' in display_name or 'gpt' in display_name or '3p' in display_name:
                c_pct = pct

        if g_pct is not None or c_pct is not None:
            data['g_pct'] = g_pct if g_pct is not None else 0
            data['c_pct'] = c_pct if c_pct is not None else 0
            data['quota_percent'] = data['g_pct'] + data['c_pct']
            with open(profile_path, 'w') as f:
                json.dump(data, f)
            return True
    except Exception:
        pass
    return False

def get_email(token_path):
    try:
        with open(token_path) as f:
            data = json.load(f)
        access_token = data.get('token', {}).get('access_token', '')
        if not access_token:
            return ""
        req = urllib.request.Request(
            'https://www.googleapis.com/oauth2/v3/userinfo',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        with urllib.request.urlopen(req, timeout=5) as res:
            email = json.loads(res.read().decode('utf-8')).get('email', '')
            import re
            return re.sub(r'[^a-zA-Z0-9@._+-]', '_', email)
    except Exception:
        return ""

def get_all_quotas(profiles_dir):
    import glob
    res = []
    if os.path.isdir(profiles_dir):
        for p in sorted(glob.glob(os.path.join(profiles_dir, '*.json'))):
            try:
                with open(p) as f:
                    d = json.load(f)
                    g = d.get('g_pct', '')
                    c = d.get('c_pct', '')
                    q = d.get('quota_percent', '')
                    res.append(f"{p},{g},{c},{q}")
            except Exception:
                pass
    return "\n".join(res)

def main():
    if len(sys.argv) < 2:
        sys.exit(1)
    
    cmd = sys.argv[1]
    if cmd == 'get_config':
        print(get_config(sys.argv[2], sys.argv[3], sys.argv[4]))
    elif cmd == 'get_quota':
        print(get_profile_quota(sys.argv[2]))
    elif cmd == 'get_all_quotas':
        print(get_all_quotas(sys.argv[2]))
    elif cmd == 'refresh':
        success = refresh_quota(sys.argv[2], int(sys.argv[3]))
        sys.exit(0 if success else 1)
    elif cmd == 'get_email':
        print(get_email(sys.argv[2]))

if __name__ == '__main__':
    main()
