from errbot import BotPlugin, botcmd, arg_botcmd, webhook, templating
from errbot.utils import ValidationException
from datadog import initialize, api
import time
import json
import requests


def initialize_datadog_api(api_key, app_key):
    options = {
        'api_key': api_key,
        'app_key': app_key
    }

    initialize(**options)


def send_datadog_style_attachment(self, message, snapshot_url, fields=None):
    """
    Sends an attachment back to the user that looks Datadog-esk.
    """
    # wait for image to be created
    wait_for_datadog_image_to_load(snapshot_url)

    # create fields to be sent
    if fields:
        fields_array = []

        for key, value in fields.items():
            fields_array.append([key, value])
    else:
        fields_array = None

    self.send_card(image=snapshot_url,
                   color='#5d53ed',
                   fields=fields_array,
                   in_reply_to=message)


def wait_for_datadog_image_to_load(url):
    """
    Waits for the DataDog linked image to be ready
    """
    req_bytes = 0

    while req_bytes < 1024:
        result = requests.get(url)
        req_bytes = len(result.content)
        time.sleep(0.5)

    return


def ez_cpu_graph(hostname):
    graph_def = {
        "viz": "timeseries",
        "requests": [
            {
                "q": "avg:system.cpu.idle{host:REPLACEME}, avg:system.cpu.system{host:REPLACEME}, avg:system.cpu.iowait{host:REPLACEME}, avg:system.cpu.user{host:REPLACEME}, avg:system.cpu.stolen{host:REPLACEME}, avg:system.cpu.guest{host:REPLACEME}",
                "type": "area",
                "conditional_formats": []
            }
        ]
    }

    graph_def = json.dumps(graph_def, separators=(',', ':'))
    return graph_def.replace("REPLACEME", hostname)


def ez_mem_graph(hostname):
    graph_def = {
        "viz": "timeseries",
        "requests": [
            {
                "q": "avg:system.mem.free{host:REPLACEME}, avg:system.mem.used{host:REPLACEME}",
                "type": "area",
                "conditional_formats": []
            }
        ]
    }

    graph_def = json.dumps(graph_def, separators=(',', ':'))
    return graph_def.replace("REPLACEME", hostname)


def ez_hdd_graph(hostname):
    graph_def = {
        "viz": "toplist",
        "requests": [
            {
                "q": "system.disk.in_use{host:REPLACEME} by {host,device} * 100",
                "style": {
                    "palette": "dog_classic"
                },
                "conditional_formats": [
                    {
                        "palette": "white_on_red",
                        "value": 95,
                        "comparator": ">"
                    },
                    {
                        "palette": "white_on_yellow",
                        "value": 75,
                        "comparator": ">="
                    },
                    {
                        "palette": "white_on_green",
                        "value": 75,
                        "comparator": "<"
                    }
                ]
            }
        ]
    }

    graph_def = json.dumps(graph_def, separators=(',', ':'))
    return graph_def.replace("REPLACEME", hostname)


