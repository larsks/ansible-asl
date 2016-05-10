import logging
import argparse
import json
import yaml
import jinja2
import sys
import os
import datetime

from ansible_asl import model

LOG = logging.getLogger(__name__)


def filter_status(val):
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


def filter_from_json(val):
    return json.loads(val)


def filter_to_json(val, **kwargs):
    return json.dumps(val, **kwargs)


def filter_to_yaml(val, **kwargs):
    return yaml.safe_dump(val, **kwargs)


def filter_timedelta(val):
    hours, remainder = divmod(val.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)

    return '%02d:%02d:%02.2f' % (hours, minutes, seconds)


def filter_relpath(val):
    global args
    if args.strip_path and val.startswith(args.strip_path):
        val = val[len(args.strip_path):]
        if val.startswith('/'):
            val = val[1:]

    return val


def parse_args():
    p = argparse.ArgumentParser()

    p.add_argument('--template-dir', '-T',
                   default='templates')
    p.add_argument('--run', '-r',
                   type=int)
    p.add_argument('--strip-path')
    p.add_argument('--strip-cwd', '-C',
                   action='store_const',
                   const=os.getcwd(),
                   dest='strip_path')
    p.add_argument('dburi')

    return p.parse_args()


def main():
    global args
    args = parse_args()
    logging.basicConfig(level='DEBUG')

    model.initdb(args.dburi)

    env = jinja2.Environment(loader=jinja2.FileSystemLoader(args.template_dir))
    env.filters['basename'] = lambda x: os.path.basename(x)
    env.filters['to_json'] = filter_to_json
    env.filters['to_yaml'] = filter_to_yaml
    env.filters['from_json'] = filter_from_json
    env.filters['timedelta'] = filter_timedelta
    env.filters['relpath'] = filter_relpath
    env.filters['status'] = filter_status
    template = env.get_template('ansible_run.html')

    with model.db_session:
        if args.run:
            run = model.Run[args.run]
        else:
            run = list(model.Run.select().order_by(model.Run.time_start))[-1]

        LOG.info('using run %d', run.id)

        tasks = (model.select(t for t in model.Task
                              for p in model.Play
                              if p.run == run and t.play == p))
        sys.stdout.write(template.render(run=run, model=model, tasks=tasks))

if __name__ == '__main__':
    main()
