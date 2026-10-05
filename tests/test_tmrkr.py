from pathlib import Path
import tempfile
import unittest

import tmrkr


class HelpersTest(unittest.TestCase):
    def test_qt_value(self):
        self.assertEqual(
            tmrkr.qt_value(r"@ByteArray(C:\\Games\\Fallout 4)"),
            r"C:\Games\Fallout 4",
        )

    def test_safe_relative_rejects_parent(self):
        with self.assertRaises(ValueError):
            tmrkr.safe_relative("../Data/Fallout4.esm")

    def test_sha256(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "x"
            path.write_bytes(b"abc")
            self.assertEqual(
                tmrkr.sha256(path),
                "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
            )


if __name__ == "__main__":
    unittest.main()
