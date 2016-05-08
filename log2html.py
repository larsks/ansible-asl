import json
import yaml
import jinja2
import sys
import os
import datetime

def tasks():
    start = None
    for line in sys.stdin:
        task = json.loads(line)
        time_task_start = datetime.datetime.strptime(task['time_task_start'],
                                                     '%Y-%m-%d %H:%M:%S.%f')

        if start is None:
            start = time_task_start

        task['offset'] = time_task_start - start

        yield task

def filter_to_json(val, **kwargs):
    return json.dumps(val, **kwargs)

def filter_to_yaml(val, **kwargs):
    return yaml.safe_dump(val, **kwargs)

env = jinja2.Environment()
env.filters['basename'] = lambda x: os.path.basename(x)
env.filters['to_json'] = filter_to_json
env.filters['to_yaml'] = filter_to_yaml

with open('play.html') as fd:
    template = env.from_string(fd.read())

sys.stdout.write(template.render(tasks=tasks))
