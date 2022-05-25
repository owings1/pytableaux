# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2022 Doug Owings.
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import annotations
"""
pytableaux.web.mail
-------------------

"""

__all__ = ('Mailroom',)

import re
import smtplib
import ssl
import threading
import time
from collections import deque
from typing import TYPE_CHECKING, Any, Callable, Mapping, Sequence

from pytableaux import errors, web
from pytableaux.errors import Emsg, check
from pytableaux.tools.mappings import MapProxy

if TYPE_CHECKING:
    import logging

re_email = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
'Email regex.'

def is_valid_email(value: str) -> bool:
    "Whether a string is a valid email address."
    return re_email.fullmatch(value) is not None

def validate_feedback_form(form_data: dict[str, str]) -> None:
    "Validate `name`, `email`, and `message` keys."
    errs = {}
    if not is_valid_email(form_data['email']):
        errs['Email'] = 'Invalid email address'
    if not len(form_data['name']):
        errs['Name'] = 'Please enter your name'
    if not len(form_data['message']):
        errs['Message'] = 'Please enter a message'
    if errs:
        raise errors.RequestDataError(errs)

class Mailroom:

    config: Mapping[str, Any]
    "Instance config."

    logger: logging.Logger
    "Logger instance."

    loaded: bool
    "Whether the config has been loaded, including TLS, etc."

    should_stop: bool
    "Flag to signal background thread to exit."

    last_was_success: bool
    "Whether the last email attempt was successful."

    queue: deque
    "The main message job queue."

    failqueue: deque
    "The queue of message jobs that have failed."

    tlscontext: ssl.SSLContext|None
    "TLS config context."

    _thread: threading.Thread

    def __init__(self, config: Mapping[str, Any]):

        self.config = MapProxy(config)
        self.logger = web.get_logger(self, self.config)

        self.queue = deque()
        self.failqueue = deque()

        self.loaded = False
        self.should_stop = False
        self.last_was_success = True

        self.tlscontext = None
        self._thread = None

        # Validate email addresses in config if applicable.
        if self.enabled and config['feedback_enabled']:
            for key in ('feedback_to_address', 'feedback_from_address'):
                addr = config[key]
                if not addr:
                    raise errors.ConfigError(f"Feedback enabled but '{key}' not set")
                if not is_valid_email(addr):
                    raise errors.ConfigError(f"Invalid email for '{key}': '{addr}'")

    @property
    def enabled(self):
        "Whether SMTP is enabled in the config."
        return bool(self.config['smtp_host'])

    @property
    def tls_enabled(self):
        "Whether TLS is enabled in the config."
        return bool(self.config['smtp_starttls'])

    @property
    def auth_enabled(self):
        "Whether SMTP authentication enabled in the config."
        return bool(self.config['smtp_username'])

    @property
    def running(self):
        "Whether the background thread is running."
        return self._thread is not None and self._thread.is_alive()

    def start(self):
        "Start the mailroom background thread."

        if self.running:
            raise Emsg.ThreadRuning()
        if not self.loaded:
            self._load()
        if not self.enabled:
            return

        def process_queue():

            sent, tried = process_mail(
                queue = self.queue,
                failqueue = self.failqueue,
                logger = self.logger,
                connect = self._connect
            )
            if sent > 0:
                self.last_was_success = True
            elif tried > 0:
                self.last_was_success = False

        def requeue():
            "Put all failed messages back in the queue."
            queue = self.queue
            failqueue = self.failqueue
            self.logger.info(f'Requeuing {len(failqueue)} failed messages')
            queue.extend(failqueue)
            failqueue.clear()

        def quit():
            logger = self.logger
            queue = self.queue
            logger.info('Received quit signal, stopping')
            if queue:
                logger.warning(f'Dumping {len(queue)} unprocessed messages')
                try:
                    logger.warning(_dump_queue(queue))
                except Exception as e:
                    logger.error(e)

        config = self.config
        interval: int = config['mailroom_interval']
        rq_interval: int = config['mailroom_requeue_interval']

        def loop():

            self.logger.info(f'Starting interval {interval}s, requeue {rq_interval}s')

            # TODO: Use a stopwatch instead of just counting ticks.

            # Ticks since main queue checked.
            tick = 0
            # Ticks since failqueue checked.
            rq_tick = 0

            while True:

                if rq_tick >= rq_interval:
                    if len(self.failqueue):
                        requeue()
                    rq_tick = 0

                if tick >= interval:
                    if len(self.queue):
                        process_queue()
                    tick = 0

                while tick < interval:
                    time.sleep(1)
                    if self.should_stop:
                        quit()
                        return
                    tick += 1
                    rq_tick += 1

        def target():
            try:
                loop()
            except:
                raise
            finally:
                pass

        self.should_stop = False
        thread = self._thread = threading.Thread(target = target, daemon = True)
        if self.running:
            raise Emsg.ThreadRuning()
        thread.start()

    def stop(self, timeout: float = None):
        if not self.running:
            raise Emsg.ThreadStopped()
        self.should_stop = True
        self._thread.join(timeout = timeout)
        if timeout is not None and self.running:
            raise RuntimeError('Failed to stop background thread')
        self.logger.info('Background thread stopped')

    def enqueue(self, from_addr: str, to_addrs: Sequence[str], msg: str):
        "Add a message to the queue."
        if not self.enabled:
            raise errors.ConfigError('SMTP not configured, cannot enqueue message')
        if not is_valid_email(from_addr):
            raise ValueError(f"Invalid from_addr: {from_addr}")
        if not len(to_addrs):
            raise ValueError(f"to_addrs cannot be empty")
        for addr in to_addrs:
            if not is_valid_email(addr):
                raise ValueError(f"Invalid to_addr: {addr}")
        check.inst(msg, str)
        if not self.running:
            self.logger.warn("Background thread not running, enqueuing anyway")
        job = dict(from_addr = from_addr, to_addrs = to_addrs, msg = msg)
        self.queue.append(job)

    def _load(self):
        logger = self.logger
        if not self.enabled:
            logger.warn('SMTP not configured, Mailroom is disabled.')
            return
        logger.info('Intializing SMTP settings')
        if self.tls_enabled:
            self._load_tlsconfig()
        else:
            logger.warn('TLS disabled for SMTP, messages will NOT be encrypted')
        self.loaded = True

    def _load_tlsconfig(self):
        config = self.config
        logger = self.logger
        self.tlscontext = ssl.SSLContext()
        if config['smtp_tlscertfile']:
            logger.info('Loading TLS client certificate for SMTP')
            self.tlscontext.load_cert_chain(
                config['smtp_tlscertfile'],
                keyfile = config['smtp_tlskeyfile'],
                password = config['smtp_tlskeypass'],
            )

    def _connect(self) -> smtplib.SMTP:
        config = self.config
        logger = self.logger
        host = config['smtp_host']
        port = config['smtp_port']
        logger.info(f'Connecting to SMTP server {host}:{port}')
        smtp = smtplib.SMTP(host, port, config['smtp_helo'])
        smtp.ehlo()
        if self.tls_enabled:
            logger.info('Starting SMTP TLS session')
            resp = smtp.starttls(context = self.tlscontext)
            logger.debug(f'Starttls response: {resp}')
        else:
            logger.warn('TLS disabled, not encrypting email')
        if self.auth_enabled:
            username = config['smtp_username']
            password = config['smtp_password']
            logger.debug(f'Logging into SMTP with user {username}')
            smtp.login(username, password)
        return smtp


