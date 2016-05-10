import sys
import os

from ansible_asl import __version__
from ansible_asl import model

from cliff.app import App
from cliff.commandmanager import CommandManager

default_db_uri = os.environ.get('ASL_DB_URI',
                                'sqlite:///ansible_log.db')


class ASLApp(App):
    def __init__(self):
        super(ASLApp, self).__init__(
            description='ansible sql logger and reporter',
            version=__version__,
            command_manager=CommandManager('ansible_asl.command'),
            deferred_help=True,
        )

    def build_option_parser(self, description, version, argparse_kwargs=None):
        p = super(ASLApp, self).build_option_parser(
            description, version, argparse_kwargs)

        p.add_argument('--database-uri', '-d',
                       default=default_db_uri)

        return p

    def initialize_app(self, argv):
        model.initdb(self.options.database_uri)


def main():
    app = ASLApp()
    return app.run(sys.argv[1:])

if __name__ == '__main__':
    sys.exit(main())
