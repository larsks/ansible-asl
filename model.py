import urlparse
import logging
from datetime import datetime
from pony.orm import *  # NOQA

LOG = logging.getLogger('sql_logger.model')
db = Database()


class Run(db.Entity):
    time_start = Required(datetime, default=datetime.now)
    playbooks = Set('Playbook')


class Playbook(db.Entity):
    path = Required(str)
    time_start = Optional(datetime)
    time_end = Optional(datetime)

    plays = Set('Play')
    run = Required('Run')


class Play(db.Entity):
    name = Optional(str)
    tasks = Set('Task')
    playbook = Required('Playbook')


class Path(db.Entity):
    path = Required(str)
    tasks = Set('Task')


class Task(db.Entity):
    uuid = Required(str)
    name = Required(str)
    action = Required(str)
    path = Optional('Path')
    lineno = Optional(int)
    time_start = Required(datetime, default=datetime.now)

    play = Required('Play')
    taskresults = Set('TaskResult')


class TaskResult(db.Entity):
    task = Required('Task')

    host = Required('Host')
    changed = Required(bool)
    skipped = Required(bool)
    failed = Required(bool)
    status = Required(str)
    result = Required(str)
    ignore_errors = Required(bool)

    time_start = Optional(datetime)
    time_end = Optional(datetime)

    def duration(self):
        return (self.time_end - self.time_start).total_seconds()


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


# <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
def resolve_dburi(uri):
    scheme, netloc, path, params, query, frag = urlparse.urlparse(uri)
    if netloc:
        host, user, password = split_netloc(netloc)

    kwargs = dict(urlparse.parse_qsl(query))

    if scheme == 'sqlite':
        path = ':memory:' if not path else path[1:]
        args = (scheme, path)
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
    sql_debug(True)
    args, kwargs = resolve_dburi(uri)
    LOG.debug('got db args=%s, kwargs=%s', args, kwargs)
    db.bind(*args, **kwargs)
    db.generate_mapping(check_tables=True, create_tables=True)


if __name__ == '__main__':
    initdb('sqlite', 'testdb.db', create_db=True)