def process_mail(*, queue: deque, failqueue: deque, logger: logging.Logger, connect: Callable[[], smtplib.SMTP]) -> tuple[int, int]:

    if not len(queue):
        logger.error('No mail to process.')
        return

    requeue = deque()
    tried = sent = failed = 0

    try:
        try:
            smtp = connect()
        except:
            smtp = None
            # All messages fail on connection fail.
            requeue.extend(queue)
            queue.clear()
            raise
        else:
            while len(queue):
                job = queue.popleft()
                tried += 1
                total = len(queue) + tried
                try:
                    logger.info(f'Sending message {tried} of {total}')
                    smtp.sendmail(**job)
                except Exception as err:
                    failed += 1
                    logger.error(
                        f'Sendmail failed with error: {err}',
                        exc_info = err, stack_info = True
                    )
                    requeue.append(job)
                else:
                    sent += 1

    except Exception as err:
        logger.error(
            f'SMTP failed with error: {err}',
            exc_info = err, stack_info = True
        )

    finally:
        if smtp is not None:
            logger.info('Disconnecting from SMTP server')
            try:
                smtp.quit()
            except Exception as err:
                logger.warn(
                    f'Failed to quit SMTP connection: {err}',
                    exc_info = err, stack_info = True
                )

    if len(requeue):
        logger.info(f'Requeuing {len(requeue)} failed messages')
        failqueue.extend(requeue)

    return sent, tried


def _dump_queue(queue):
    return '\n'.join(
        [
            '\n', *[str(job['msg']) for job in queue]
        ]
    )
