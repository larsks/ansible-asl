import logging
import argparse
import json
import yaml
import jinja2
import sys
import os
import datetime

from ansible_asl import model
from ansible_asl import filters

LOG = logging.getLogger(__name__)


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
    env.filters['relpath'] = filter_relpath
    filters.register_filters(env)
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
