import os

from ansible_asl import model
from ansible_asl import filters
from cliff.lister import Lister


class TaskList(Lister):
    def get_parser(self, name):
        p = super(TaskList, self).get_parser(name)
        p.add_argument('playid',
                       type=int)
        return p

    @model.db_session
    def take_action(self, argv):
        play = model.Play[argv.playid]
        return (('ID', 'Start', 'End', 'Duration', 'Action', 'Name'),
                ((task.id,
                 filters.format_datetime(task.time_start),
                 filters.format_datetime(task.time_end),
                 filters.format_timedelta(task.duration),
                 task.action,
                 task.name) for task in play.tasks))
