import os

from ansible_asl import model
from ansible_asl import filters
from cliff.lister import Lister


class PlayList(Lister):
    def get_parser(self, name):
        p = super(PlayList, self).get_parser(name)

        p.add_argument('runid')
        return p

    @model.db_session
    def take_action(self, argv):
        if argv.runid == 'last':
            runid = list(model.Run.select(lambda r: r.time_end is not None))[-1].id
        else:
            runid = int(argv.runid)

        try:
            run = model.Run[runid]
        except model.ObjectNotFound:
            raise RuntimeError('Run %d does not exist' % runid)

        if run.time_end is None:
            raise RuntimeError('Run %d is incomplete' % runid)

        return (('ID', 'Start', 'End', 'Duration', 'Playbook', 'Tasks'),
                [(play.id,
                  filters.format_datetime(play.time_start),
                  filters.format_datetime(play.time_end),
                  filters.format_timedelta(play.duration),
                  play.playbook.path,
                  len(play.tasks))
                 for play in model.Play.select(lambda p: p.run == run)])
