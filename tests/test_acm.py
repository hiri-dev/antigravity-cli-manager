import os
import sys
import unittest
import json
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import acm_helper

class TestAcmHelper(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_sanitize_blocks_path_traversal(self):
        token_data = {
            "token": {
                "access_token": "mock_token"
            }
        }
        token_path = os.path.join(self.test_dir, "token.json")
        with open(token_path, "w") as f:
            json.dump(token_data, f)

        original_urlopen = acm_helper.urllib.request.urlopen
        class MockResponse:
            def read(self):
                return json.dumps({"email": "../../../etc/shadow"}).encode('utf-8')
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc_val, exc_tb):
                pass

        def mock_urlopen(req, timeout=None):
            return MockResponse()

        acm_helper.urllib.request.urlopen = mock_urlopen
        try:
            email = acm_helper.get_email(token_path)
            self.assertEqual(email, ".._.._.._etc_shadow")
        finally:
            acm_helper.urllib.request.urlopen = original_urlopen

    def test_get_all_quotas_skips_invalid_json(self):
        valid_profile = {
            "g_pct": 50,
            "c_pct": 40,
            "quota_percent": 90
        }
        with open(os.path.join(self.test_dir, "valid.json"), "w") as f:
            json.dump(valid_profile, f)

        with open(os.path.join(self.test_dir, "invalid.json"), "w") as f:
            f.write("{invalid_json")

        result = acm_helper.get_all_quotas(self.test_dir)
        lines = result.splitlines()
        self.assertEqual(len(lines), 1)
        self.assertIn("valid.json", lines[0])
        self.assertIn("50,40,90", lines[0])

    def test_get_all_quotas_handles_missing_keys(self):
        incomplete_profile = {
            "g_pct": 20
        }
        with open(os.path.join(self.test_dir, "incomplete.json"), "w") as f:
            json.dump(incomplete_profile, f)

        result = acm_helper.get_all_quotas(self.test_dir)
        self.assertIn("incomplete.json,20,,", result)

    def test_get_config_returns_default_on_missing_file(self):
        config_path = os.path.join(self.test_dir, "nonexistent.json")
        val = acm_helper.get_config(config_path, "show_ascii_art", True)
        self.assertTrue(val)

    def test_rotate_profile_swaps_on_zero_quota(self):
        token_path = os.path.join(self.test_dir, "token.json")
        token_data = {"token": {"refresh_token": "token_a"}, "quota_percent": 0}
        with open(token_path, "w") as f:
            json.dump(token_data, f)

        profiles_dir = os.path.join(self.test_dir, "profiles")
        os.makedirs(profiles_dir)
        
        with open(os.path.join(profiles_dir, "profile_a.json"), "w") as f:
            json.dump({"token": {"refresh_token": "token_a"}, "quota_percent": 0}, f)
        with open(os.path.join(profiles_dir, "profile_b.json"), "w") as f:
            json.dump({"token": {"refresh_token": "token_b"}, "quota_percent": 80}, f)

        rotated = acm_helper.rotate_profile(token_path, profiles_dir)
        self.assertEqual(rotated, "profile_b")
        with open(token_path) as f:
            new_data = json.load(f)
        self.assertEqual(new_data["token"]["refresh_token"], "token_b")

    def test_rotate_profile_skips_when_quota_valid(self):
        token_path = os.path.join(self.test_dir, "token.json")
        token_data = {"token": {"refresh_token": "token_a"}, "quota_percent": 30}
        with open(token_path, "w") as f:
            json.dump(token_data, f)

        profiles_dir = os.path.join(self.test_dir, "profiles")
        os.makedirs(profiles_dir)

        with open(os.path.join(profiles_dir, "profile_a.json"), "w") as f:
            json.dump({"token": {"refresh_token": "token_a"}, "quota_percent": 30}, f)
        with open(os.path.join(profiles_dir, "profile_b.json"), "w") as f:
            json.dump({"token": {"refresh_token": "token_b"}, "quota_percent": 80}, f)

        rotated = acm_helper.rotate_profile(token_path, profiles_dir)
        self.assertEqual(rotated, "")
        with open(token_path) as f:
            new_data = json.load(f)
        self.assertEqual(new_data["token"]["refresh_token"], "token_a")

    def test_is_token_expired(self):
        self.assertTrue(acm_helper.is_token_expired(None))
        self.assertTrue(acm_helper.is_token_expired(""))
        self.assertTrue(acm_helper.is_token_expired("2020-01-01T00:00:00Z"))
        
        future_dt = (acm_helper.datetime.datetime.now(acm_helper.datetime.timezone.utc).replace(tzinfo=None) + acm_helper.datetime.timedelta(hours=2)).strftime('%Y-%m-%dT%H:%M:%SZ')
        self.assertFalse(acm_helper.is_token_expired(future_dt))
        
        past_dt = (acm_helper.datetime.datetime.now(acm_helper.datetime.timezone.utc).replace(tzinfo=None) - acm_helper.datetime.timedelta(hours=2)).strftime('%Y-%m-%dT%H:%M:%SZ')
        self.assertTrue(acm_helper.is_token_expired(past_dt))

    def test_ensure_token_valid_refreshes(self):
        data = {
            "token": {
                "access_token": "old_token",
                "refresh_token": "refresh_val",
                "expiry": "2020-01-01T00:00:00Z"
            }
        }
        
        original_try_refresh = acm_helper._try_refresh_token
        def mock_try_refresh(refresh_token, timeout):
            return {"access_token": "new_token", "expires_in": 3600}
        
        acm_helper._try_refresh_token = mock_try_refresh
        try:
            updated = acm_helper.ensure_token_valid(data, 5)
            self.assertTrue(updated)
            self.assertEqual(data["token"]["access_token"], "new_token")
            self.assertFalse(acm_helper.is_token_expired(data["token"]["expiry"]))
        finally:
            acm_helper._try_refresh_token = original_try_refresh

if __name__ == '__main__':
    unittest.main()