class datadog(BotPlugin):
    """
    DataDog Snapshot
    """

    def add_to_querystore(self, name, query, hours):
        """
        Add an item to QUERYSTORE
        """

        # lowercase the name
        name = str.lower(name)

        # make an array if it doesn't exist
        if 'QUERY_STORE' not in self:
            self['QUERY_STORE'] = []

        name_already_exists = False

        # return if the name for the query has been found
        for saved_queries in self['QUERY_STORE']:
            if saved_queries['name'] == name:
                name_already_exists = True
                break

        if name_already_exists:
            return False # no change made as it already exists
        else:
            # grab the current store
            list_of_saved_queries = self['QUERY_STORE']

            # add to the current store
            list_of_saved_queries.append({
                'name': name,
                'query': query,
                'hours': hours
            })

            # need to use this method of saving the data
            # http://errbot.io/en/latest/user_guide/plugin_development/persistence.html
            self['QUERY_STORE'] = list_of_saved_queries

            return True # change made

    def delete_from_querystore(self, name):
        """
        Add an item to QUERYSTORE
        """

        temp_list = []

        query_deleted = False
        for query in self['QUERY_STORE']:
            if query['name'] == name:
                # found something that should be deleted
                query_deleted = True
            else:
                # should be kept, add to new list
                temp_list.append(query)

        self['QUERY_STORE'] = temp_list

        # return True if something was deleted
        return query_deleted

    def get_from_querystore(self, name):
        """
        Get an item from QUERYSTORE
        """

        # lowercase the name
        name = str.lower(name)

        # return if the name for the query has been found
        for saved_queries in self['QUERY_STORE']:
            if saved_queries['name'] == name:
                return saved_queries

        # nothing found
        return False

    def get_configuration_template(self):
        """
        Defines the DataDog configuration
        """
        return {'DATADOG_API_KEY': "xxxxxxxxxxxxxxx",
                'DATADOG_APP_KEY': "xxxxxxxxxxxxxxxxx"}

    def check_configuration(self, config):
        for key in ['DATADOG_API_KEY', 'DATADOG_APP_KEY']:
            if key not in config:
                raise ValidationException("missing config value: " + key)

    @arg_botcmd('hostname', type=str, template="search")
    def ddog_search(self, message, hostname=None):
        """
        Search DataDog inventory for hosts
        """

        initialize_datadog_api(self.config['DATADOG_API_KEY'],
                               self.config['DATADOG_APP_KEY'])

        # need to search for what the user asked in upper and lower case
        # the datadog api is case sensitive
        search_string_lower = "hosts:{hostname}".format(
            hostname=str.lower(hostname))
        search_string_upper = "hosts:{hostname}".format(
            hostname=str.upper(hostname))

        response_lower = api.Infrastructure.search(q=search_string_lower)
        response_upper = api.Infrastructure.search(q=search_string_upper)

        all_hosts = response_lower['results'][
            'hosts'] + response_upper['results']['hosts']

        return {'hosts': all_hosts}

    @arg_botcmd('metric_type', type=str)
    @arg_botcmd('hostname', type=str)
    @arg_botcmd('--hours', dest='hours', type=int, default=1)
    def ddog_ezgraph(self, message, metric_type='cpu', hostname=None, hours=None):
        """
        A command to easily view common host based metrics
        """

        valid_metrics = ['cpu', 'mem', 'hdd']

        # create fields key value pairs
        fields = {
            'Server Name': hostname,
            'Time Window': "{hours}h".format(hours=hours)
        }

        if metric_type in valid_metrics:
            if metric_type == 'cpu':
                graph_json = ez_cpu_graph(hostname)
                fields['Graph Type'] = "CPU Usage"
                fields['Measurement'] = "Percentage (%)"

            elif metric_type == 'mem':
                graph_json = ez_mem_graph(hostname)
                fields['Graph Type'] = "Memory Usage"
                fields['Measurement'] = "Gigabytes Used (gb)"

            elif metric_type == 'hdd':
                graph_json = ez_hdd_graph(hostname)
                fields['Graph Type'] = "Disk Usage"
                fields['Measurement'] = "Percentage Used (%)"

            else:
                return "Haven't done {name} yet".format(name=metric_type)

            initialize_datadog_api(self.config['DATADOG_API_KEY'],
                                   self.config['DATADOG_APP_KEY'])

            # setup some timestamps for the graph
            end = int(time.time())
            start = end - (hours * 60 * 60)

            # grab the json result
            snap = api.Graph.create(graph_def=graph_json, start=start, end=end)

            send_datadog_style_attachment(
                self, message, snap['snapshot_url'], fields)

        else:
            return "`{metric_type}` isn't an ez metric type, try one of these `{valid_metrics}`".format(
                metric_type=metric_type,
                valid_metrics=valid_metrics,
            )

    @arg_botcmd('query', type=str)
    @arg_botcmd('--hours', dest='hours', type=int, default=1)
    def ddog_query(self, message, query=None, hours=None):
        """
        Query for a metric in DataDog
        """

        if ":" in query:
            initialize_datadog_api(self.config['DATADOG_API_KEY'],
                                self.config['DATADOG_APP_KEY'])

            # setup some timestamps for the graph
            end = int(time.time())
            start = end - (hours * 60 * 60)

            # grab the json result
            snap = api.Graph.create(metric_query=query, start=start, end=end)

            send_datadog_style_attachment(
                self, message, snap['snapshot_url'])
        else:
            yield "Hrmm `{query}` doesn't look like a DataDog query string. Maybe you need to use the **get** command".format(query=query)

    @botcmd(template="list")
    def ddog_list(self, message, args):
        """
        List saved DataDog queries
        """

        return { 'saves': self['QUERY_STORE'] }

    @arg_botcmd('name', type=str)
    def ddog_delete(self, message, name=None):
        """
        Delete a saved DataDog query.
        """

        result = self.delete_from_querystore(name)

        if result:
            yield "Annnnd its gone. `{name}` was deleted :+1:".format(name=name)
        else:
            yield "The query `{name}` was not in the list to delete.".format(name=name)


    @arg_botcmd('query', type=str)
    @arg_botcmd('name', type=str)
    @arg_botcmd('--hours', dest='hours', type=int, default=1)
    def ddog_save(self, message, query=None, name=None, hours=None):
        """
        Save a metric query so it can be recalled quickly
        """

        if ":" in query:
            name = str.lower(name)

            result = self.add_to_querystore(name, query, hours)

            if result:
                yield ":white_check_mark: The graph `{name}` has been saved".format(name=name)
            else:
                yield ":no_entry: The graph `{name}` already exists as a saved query".format(name=name)
        else:
            yield "Hrmm `{query}` doesn't look like a DataDog query string. I'm not going to save that one".format(query=query)



    @arg_botcmd('name', type=str)
    # not setting a default so it uses the saved timestamp while allowing for
    # overriding
    @arg_botcmd('--hours', dest='hours', type=int)
    def ddog_get(self, message, query=None, name=None, hours=None):
        """
        Get a metric query that has been saved
        """

        saved_query = self.get_from_querystore(name)

        if saved_query:
            initialize_datadog_api(self.config['DATADOG_API_KEY'],
                                   self.config['DATADOG_APP_KEY'])

            # if hours isn't set, used the saved hours from the user
            if not hours:
                hours = saved_query['hours']

            # setup some timestamps for the graph
            end = int(time.time())
            start = end - (hours * 60 * 60)

            fields = {
                'Saved Query Name': name,
                'Time Window': "{hours}h".format(hours=hours)
            }

            yield "Running saved query `{query}`".format(query=saved_query['query'])

            # grab the json result
            snap = api.Graph.create(metric_query=saved_query['query'], start=start, end=end)

            send_datadog_style_attachment(
                self, message, snap['snapshot_url'], fields)
        else:
            yield ":no_entry: The saved query {name} does not exist".format(name=name)
