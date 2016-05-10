import json

from ansible_asl import model
from ansible_asl import filters
from cliff.show import ShowOne


class ResultShow(ShowOne):
    def get_parser(self, name):
        p = super(ResultShow, self).get_parser(name)
        p.add_argument('--full', '-F',
                       action='store_true')
        p.add_argument('taskid',
                       type=int)
        p.add_argument('hostname')
        return p

    @model.db_session
    def take_action(self, argv):
        result = model.TaskResult.get(lambda r: r.task.id == argv.taskid
                                      and r.host.name == argv.hostname)

        if result is None:
            raise RuntimeError('Unable to find results for '
                               'task %d, host %s' % (
                                   argv.taskid, argv.hostname))

        labels = ['ID', 'Host', 'Start', 'End', 'Duration', 'Name',
                  'Action', 'Status']
        data = [result.task.id, result.host.name,
                filters.format_datetime(result.time_start),
                filters.format_datetime(result.time_end),
                filters.format_timedelta(result.duration),
                result.task.name,
                result.task.action,
                filters.format_status(result)]

        result_dict = json.loads(result.result)

        for key in ['cmd', 'stdout', 'stderr']:
            if key in result_dict and result_dict[key]:
                val = result_dict[key]
                labels.append(key.title())
                if isinstance(val, list):
                    data.append(' '.join(val))
                else:
                    data.append(val)

        if argv.full:
            labels.append('Result')
            data.append(json.dumps(result_dict, indent=2))

        return (labels, data)
