"""This file sets up a command line manager.

Use "python manage.py" for a list of available commands.
Use "python manage.py runserver" to start the development web server on localhost:5000.
Use "python manage.py runserver --help" for a list of runserver options.
"""
import sys

from app import create_app
from flask_script import Manager
from app.commands import InitDbCommand,WatcherCommand

# Setup Flask-Script with command line commands
print(sys.argv)
if sys.argv[1] != 'runserver':
    manager = Manager(create_app(oidcEnable=False))
else:
    manager = Manager(create_app)

#manager.add_command('db', Migrate)
# manager.add_command('init_db', InitDbCommand)
manager.add_command('watcher', WatcherCommand)

if __name__ == "__main__":
    # python manage.py                      # shows available commands
    # python manage.py runserver --help     # shows available runserver options
    manager.run()