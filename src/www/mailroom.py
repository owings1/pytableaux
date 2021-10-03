# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2021 Doug Owings.
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
#
# ------------------
#
# pytableaux - Web App SMTP Mailroom
import re, smtplib, ssl, threading, time, traceback
from collections import deque
from www.conf import logger, re_email
from errors import ConfigError, IllegalStateError

def is_valid_email(value):
    return re.fullmatch(re_email, value)

class Mailroom(object):

    def __init__(self, opts):
        self.opts = opts
        self.loaded = False
        self.enabled = bool(opts['smtp_host'])
        self.queue = deque()
        self.failqueue = deque()
        self.started = False
        self.should_stop = False
        self.last_was_success = True
        
    def reload(self):
        opts = self.opts
        self.enabled = bool(opts['smtp_host'])
        if not self.enabled:
            logger.warn('SMTP not enabled, not starting mailroom')
            return
        logger.info('Intializing SMTP settings')
        if opts['feedback_enabled']:
            if not opts['feedback_to_address']:
                raise ConfigError(
                    'Feedback is enabled but to address is not set'
                )
            if not opts['feedback_from_address']:
                raise ConfigError(
                    'Feedback is enabled but from address is not set'
                )
            if not is_valid_email(opts['feedback_to_address']):
                raise ConfigError(
                    'Invalid feedback to address: {0}'.format(
                        str(opts['feedback_to_address'])
                    )
                )
            if not is_valid_email(opts['feedback_from_address']):
                raise ConfigError(
                    'Invalid feedback from address: {0}'.format(
                        str(opts['feedback_from_address'])
                    )
                )
        if opts['smtp_starttls']:
            self.tlscontext = ssl.SSLContext()
            if opts['smtp_tlscertfile']:
                logger.info('Loading TLS client certificate for SMTP')
                self.tlscontext.load_cert_chain(
                    opts['smtp_tlscertfile'],
                    keyfile = opts['smtp_tlskeyfile'],
                    password = opts['smtp_tlskeypass'],
                )
        else:
            logger.warn('TLS disabled for SMTP, messages will NOT be encrypted')
        self.loaded = True

    def start(self):
        if not self.loaded:
            self.reload()
        if not self.enabled:
            return
        self.should_stop = False
        self._thread = threading.Thread(target = self.runner)
        self._thread.daemon = True
        self._thread.start()

    def enqueue(self, from_addr, to_addrs, msg):
        if not self.enabled:
            raise ConfigError('SMTP not configured, cannot enqueue message')
        self.queue.append({
            'from_addr' : from_addr,
            'to_addrs'  : to_addrs,
            'msg'       : msg,
        })

    def runner(self):
        if not self.enabled:
            raise ConfigError('SMTP not configured, cannot start Mailroom.')
        if self.started:
            raise IllegalStateError('Mailroom already running')
        self.started = True
        interval = self.opts['mailroom_interval']
        requeue_interval = self.opts['mailroom_requeue_interval']
        logger.info(
            'Starting SMTP Mailroom with interval {0}s, requeue {1}s'.format(
                str(interval), str(requeue_interval)
            )
        )
        qi = 0
        rqi = 0
        while True:
            if rqi >= requeue_interval:
                if self.failqueue:
                    logger.info(
                        'Requeuing {0} previously failed messages'.format(
                            str(len(self.failqueue))
                        )
                    )
                    self.queue.extend(self.failqueue)
                    self.failqueue.clear()
                rqi = 0
            if qi >= interval:
                self._mailproc()
                qi = 0
            while qi < interval:
                time.sleep(1)
                if self.should_stop:
                    logger.info('Mailroom received quit signal, stopping')
                    if self.queue:
                        logger.warn(
                            'Dumping {0} unprocessed messages'.format(str(len(self.queue)))
                        )
                        try:
                            logger.warn('\n'.join(['\n', *[str(job['msg']) for job in self.queue]]))
                        except Exception as e:
                            logger.error(str(e))
                    self.started = False
                    return
                qi += 1
                rqi += 1

    def _mailproc(self):
        if not self.queue:
            return
        opts = self.opts
        logger.info(
            'Connecting to SMTP server {0}:{1}'.format(
                opts['smtp_host'], str(opts['smtp_port'])
            )
        )
        smtp = None
        total = len(self.queue)
        requeue = []
        try:
            try:
                smtp = smtplib.SMTP(
                    host = opts['smtp_host'],
                    port = opts['smtp_port'],
                    local_hostname = opts['smtp_helo'],
                )
                smtp.ehlo()
                if opts['smtp_starttls']:
                    logger.info('Starting SMTP TLS session')
                    resp = smtp.starttls(context = self.tlscontext)
                    logger.debug('Starttls response: {0}'.format(str(resp)))
                else:
                    logger.warn('TLS disabled, not encrypting email')
                if (opts['smtp_username']):
                    logger.debug(
                        'Logging into SMTP server with {0}'.format(
                            opts['smtp_username']
                        )
                    )
                    smtp.login(opts['smtp_username'], opts['smtp_password'])
            except:
                requeue.extend(self.queue)
                self.queue.clear()
                raise
            i = 0
            while self.queue:
                job = self.queue.popleft()
                try:
                    logger.info(
                        'Sending message {0} of {1}'.format(
                            str(i + 1), str(total)
                        )
                    )
                    smtp.sendmail(**job)
                except Exception as merr:
                    traceback.print_exc()
                    logger.error(
                        'Sendmail failed with error: {0}'.format(str(merr))
                    )
                    requeue.append(job)
                i += 1
            logger.info('Disconnecting from SMTP server')
            smtp.quit()
        except Exception as err:
            logger.error('SMTP failed with error {0}'.format(str(err)))
            if smtp:
                try:
                    smtp.quit()
                except Exception as err:
                    logger.warn('Failed to quit SMTP connection: {0}'.format(str(err)))
        if requeue:
            logger.info('Requeuing {0} failed messages'.format(len(requeue)))
            self.failqueue.extend(requeue)
            if len(requeue) == total:
                # All messages failed.
                self.last_was_success = False
