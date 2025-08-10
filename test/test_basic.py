import unittest
from barcode_lib.reader import BarcodeReader
class T(unittest.TestCase):
    def test_main(self):
        r=BarcodeReader(); self.assertIsNotNone(r)
if __name__=='__main__': unittest.main()
