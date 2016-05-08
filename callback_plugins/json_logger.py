from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import sys
import pprint
import json
import time

from ansible.plugins.callback import CallbackBase
from ansible import constants as C


class CallbackModule(CallbackBase):

    '''
    This is the default callback interface, which simply prints messages
    to stdout when new callback events are received.
    '''

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'
    CALLBACK_NAME = 'minimal'

    def __init__(self):
        super(CallbackModule, self).__init__()

        self.logfile = 'ansible_log.json'
        with open(self.logfile, 'w'):
            pass

    def log_task_result(self, status, result, ignored=False):
        now = time.time()

        if self._task.get_path() is None:
            playbook_path, lineno = "", 0
        else:
            playbook_path, lineno = self._task.get_path().split(':', 1)


        with open(self.logfile, 'a') as fd:
            json.dump({
                'when': now,
                'playbook': playbook_path,
                'lineno': lineno,
                'play': self._play.get_name(),
                'host': result._host.get_name(),
                'task': result._task.get_name(),
                'module': result._task.action,
                'status': status,
                'result': result._result,
                'ignore_errors': ignored}, fd)
            fd.write('\n')

    def v2_playbook_on_start(self, playbook):
        self._playbook = playbook

    def v2_playbook_on_task_start(self, task, is_conditional):
        self._task = task

    def v2_playbook_on_play_start(self, play):
        self._play = play

    def v2_runner_on_failed(self, result, ignore_errors=False):
        self.log_task_result('failed', result, ignored=True)

    def v2_runner_on_ok(self, result):
        self.log_task_result('ok', result)

    def v2_runner_on_skipped(self, result):
        self.log_task_result('skipped', result)

    def v2_runner_on_unreachable(self, result):
        self.log_task_result('unreachable', result)
