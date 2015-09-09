# Python
from unittest import main, TestCase

# Local
from utils import convert_byte_size

class ConvertByteSizeTestCase(TestCase):
    def setUp(self):
        self._size1 = None
        self._size2 = -1
        self._size3 = 0
        self._size4 = 1000
        self._size5 = 1000000

    def test_none_size(self):
        with self.assertRaises(TypeError):
            convert_byte_size(self._size1)

    def test_negative_size(self):
        with self.assertRaises(ValueError):
            convert_byte_size(self._size2)
    
    def test_zero_size(self):
        self.assertEqual(convert_byte_size(self._size3), '0B')

    def test_kilobyte(self):
        self.assertEqual(convert_byte_size(self._size4), '1.0KB')

    def test_megabyte(self):
        self.assertEqual(convert_byte_size(self._size5), '1.0MB')

if __name__ == '__main__':
    main()
