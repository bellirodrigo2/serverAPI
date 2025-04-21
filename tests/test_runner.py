from serveAPI.container import ioc
from serveAPI.taskrunner import TaskRunner


def test_dispatch():
    taskrunner = ioc.resolve(TaskRunner)
