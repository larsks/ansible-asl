from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from datetime import datetime
import logging
import os
import json

from ansible.plugins.callback import CallbackBase
from ansible.constants import load_config_file

from ansible_asl import model

DEFAULT_DBURI = 'sqlite://:memory:?create_db=True'


LOG = logging.getLogger('sql_logger')
LOG.setLevel('DEBUG')
fh = logging.FileHandler('callback.log')
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
LOG.addHandler(fh)


def parse_time(timestr):
    return datetime.strptime(timestr, '%Y-%m-%d %H:%M:%S.%f')


class CallbackModule(CallbackBase):

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'
    CALLBACK_NAME = 'sql_logger'

    def __init__(self):
        super(CallbackModule, self).__init__()

        dburi = None
        cfg, cfgpath = load_config_file()

        if (cfg
                and cfg.has_section('sql_logger')
                and cfg.has_option('sql_logger', 'database')):
            dburi = cfg.get('sql_logger', 'database')

        if dburi is None:
            dburi = DEFAULT_DBURI

        self.dburi = dburi

        LOG.debug('using dburi %s', dburi)
        model.initdb(dburi)

        # need to reset these on task completion
        self._playbook = None
        self._play = None
        self._task = None

        self.start_run()

    @model.db_session
    def start_run(self):
        LOG.debug('START_RUN')
        self.run = model.Run()

    def _get_or_create_host(self, hostname):
        host = model.Host.get(name=hostname)
        if host is None:
            host = model.Host(name=hostname)

        return host

    def _get_or_create_path(self, path):
        pathobj = model.Path.get(path=path)
        if pathobj is None:
            pathobj = model.Path(path=path)

        return pathobj

    @model.db_session
    def log_task_result(self, status, result, ignore_errors=False):
        LOG.debug('TASK_COMPLETE %s %s', result._task.action, status)

        host = self._get_or_create_host(result._host.get_name())
        task = model.Task[self._task.id]

        time_start = task.time_start
        time_end = datetime.now()

        if ignore_errors is None:
            LOG.warn('ignore_errors was None')
            ignore_errors = False

        result = model.TaskResult(
            host=host,
            task=task,
            time_start=time_start,
            time_end=time_end,
            status=status,
            changed=result._result.get('changed', False),
            skipped=result._result.get('skipped', False),
            failed=result._result.get('failed', False),
            ignore_errors=ignore_errors,
            result=json.dumps(result._result)
        )

    def close_task(self):
        if not self._task:
            return

        task = model.Task[self._task.id]
        task.time_end = datetime.now()
        self._task = None

    def close_play(self):
        if not self._play:
            return

        play = model.Play[self._play.id]
        play.time_end = datetime.now()
        self._play = None

    @model.db_session
    def v2_playbook_on_start(self, playbook):
        LOG.debug('PLAYBOOK_ON_START %s', playbook._file_name)
        self._playbook = model.Playbook(path=playbook._file_name,
                                        run=self.run.id)

    @model.db_session
    def v2_playbook_on_play_start(self, play):
        LOG.debug('PLAY_START %s', play.get_name())
        self.close_play()

        self._play = model.Play(name=play.name,
                                uuid=str(play._uuid),
                                playbook=self._playbook.id,
                                run=self.run.id)

    @model.db_session
    def v2_playbook_on_task_start(self, task, is_conditional=False):
        LOG.debug('TASK_START %s', task.get_name())
        self.close_task()

        if self._play is None:
            LOG.error('play is none!')

        play = model.Play[self._play.id]

        pathspec = task.get_path()
        if pathspec:
            path, lineno = pathspec.split(':', 1)
            LOG.debug('PATH %s', path)
            path = self._get_or_create_path(path)
        else:
            LOG.warn('pathspec is none!')
            path = None
            lineno = 0

        self._task = model.Task(name=task.get_name(),
                                uuid=str(task._uuid),
                                action=task.action,
                                path=path,
                                lineno=lineno,
                                play=play)

    def v2_runner_on_failed(self, result, ignore_errors=False):
        return self.log_task_result('failed', result,
                                    ignore_errors=ignore_errors)

    def v2_runner_on_ok(self, result):
        return self.log_task_result('ok', result)

    def v2_runner_on_skipped(self, result):
        return self.log_task_result('skipped', result)

    def v2_runner_on_unreachable(self, result):
        return self.log_task_result('unreachable', result)

    def v2_playbook_on_include(self, included_file):
        LOG.debug('INCLUDE %s', included_file)

    @model.db_session
    def v2_playbook_on_stats(self, stats):
        self.close_task()
        self.close_play()
        playbook = model.Playbook[self._playbook.id]
        playbook.time_end = datetime.now()


if __name__ == '__main__':
    import mock

    logging.basicConfig(level='DEBUG')

    cb = CallbackModule()
    cb.v2_playbook_on_start(mock.Mock(_file_name='sample.yml'))
