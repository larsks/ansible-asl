import json
import jinja2
import sys
import os
import datetime

def tasks():
    start = None
    for line in sys.stdin:
        task = json.loads(line)
        task['when'] = datetime.datetime.fromtimestamp(task['when'])

        if start is None:
            start = task['when']

        task['offset'] = task['when'] - start

        yield task

def filter_to_json(val, **kwargs):
    return json.dumps(val, **kwargs)

env = jinja2.Environment()
env.filters['basename'] = lambda x: os.path.basename(x)
env.filters['to_json'] = filter_to_json

with open('play.html') as fd:
    template = env.from_string(fd.read())

sys.stdout.write(template.render(tasks=tasks))
