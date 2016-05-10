from ansible_asl import model
from ansible_asl import filters
from cliff.lister import Lister


class RunList(Lister):
    @model.db_session
    def take_action(self, argv):
        return (('ID', 'Start', 'End', 'Duration', 'Playbook'),
                [(run.id,
                  filters.format_datetime(run.time_start),
                  filters.format_datetime(run.time_end),
                  filters.format_timedelta(run.duration),
                  run.playbook.path)
                 for run in model.Run.select(lambda r: r.time_end is not None)])
