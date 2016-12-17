import os
import errdatadog
from errbot.backends.test import testbot

class TestDataDogBot(object):
    extra_plugin_dir = '.'

    def test_hello(self, testbot):
        testbot.push_message('!ddog list')
        assert ':thinking_face: Maybe you could should make a saved graph first before listing them?' in testbot.pop_message()
