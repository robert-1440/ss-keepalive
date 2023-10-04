from base_test import BaseTest


class AppTest(BaseTest):

    def test_internal(self):
        self.invoke_event({'foo': 'bar'})
        pass

    def setUp(self) -> None:
        super().setUp()
