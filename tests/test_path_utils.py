from better_test_case import BetterTestCase
from utils.path_utils import Path, encode_for_url, decode_from_url, join_paths, parse_query_string


class MySuite(BetterTestCase):

    def test_path_matcher(self):
        p = Path("/configuration-service/users/{userId}")
        match = p.matches("/configuration-service/users/the-user-id")
        self.assertEqual({'userId': 'the-user-id'}, match)

        self.assertIsNone(p.matches("/configuration-service/users/the-user-id/nope"))

        p = Path("/configuration-service/users")
        self.assertHasLength(0, p.matches("/configuration-service/users"))

        self.assertRaises(ValueError, lambda: Path("/configuration-service/users/{userId}/blah/{userId}"))

    def test_encode_for_url(self):
        self.assertEqual("foo%2Fbar", encode_for_url("foo/bar"))
        self.assertEqual("foo/bar", decode_from_url("foo%2Fbar"))

    def test_join_paths(self):
        self.assertEqual("a/b", join_paths("a", "b"))
        self.assertEqual("a/b", join_paths("a", "/b"))
        self.assertEqual("a/b", join_paths("a/", "/b"))

    def test_parse_query_string(self):
        self.assertIsNone(parse_query_string(None))
        self.assertHasLength(0, parse_query_string(""))
        self.assertEqual({'one': '1', 'two': '2'}, parse_query_string("one=1&two=2"))
        self.assertEqual({'one': '1', 'two': '2'}, parse_query_string({'one': '1', 'two': '2'}))
