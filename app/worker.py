import threading
import queue
import time

import database
import typing

import logging
import sys

from docker_client import client

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

LOG = logging.getLogger(__name__)


class Worker:
    def __init__(self, num_of_workers=1, max_concurrent_tasks=2):
        self.queue = queue.Queue()
        self.num_of_workers = num_of_workers
        self.semaphore = threading.Semaphore(max_concurrent_tasks)

    def start_workers(self):
        LOG.debug("Starting %s workers.", self.num_of_workers)
        for i in range(self.num_of_workers):
            t = threading.Thread(target=self.worker)
            t.daemon = True
            t.start()

    def worker(self):
        while True:
            self.semaphore.acquire()
            item = self.queue.get()
            self._process_task(item)
            self.queue.task_done()
            self.semaphore.release()

    def wait(self):
        """Wait for all tasks to be processed."""
        self.queue.join()

    def _put_task(self, task: database.Task):
        self.queue.put(task)

    def _process_task(self, task: database.Task):
        # Get the command and image from the task attributes
        LOG.debug("Processing task %s.", task)
        task.status = database.Task.Status.running.value
        task.save()

        self._run_task(task)

    def _run_task(self, task):
        # Run task in Docker container
        LOG.debug("Running task %s.", task)
        container = client.containers.run(task.image, task.command, detach=True)
        container.wait()
        logs = container.logs().decode('utf-8')
        exit_code = container.wait()['StatusCode']
        container.remove()
        self._save_logs(task, logs, exit_code)

    def _save_logs(self, task, logs, exit_code):
        LOG.debug("Saving logs for task %s.", task)
        # Update task status and logs in database
        if exit_code == 0:
            task.status = database.Task.Status.finished.value
        else:
            task.status = database.Task.Status.failed.value
        task.logs = logs
        task.save()

    def _gather_tasks(self) -> typing.Sequence[database.Task]:
        """Gather all tasks in the database."""
        tasks = database.Task.select().where(database.Task.status == database.Task.Status.pending)
        return list(tasks)

    def start(self):
        database.init_database()
        self.start_workers()

        while True:
            tasks = self._gather_tasks()
            if tasks:
                for task in tasks:
                    self._put_task(task)
            else:
                LOG.debug("No tasks found, sleeping for 1 seconds.")
                time.sleep(1)

            self.wait()


w = Worker()
w.start()
