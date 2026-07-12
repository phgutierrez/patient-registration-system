import unittest

from src.password_policy import generate_pin, is_valid_pin


class PasswordPolicyTests(unittest.TestCase):
    def test_pin_requires_exactly_six_digits(self):
        self.assertTrue(is_valid_pin('012345'))
        for invalid in ('12345', '1234567', 'abcdef', '12 345', ''):
            with self.subTest(invalid=invalid):
                self.assertFalse(is_valid_pin(invalid))

    def test_generated_pin_preserves_six_digit_shape(self):
        for _ in range(20):
            pin = generate_pin()
            self.assertEqual(6, len(pin))
            self.assertTrue(pin.isdigit())
