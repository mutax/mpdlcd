# -*- coding: utf-8 -*-
# Copyright (c) 2011-2012 Raphaël Barrois

import logging
import mpd
import time
import socket


logger = logging.getLogger(__name__)

STATE_PLAY = 'play'
STATE_STOP = 'stop'


class MPDError(Exception):
    pass


class MPDConnectionError(MPDError):
    pass


class MPDClient(object):

    def __init__(self, host='localhost', port='6600'):
        self._client = mpd.MPDClient()
        self._connected = False
        self.host = host
        self.port = port

    def connect(self, retries=3, wait=3):
        if not self._connected:
            logger.info('Connecting to MPD server at %s:%s', self.host, self.port)
            for _ in xrange(retries):
                try:
                    self._client.connect(host=self.host, port=self.port)
                except socket.error as e:
                    logger.warning('Unable to connect to MPD server %s:%s: %s',
                        self.host, self.port, e)
                    time.sleep(wait)
                else:
                    self._connected = True
                    return
            logger.error('Unable to connect to MPD %s:%s after %d attempts.',
                self.host, self.port, retries)
            raise MPDConnectionError('Unable to connect to MPD at %s:%s' %
                    (self.host, self.port))

    @property
    def status(self):
        return self._client.status()

    @property
    def random(self):
        logger.debug('Fetching MPD random state')
        return self.status['random'] == 1

    @property
    def repeat(self):
        logger.debug('Fetchin MPD repeat state')
        return self.status['repeat'] == 1

    def _parse_time(self, time):
        try:
            return int(time)
        except ValueError:
            return None

    @property
    def elapsed(self):
        logger.debug('Fetching MPD elapsed time')
        time = self.status.get('time')
        return self._parse_time(time.split(':')[0])

    @property
    def total(self):
        logger.debug('Fetching MPD total time')
        time = self.status.get('time')
        return self._parse_time(time.split(':')[-1])

    @property
    def elapsed_and_total(self):
        logger.debug('Fetching MPD elapsed and total time')
        time = self.status.get('time')
        if ':' in time:
            elapsed, total = time.split(':', 1)
            return self._parse_time(elapsed), self._parse_time(total)
        else:
            return (None, None)

    @property
    def state(self):
        logger.debug('Fetching MPD state')
        return self.status['state']

    @property
    def current_song(self):
        logger.debug('Fetching MPD song information')
        return MPDSong(**self._client.currentsong())


class MPDSong(object):

    def __init__(self, **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)

    def format(self, fmt='{artist} - {title}'):
        return fmt.format(
                title=self.title,
                artist=self.artist,
                )
