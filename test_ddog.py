import os
import ddog
import unittest
import mock
from errbot.backends.test import testbot

class TestDatadog(object):
    extra_plugin_dir = '.'

    def test_ddog_config_api_key(self, testbot):
        testbot.push_message('!plugin config ddog')
        assert 'DATADOG_API_KEY' in testbot.pop_message()

    def test_ddog_config_app_key(self, testbot):
        testbot.push_message('!plugin config ddog')
        assert 'DATADOG_APP_KEY' in testbot.pop_message()

    def test_ddog_save_item(self, testbot):
        testbot.push_message('!ddog save test-list avg:some.fake.metric{*}')
        assert 'The graph test-list has been saved' in testbot.pop_message()

    def test_ddog_save_duplicate_item(self, testbot):
        testbot.push_message('!ddog save test-list avg:some.fake.metric{*}')
        testbot.push_message('!ddog save test-list avg:some.fake.metric{*}')
        testbot.pop_message()  # pop the first message off the queue saying the save was ok
        assert 'The graph test-list already exists as a saved query' in testbot.pop_message()

    def test_ddog_delete_item_doesnt_exist(self, testbot):
        testbot.push_message('!ddog delete test1')
        assert 'The query test1 was not in the list to delete.' in testbot.pop_message()

    def test_ddog_delete_item(self, testbot):
        testbot.push_message('!ddog save test-list avg:some.fake.metric{*}')
        testbot.pop_message()  # pop the first message off the queue saying the save was ok
        testbot.push_message('!ddog delete test-list')
        assert 'Annnnd its gone. test-list was deleted' in testbot.pop_message()

    def test_ddog_list_with_no_items(self, testbot):
        testbot.push_message('!ddog list')
        assert 'Maybe you could should make a saved graph first before listing them?' in testbot.pop_message()

    def test_ddog_list_with_item(self, testbot):
        testbot.push_message('!ddog save test-list avg:some.fake.metric{*}')
        testbot.pop_message()  # pop the first message off the queue saying the save was ok
        testbot.push_message('!ddog list')
        assert 'Found 1 saved queries:' in testbot.pop_message()

    def test_ddog_add_to_querystore_once(self,testbot):
        plugin = testbot.bot.plugin_manager.get_plugin_obj_by_name('ddog')
        result = plugin.add_to_querystore('name', 'sum:myquery', 1)
        assert result == True

    def test_ddog_add_to_querystore_duplicate(self,testbot):
        plugin = testbot.bot.plugin_manager.get_plugin_obj_by_name('ddog')
        first = plugin.add_to_querystore('name', 'sum:myquery', 1)
        second = plugin.add_to_querystore('name', 'sum:myquery', 1)
        assert second == False # doesn't allow duplicate names

    def test_ddog_delete_from_querystore_doenst_exist(self,testbot):
        plugin = testbot.bot.plugin_manager.get_plugin_obj_by_name('ddog')
        result = plugin.delete_from_querystore('test')
        assert result == False # doesn't allow duplicate names
