# This file defines command line commands for manage.py
from flask import current_app
from flask_script import Command
import logging,time,os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from watchdog.observers.polling import PollingObserver

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)

class WatcherCommand(Command):
    def run(self):
        w = Watcher()
        w.run(dirToWatch=current_app.config['DIRECTORY_TO_WATCH'])

class Watcher:

    def __init__(self):

        self.observer = PollingObserver()

    def run(self,dirToWatch):

        event_handler = Handler()
        self.observer.schedule(event_handler, dirToWatch, recursive=True)
        logging.info('Start watcher in %s', dirToWatch)
        self.observer.start()
        try:
            while True:
                time.sleep(5)
        except:
            self.observer.stop()
            logging.error("Error watcher")
        self.observer.join()


class Handler(FileSystemEventHandler):
    @staticmethod
    def on_any_event(event):
        from app.tasks.publication_tasks import creation_publication_task
        if event.is_directory:
            return None
        elif event.event_type == 'created':
            # Take any action here when a file is first created.
            logging.info("Received created event - %s." % event.src_path)
            historicalSize = -1
            while (historicalSize != os.path.getsize(event.src_path)):
                historicalSize = os.path.getsize(event.src_path)
                time.sleep(1)
            logging.info("file copy has now finished")
            creation_publication_task.delay(event.src_path)
            logging.info("task send")

        elif event.event_type == 'modified':
            # Taken any action here when a file is modified.
            logging.info("Received modified event - %s." % event.src_path)
        else :
            # Take any action here when a file is first created.
            logging.info("Received %s event - %s.", event.event_type, event.src_path)

