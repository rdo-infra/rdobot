from errbot import BotPlugin, botcmd
import re

TRIPLEO = "https://www.rdoproject.org/blog/2016/02/rdo-manager-is-now-tripleo/"


class ErrbotRdo(BotPlugin):
    """An Err Sensu Monitoring plugin"""
    min_err_version = '3.2.2'
    max_err_version = '9.9.9'

    def activate(self):
        """
        Triggers on plugin activation
        """
        super(ErrbotRdo, self).activate()

    def deactivate(self):
        """
        Triggers on plugin deactivation
        """
        super(ErrbotRdo, self).deactivate()

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
        # The "message.nick" value is available on IRC backend
        # so we avoid a crash here in text backend.
        try:
            author = message.nick
        except AttributeError:
            author = '^'

        # s/rdo manager/tripleo/
        pattern = ".*(rdo manager|rdo-m\s).*"
        if re.match(pattern, message.body, re.IGNORECASE):
            response = "I think {0} meant TripleO! ( {1} )".format(author,
                                                                   TRIPLEO)
            self.send(
                message.frm,
                response,
                message_type=message.type
            )

    def callback_botmessage(self, message):
        """
        Triggered for every message that comes from the bot itself
        """
        pass
