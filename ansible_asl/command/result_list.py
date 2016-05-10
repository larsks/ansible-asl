import os

from ansible_asl import model
from ansible_asl import filters
from cliff.lister import Lister


class ResultList(Lister):
    def get_parser(self, name):
        p = super(ResultList, self).get_parser(name)
        p.add_argument('taskid',
                       type=int)
        return p

    @model.db_session
    def take_action(self, argv):
        try:
            task = model.Task[argv.taskid]
        except model.ObjectNotFound:
            raise RuntimeError('Task %d does not exist' % argv.taskid)

        return (('ID', 'Host', 'Start', 'End', 'Duration', 'Status'),
                [(task.id, result.host.name,
                  filters.format_datetime(result.time_start),
                  filters.format_datetime(result.time_end),
                  filters.format_timedelta(result.duration),
                  filters.format_status(result))
                 for result in model.TaskResult.select(lambda t: t.task == task)])
