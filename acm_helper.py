#!/usr/bin/env python3

import os
import sys
import json
import urllib.request
import urllib.parse
import glob
import shutil
import re
import datetime
import credentials

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
            'User-Agent': credentials.USER_AGENT
        },
        data=json.dumps({}).encode('utf-8'),
        method='POST'
    )
    with urllib.request.urlopen(req, timeout=timeout) as res:
        return json.loads(res.read().decode('utf-8'))

def _try_refresh_token(refresh_token, timeout):
    try:
        req_refresh = urllib.request.Request(
            'https://oauth2.googleapis.com/token',
            data=urllib.parse.urlencode({
                'client_id': credentials.CLIENT_ID,
                'client_secret': credentials.get_client_secret(),
                'refresh_token': refresh_token,
                'grant_type': 'refresh_token'
            }).encode('utf-8'),
            method='POST'
        )
        with urllib.request.urlopen(req_refresh, timeout=timeout) as res_ref:
            return json.loads(res_ref.read().decode('utf-8'))
    except Exception:
        return None

def is_token_expired(expiry_str):
    if not expiry_str:
        return True
    try:
        m = re.match(r'^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})', expiry_str)
        if not m:
            return True
        dt_str = m.group(1)
        dt = datetime.datetime.strptime(dt_str, '%Y-%m-%dT%H:%M:%S')
        offset_minutes = 0
        if 'Z' not in expiry_str and 'z' not in expiry_str:
            m_off = re.search(r'([+-])(\d{2}):(\d{2})$', expiry_str)
            if m_off:
                sign = 1 if m_off.group(1) == '+' else -1
                hours = int(m_off.group(2))
                minutes = int(m_off.group(3))
                offset_minutes = sign * (hours * 60 + minutes)
        dt_utc = dt - datetime.timedelta(minutes=offset_minutes)
        now_utc = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        return dt_utc <= now_utc + datetime.timedelta(minutes=5)
    except Exception:
        return True

def ensure_token_valid(data, timeout, force=False):
    token_dict = data.get('token', {})
    expiry = token_dict.get('expiry')
    refresh_token = token_dict.get('refresh_token')
    if (force or is_token_expired(expiry)) and refresh_token:
        ref_data = _try_refresh_token(refresh_token, timeout)
        if ref_data and 'access_token' in ref_data:
            token_dict['access_token'] = ref_data['access_token']
            expires_in = ref_data.get('expires_in', 3600)
            now_t = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
            new_expiry = (now_t + datetime.timedelta(seconds=expires_in)).strftime('%Y-%m-%dT%H:%M:%SZ')
            token_dict['expiry'] = new_expiry
            data['token'] = token_dict
            return True
    return False

def save_profile_and_sync(profile_path, data):
    try:
        with open(profile_path, 'w') as f:
            json.dump(data, f)
    except Exception:
        pass
    try:
        token_path = os.path.expanduser('~/.gemini/antigravity-cli/antigravity-oauth-token')
        if os.path.exists(token_path):
            with open(token_path) as f:
                active_data = json.load(f)
            active_ref = active_data.get('token', {}).get('refresh_token')
            profile_ref = data.get('token', {}).get('refresh_token')
            if active_ref and profile_ref and active_ref == profile_ref:
                with open(token_path, 'w') as f:
                    json.dump(data, f)
    except Exception:
        pass

def _parse_quota_groups(groups):
    g_pct = None
    c_pct = None
    for group in groups:
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
    return g_pct, c_pct

def refresh_quota(profile_path, timeout):
    try:
        with open(profile_path) as f:
            data = json.load(f)
    except Exception:
        return False

    if ensure_token_valid(data, timeout):
        save_profile_and_sync(profile_path, data)

    access_token = data.get('token', {}).get('access_token')
    if not access_token:
        return False

    quota_data = None
    try:
        quota_data = query_quota(access_token, timeout)
    except Exception:
        if ensure_token_valid(data, timeout, force=True):
            save_profile_and_sync(profile_path, data)
            access_token = data.get('token', {}).get('access_token')
            try:
                quota_data = query_quota(access_token, timeout)
            except Exception:
                pass

    if not quota_data:
        return False

    try:
        g_pct, c_pct = _parse_quota_groups(quota_data.get('groups', []))
        if g_pct is not None or c_pct is not None:
            data['g_pct'] = g_pct if g_pct is not None else 0
            data['c_pct'] = c_pct if c_pct is not None else 0
            data['quota_percent'] = data['g_pct'] + data['c_pct']
            save_profile_and_sync(profile_path, data)
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
            return re.sub(r'[^a-zA-Z0-9@._+-]', '_', email)
    except Exception:
        return ""

def get_all_quotas(profiles_dir):
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

def rotate_profile(token_path, profiles_dir):
    try:
        with open(token_path) as f:
            active_data = json.load(f)
        active_refresh = active_data.get('token', {}).get('refresh_token')
    except Exception:
        active_refresh = None

    best_profile = None
    best_quota = -1
    active_profile_path = None
    
    for p in glob.glob(os.path.join(profiles_dir, '*.json')):
        try:
            with open(p) as f:
                d = json.load(f)
            if active_refresh and d.get('token', {}).get('refresh_token') == active_refresh:
                active_profile_path = p
            q = d.get('quota_percent', -1)
            if q > best_quota:
                best_quota = q
                best_profile = p
        except Exception:
            pass

    active_quota = -1
    if active_profile_path:
        try:
            with open(active_profile_path) as f:
                prof_data = json.load(f)
            updated = ensure_token_valid(prof_data, timeout=5)
            if updated:
                with open(active_profile_path, 'w') as f:
                    json.dump(prof_data, f)
            shutil.copy(active_profile_path, token_path)
            active_quota = prof_data.get('quota_percent', -1)
        except Exception:
            pass

    if active_quota <= 0 or not active_profile_path:
        if best_profile and best_profile != active_profile_path and best_quota > 0:
            try:
                with open(best_profile) as f:
                    best_data = json.load(f)
                updated = ensure_token_valid(best_data, timeout=5)
                if updated:
                    with open(best_profile, 'w') as f:
                        json.dump(best_data, f)
            except Exception:
                pass
            shutil.copy(best_profile, token_path)
            return os.path.basename(best_profile).replace('.json', '')
    return ""


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
    elif cmd == 'rotate':
        new_prof = rotate_profile(sys.argv[2], sys.argv[3])
        if new_prof:
            print(new_prof)

if __name__ == '__main__':
    main()
