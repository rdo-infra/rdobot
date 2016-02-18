rdobot - An IRC bot for RDO things
==================================
NOTE: This is a work in progress!

Installing
----------

    yum install python-pip libffi-devel python-devel "@Development Tools"

    pip install -r requirements.txt

Configuring
-----------

Need to configure the Webserver plugin so Errbot listens for webhooks:

    !plugin config Webserver {'HOST': '127.0.0.1', 'PORT': 3142}

Note: Webhooks are not protected and should have a web server in front (i.e,
nginx).

Otherwise the remainder of the configuration is pretty straightforward in
config.py.

Running
-------

    # With IRC backend configuration

    errbot -c rdobot/config.py

    # With text backend (will not connect to chat, useful for development)

    errbot -c rdobot/config.py -T

Sensu Config
------------
See ``contrib/errbot.json`` for a sample handler configuration.
See ``contrib/errbot.py`` for the handler script.

Sensu sends a JSON as stdin to the handler script.
The script just does a HTTP POST with the JSON to errbot at the specified
--endpoint parameter.

From there, the errbot plugin, ``rdobot/plugins/sensu/errbot-sensu.py`` takes
over.

When the handler receives a new event for a check, it will verify if the check
has a "broadcast" key configured. This "broadcast" key would contain a list of
IRC channels interested in this check.

The bot will only notify the channel if there is a match between the channel
in the check broadcast and if it is configured in config.py as
MONITORING_BROADCAST_CHANNELS.

For example, if a check is configured to broadcast to #rdo but #rdo is not in
MONITORING_BROADCAST_CHANNELS, the bot will not post there.

It's sort of a whitelist and foolproof two-sided authentication so we're not
spamming left and right on accident.

Commands
--------
Not a lot of stuff implemented so far, but most of the work (except the
commands!) is done.

    # Returns URL to Uchiwa

    !sensu dashboard

    # Returns which clients are monitored

    !sensu clients

    # Returns info about a client

    !sensu client <client>
