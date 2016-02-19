from errbot import BotPlugin, botcmd, webhook

import logging
from pysensu.api import SensuAPI


class ErrbotSensu(BotPlugin):
    """An Err Sensu Monitoring plugin"""
    min_err_version = '3.2.2'
    max_err_version = '9.9.9'

    def activate(self):
        """
        Triggers on plugin activation
        """
        super(ErrbotSensu, self).activate()
        endpoint = self.bot_config.MONITORING_ENDPOINT
        username = self.bot_config.MONITORING_USERNAME
        password = self.bot_config.MONITORING_PASSWORD

        self.sensu = SensuAPI(endpoint, username=username, password=password)

    def deactivate(self):
        """
        Triggers on plugin deactivation
        """
        super(ErrbotSensu, self).deactivate()

    def get_configuration_template(self):
        """
        Defines the configuration structure this plugin supports
        """
        return {'endpoint': u'sensu-api.tld:4567'}

    def callback_connect(self):
        """
        Triggers when bot is connected
        """
        pass

    def callback_message(self, message):
        """
        Triggered for every received message that isn't coming from the bot
        """
        pass

    def callback_botmessage(self, message):
        """
        Triggered for every message that comes from the bot itself
        """
        pass

    # Bot commands
    @botcmd(split_args_with=None)
    def sensu_dashboard(self, msg, args):
        """
        Returns the URL to the sensu dashboard
        Sample:
            !sensu dashboard
        """
        dashboard = self.bot_config.MONITORING_DASHBOARD
        username = self.bot_config.MONITORING_DASHBOARD_USERNAME
        password = self.bot_config.MONITORING_DASHBOARD_PASSWORD
        msg = "The Uchiwa dashboard is available at: {0} (credentials: {1}/{2})"
        self._monitoring_broadcast(msg.format(dashboard, username, password))

    @botcmd(split_args_with=None)
    def sensu_clients(self, msg, args):
        """
        Returns the list of clients
        Sample:
            !sensu clients
        """
        clients = self.sensu.get_clients()
        client_names = [ client['name'] for client in clients ]
        client_names = ', '.join(client_names)
        self._monitoring_broadcast("Clients: {0}".format(client_names))

    @botcmd(split_args_with=None)
    def sensu_client(self, msg, args):
        """
        Returns details of a client
        Sample:
            !sensu client <client>
        """
        client_name = args[0]
        client = self.sensu.get_client_data(client_name)
        self._monitoring_broadcast("Client details: {0}".format(client_name))
        for param in client:
            self._monitoring_broadcast("{0}: {1}".format(param,
                                                         str(client[param])))

    # Plugin endpoints
    @webhook
    def event(self, kwargs):
        host_params = ['action', 'client', 'check', 'occurrences', 'timestamp']
        params = {
            param: kwargs.get(param, None)
            for param in host_params
        }

        logging.info("Received request on host endpoint: " + str(params))
        logging.debug("Unpacked parameters:" + str(kwargs))

        hostname = params['client']['name']
        address = params['client']['address']
        check = params['check']['name']
        output = params['check']['output']

        # Custom attributes
        # datacenter is a custom client attribute for Uchiwa links
        datacenter = params['client']['datacenter']
        # broadcast is a custom check attribute for possible
        try:
            broadcast = params['check']['broadcast']
        except KeyError:
            broadcast = '#undef'

        dashboard = self.bot_config.MONITORING_DASHBOARD
        check_url = "{0}/#/client/{1}/{2}?check={3}".format(dashboard,
                                                            datacenter,
                                                            hostname,
                                                            check)

        msg_type = {
            'create': "NEW PROBLEM: {0} ({1}): {2} @ {3}",
            'resolve': "RESOLVED PROBLEM: {0} ({1}): {2} @ {3}",
            'flapping': "FLAPPING PROBLEM: {0} ({1}): {2} @ {3}",
            'unknown': "UNKNOWN PROBLEM: {0} ({1}): {2} @ {3}"
        }

        if params['action'] in msg_type:
            msg = msg_type[params['action']].format(hostname, address, check,
                                                    check_url)
        else:
            msg = msg_type['unknown'].format(hostname, address, check,
                                             check_url)

        self._monitoring_broadcast(msg, broadcast)
        self._monitoring_broadcast(output, broadcast)

    def _monitoring_broadcast(self, msg, broadcast=None):
        # If a broadcast channel is configured for a sensu check, broadcast to
        # it if it is configured to be a broadcast channel.
        for room in self.bot_config.MONITORING_BROADCAST_CHANNELS:
            if broadcast is None or room in broadcast:
                self.send(room, '[sensu] ' + msg, message_type='groupchat')
