"""版权清单故障注入；合成测试材料不替代镜像中的原始源码校验。"""
import contextlib
import hashlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('smoke', Path(__file__).with_name('fastp-smoke.py'))
smoke = importlib.util.module_from_spec(spec)
spec.loader.exec_module(smoke)

class NoticeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='fastp-notice-test-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.manifest = self.root/'notices.sha256'
        self.victim = 'source-notices/src/cmdline.h'
        self.rows = {}
        for name in sorted(smoke.REQUIRED_NOTICES):
            path = self.root/name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('synthetic notice fixture: ' + name)
            self.rows[name] = hashlib.sha256(path.read_bytes()).hexdigest() + '  ' + name
        self.write_manifest()

    def write_manifest(self):
        self.manifest.write_text('\n'.join(self.rows.values()) + '\n')

    def verify(self):
        with contextlib.redirect_stdout(io.StringIO()):
            return smoke.verify_notices(self.root)

    def test_complete(self):
        self.assertEqual(self.verify(), 11)

    def test_missing_file(self):
        (self.root/self.victim).unlink()
        with self.assertRaisesRegex(ValueError, 'missing notice file'):
            self.verify()

    def test_missing_inventory_member(self):
        del self.rows[self.victim]
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, 'incomplete notice inventory'):
            self.verify()

    def test_file_and_inventory_member_both_removed(self):
        (self.root/self.victim).unlink()
        self.test_missing_inventory_member()

    def test_empty_inventory(self):
        self.manifest.write_text('')
        with self.assertRaisesRegex(ValueError, 'incomplete notice inventory'):
            self.verify()

    def test_duplicate_member(self):
        self.manifest.write_text(self.manifest.read_text() + self.rows[self.victim] + '\n')
        with self.assertRaisesRegex(ValueError, 'duplicate notice member'):
            self.verify()

    def test_unexpected_member(self):
        self.manifest.write_text(self.manifest.read_text() + '0'*64 + '  extra/LICENSE\n')
        with self.assertRaisesRegex(ValueError, 'unexpected notice member'):
            self.verify()

    def test_corrupt_file(self):
        (self.root/self.victim).write_text('corrupted')
        with self.assertRaisesRegex(ValueError, 'notice checksum mismatch'):
            self.verify()

    def test_invalid_digest(self):
        self.manifest.write_text(self.manifest.read_text().replace(self.rows[self.victim][:64], 'z'*64))
        with self.assertRaisesRegex(ValueError, 'malformed notice inventory'):
            self.verify()

    def test_path_escape(self):
        self.manifest.write_text('0'*64 + '  ../LICENSE\n')
        with self.assertRaisesRegex(ValueError, 'unexpected notice member'):
            self.verify()

    def test_absolute_path(self):
        self.manifest.write_text('0'*64 + '  /etc/passwd\n')
        with self.assertRaisesRegex(ValueError, 'unexpected notice member'):
            self.verify()

    def test_file_symlink(self):
        path = self.root/self.victim
        backup = self.root/'notice-original'
        path.rename(backup)
        path.symlink_to(backup)
        with self.assertRaisesRegex(ValueError, 'notice symlink is not allowed'):
            self.verify()

    def test_directory_symlink(self):
        path = self.root/'source-notices'
        backup = self.root/'original-source-notices'
        path.rename(backup)
        path.symlink_to(backup, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'notice symlink is not allowed'):
            self.verify()

    def test_manifest_symlink(self):
        backup = self.root/'inventory-original'
        self.manifest.rename(backup)
        self.manifest.symlink_to(backup)
        with self.assertRaisesRegex(ValueError, 'notice symlink is not allowed'):
            self.verify()

    def test_missing_manifest(self):
        self.manifest.unlink()
        with self.assertRaisesRegex(ValueError, 'missing notice file'):
            self.verify()

if __name__ == '__main__':
    unittest.main(verbosity=2)
