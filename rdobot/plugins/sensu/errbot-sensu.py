from errbot import BotPlugin, botcmd, webhook

import logging
from pysensu.api import SensuAPI
from pyshorteners import Shortener


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
        message = "The Uchiwa dashboard is available at: {0} (credentials: {1}/{2})"
        return message.format(dashboard, username, password)

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

        return "Clients: {0}".format(client_names)

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
            yield "{0}: {1}".format(param, str(client[param]))

    # Plugin endpoints
    @webhook
    def sensu_event(self, kwargs):
        host_params = ['action', 'client', 'check', 'occurrences', 'timestamp']
        params = {
            param: kwargs.get(param, None)
            for param in host_params
        }

        logging.info("Received request on host endpoint: " + str(params))
        logging.debug("Unpacked parameters:" + str(kwargs))

        hostname = params['client']['name']
        check = params['check']['name']
        output = self._truncate_string(params['check']['output'], length=250)

        # Custom attributes
        # datacenter is a custom client attribute for Uchiwa links
        datacenter = params['client']['datacenter']
        # broadcast is a custom check attribute to know where to send IRC notifications
        try:
            if 'broadcast' in params['check']:
                broadcast = params['check']['broadcast']
            elif 'custom' in params['check'] and 'broadcast' in params['check']['custom']:
                broadcast = params['check']['custom']['broadcast']
            else:
                logging.info("This notification does not have a broadcast assigned, not doing anything with it.")
                return False
        except KeyError as e:
            logging.info("KeyError when trying to set broadcast config: " + str(e))
            return False

        dashboard = self.bot_config.MONITORING_DASHBOARD
        check_url = "{0}/#/client/{1}/{2}?check={3}".format(dashboard,
                                                            datacenter,
                                                            hostname,
                                                            check)
        shortener = Shortener('Tinyurl')
        check_url = shortener.short(check_url)

        msg_type = {
            'create': "NEW: {0} - {1} @ {2} |#| {3}",
            'resolve': "RESOLVED: {0} - {1} @ {2} |#| {3}",
            'flapping': "FLAPPING: {0} - {1} @ {2} |#| {3}",
            'unknown': "UNKNOWN: {0} - {1} @ {2} |#| {3}"
        }

        if params['action'] in msg_type:
            msg = msg_type[params['action']].format(hostname, check, check_url,
                                                    output)
        else:
            msg = msg_type['unknown'].format(hostname, check, check_url,
                                             output)

        self._monitoring_broadcast(msg, broadcast=broadcast)

    def _monitoring_broadcast(self, msg, broadcast=None):
        if broadcast is None:
            return False

        for room in self.bot_config.MONITORING_BROADCAST_CHANNELS:
            if room == broadcast:
                msg = self._truncate_string('[sensu] ' + msg)
                self.send(room, msg, message_type='groupchat')

    @staticmethod
    def _truncate_string(message, length=460):
        """
        Helper method to truncate messages too long for IRC
        :param message: message
        :param length: max length
        :return:
        """
        if len(message) > length:
            return message[:length] + " [...]"
        return message
