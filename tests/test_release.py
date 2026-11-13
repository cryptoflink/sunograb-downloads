"""Check the distribution files in dist/ before publishing a release."""
import hashlib
import unittest
import zipfile
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    'SunoGrab-Setup.exe': 74593935,
    'SunoGrab-Portable.zip': 102161529,
}


class ReleaseTests(unittest.TestCase):
    def test_published_checksums_match_the_reviewed_artifacts(self):
        rows = [line.split() for line in (ROOT / 'SHA256SUMS.txt').read_text('utf-8').splitlines()]
        self.assertEqual({name for _, name in rows}, set(EXPECTED))
        for digest, name in rows:
            with self.subTest(asset=name):
                path = ROOT / 'dist' / name
                self.assertEqual(path.stat().st_size, EXPECTED[name])
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), digest)

    def test_portable_has_only_distribution_resources(self):
        with zipfile.ZipFile(ROOT / 'dist/SunoGrab-Portable.zip') as archive:
            self.assertIsNone(archive.testzip())
            files = [PurePosixPath(name) for name in archive.namelist() if not name.endswith('/')]
            # 91 fichiers : 1 exe + 84 _internal + 3 bin (ffmpeg+licence+notice) + 3 tutos.
            # (v1.12 : PyInstaller ne recopie plus les 43 stubs api-set UCRT,
            #  fournis par le systeme Windows 10/11 ; aucun module reel perdu.)
            self.assertEqual(len(files), 91)
            self.assertTrue(all(path.parts[0] == 'SunoGrab' for path in files))
            self.assertEqual({path.parts[1] for path in files}, {
                'SunoGrab.exe', '_internal', 'bin', 'Tutoriel.txt', 'Tutoriel_EN.txt', 'Tutoriel_DE.txt',
            })
            forbidden = {'settings', 'queue', 'runtime', 'cookies', 'session'}
            for path in files:
                self.assertFalse(any(part.lower().split('.')[0] in forbidden for part in path.parts), str(path))
                self.assertNotIn(path.suffix.lower(), {'.mp3', '.mp4', '.m4a', '.wav', '.log', '.har'})
            self.assertIn(PurePosixPath('SunoGrab/bin/FFmpeg-LICENSE.txt'), files)
            self.assertIn(PurePosixPath('SunoGrab/bin/FFmpeg-NOTICE.txt'), files)


if __name__ == '__main__':
    unittest.main()
