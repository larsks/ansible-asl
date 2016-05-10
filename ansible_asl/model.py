import os
import urlparse
import logging
from datetime import datetime
from pony.orm import *  # NOQA

LOG = logging.getLogger('sql_logger.model')
db = Database()


class Run(db.Entity):
    time_start = Required(datetime, default=datetime.now)
    playbooks = Set('Playbook')
    plays = Set('Play')


class Playbook(db.Entity):
    path = Required(str)
    plays = Set('Play')
    run = Required('Run')

    time_start = Optional(datetime, default=datetime.now)
    time_end = Optional(datetime)

    @property
    def duration(self):
        return (self.time_end - self.time_start)


class Play(db.Entity):
    name = Optional(str)
    uuid = Required(str)
    tasks = Set('Task')
    run = Required('Run')
    playbook = Required('Playbook')

    time_start = Optional(datetime, default=datetime.now)
    time_end = Optional(datetime)

    @property
    def duration(self):
        return (self.time_end - self.time_start)


class Path(db.Entity):
    path = Required(str)
    tasks = Set('Task')


class Task(db.Entity):
    uuid = Required(str)
    name = Required(str)
    action = Required(str)
    path = Optional('Path')
    lineno = Optional(int)

    play = Required('Play')
    taskresults = Set('TaskResult')

    time_start = Optional(datetime, default=datetime.now)
    time_end = Optional(datetime)

    @property
    def duration(self):
        return (self.time_end - self.time_start)


class TaskResult(db.Entity):
    task = Required('Task')

    host = Required('Host')
    changed = Required(bool)
    skipped = Required(bool)
    failed = Required(bool)
    status = Required(str)
    result = Required(str)
    ignore_errors = Optional(bool, default=False)

    time_start = Optional(datetime, default=datetime.now)
    time_end = Optional(datetime)

    @property
    def duration(self):
        return (self.time_end - self.time_start)


class Host(db.Entity):
    name = Required(str)
    taskresults = Set('TaskResult')


def split_netloc(netloc):
    if '@' in netloc:
        userspec, host = netloc.split('@', 1)
        if ':' in userspec:
            user, password = userspec.split(':', 1)
        else:
            user = userspec
            password = None
    else:
        host = netloc
        user = None
        password = None

    return (host, user, password)


def infer_type(s):
    if s.isdigit():
        return int(s)
    elif s.lower() in ['true', 'false']:
        return bool(s)

    return s


# <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
def resolve_dburi(uri):
    scheme, netloc, path, params, query, frag = urlparse.urlparse(uri)
    if netloc:
        host, user, password = split_netloc(netloc)

    kwargs = dict((k, infer_type(v))
                  for k, v in urlparse.parse_qsl(query))

    if scheme == 'sqlite':
        path = (':memory:' if not path
                else os.path.abspath(path[1:]))
        args = (scheme, path)
        kwargs.update({'create_db': True})
    elif scheme == 'postgres':
        kwargs.update({
            'user': user,
            'password': password,
            'host': host,
            'database': path[1:]})
        args = (scheme,)
    elif scheme == 'mysql':
        kwargs.update({
            'user': user,
            'passwd': password,
            'host': host,
            'db': path[1:]})
        args = (scheme,)
    elif scheme == 'oracle':
        args = (scheme, '%s/%s@%s' % (user, password, host))

    return (args, kwargs)


def initdb(uri):
    args, kwargs = resolve_dburi(uri)
    LOG.debug('got db args=%s, kwargs=%s', args, kwargs)
    db.bind(*args, **kwargs)
    db.generate_mapping(check_tables=True, create_tables=True)


if __name__ == '__main__':
    initdb('sqlite', 'testdb.db', create_db=True)
