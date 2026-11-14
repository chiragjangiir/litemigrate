import unittest
from litemigrate.json_norm import canonicalize_json


class TestJsonNormalization(unittest.TestCase):
    def test_canonical_object_keys(self):
        raw = '{"z": 1, "a": 2, "m": 3}'
        expected = '{"a":2,"m":3,"z":1}'
        self.assertEqual(canonicalize_json(raw), expected)

    def test_nested_canonical_objects(self):
        raw = '{"users": [{"b": 2, "a": 1}], "count": 1}'
        expected = '{"count":1,"users":[{"a":1,"b":2}]}'
        self.assertEqual(canonicalize_json(raw), expected)

    def test_array_preserves_order(self):
        raw = '[3, 1, 2]'
        expected = '[3,1,2]'
        self.assertEqual(canonicalize_json(raw), expected)

    def test_whitespace_normalization(self):
        raw = """{
            "key":   "value"   ,
            "list": [ 1 , 2 ]
        }"""
        expected = '{"key":"value","list":[1,2]}'
        self.assertEqual(canonicalize_json(raw), expected)

    def test_non_json_strings_passthrough(self):
        self.assertEqual(canonicalize_json("plain text"), "plain text")
        self.assertEqual(canonicalize_json(None), None)

    def test_malformed_json_fallback(self):
        malformed = '{"key": incomplete'
        self.assertEqual(canonicalize_json(malformed), malformed)

    def test_bytes_input(self):
        raw = b'{"hello": "world"}'
        self.assertEqual(canonicalize_json(raw), '{"hello":"world"}')


if __name__ == "__main__":
    unittest.main()
