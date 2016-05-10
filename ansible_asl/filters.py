import json


def filter(name):
    def wrapper(func):
        func.__filter_name__ = name
        return func

    return wrapper


@filter('format_status')
def format_status(val):
    '''return a status string based on status attributes of a taskresult'''

    if val.failed and val.ignore_errors:
        status = 'ignored'
    elif val.failed:
        status = 'failed'
    elif val.changed:
        status = 'changed'
    elif val.skipped:
        status = 'skipped'
    else:
        status = 'ok'

    return status


@filter('from_json')
def filter_from_json(val):
    '''take json and return a python object'''
    return json.loads(val)


@filter('to_json')
def filter_to_json(val, **kwargs):
    '''serialize a python object to json'''
    return json.dumps(val, **kwargs)


@filter('to_yaml')
def filter_to_yaml(val, **kwargs):
    '''serialize a python object to yaml'''
    return yaml.safe_dump(val, **kwargs)


@filter('format_datetime')
def format_datetime(val, format='%Y/%m/%d %H:%M:%S'):
    '''format a datetime.datetime object'''
    return val.strftime(format)


@filter('format_timedelta')
def format_timedelta(val):
    '''format a datetime.timedelta object'''
    hours, remainder = divmod(val.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)

    return '%02d:%02d:%02.2f' % (hours, minutes, seconds)


def register_filters(env):
    '''register all filters with the given jinja2 environment'''

    for objname, obj in globals().items():
        if hasattr(obj, '__filter_name__'):
            env.filters[obj.__filter_name__] = obj
