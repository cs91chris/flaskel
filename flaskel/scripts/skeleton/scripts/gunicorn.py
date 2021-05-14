import sys
import threading
import traceback
from multiprocessing import cpu_count

from decouple import config as AutoConfig

host = AutoConfig('APP_HOST', default='127.0.0.1')
port = AutoConfig('APP_PORT', default='5000', cast=int)
pidfile = AutoConfig('PID_FILE', default='.gunicorn.pid')
# This requires that you install the setproctitle module
proc_name = AutoConfig('PROC_NAME', default=None)
app_config = AutoConfig('APP_CONFIG_FILE', default='config.py')

timeout = 30
keepalive = 3
backlog = 2048

# generally in the 2-4 x $(NUM_CORES) range
workers = 1 + 2 * cpu_count()
worker_class = 'meinheld.gmeinheld.MeinheldWorker'

# For eventlet and gevent, limits the max number of simultaneous clients
# that a single process can handle
worker_connections = 1000
# A string of the form: 'HOST', 'HOST:PORT', 'unix:PATH'
bind = f'{host}:{port}'

# Install a trace function that spews every line of Python that is executed when running the server
spew = False

daemon = False
umask = 0
user = None
group = None

raw_env = [
    f'APP_CONFIG_FILE={app_config}',
]

errorlog = '-'
accesslog = '-'
loglevel = 'info'  # One of "debug", "info", "warning", "error", "critical"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'


def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)


def pre_fork(server, worker):
    server.log.info("pre fork (pid: %s)", worker.pid)


def after_fork(server, worker):
    server.log.info("after fork (pid: %s)", worker.pid)


def pre_exec(server):
    server.log.info("Forked child, re-executing.")


def when_ready(server):
    server.log.info("Server is ready. Spawning workers")


def worker_abort(worker):
    worker.log.info("worker received SIGABRT signal")


def worker_int(worker):
    worker.log.info("worker received INT or QUIT signal")

    class DumpTraceback:
        def __str__(self):
            code = []
            id2name = {th.ident: th.name for th in threading.enumerate()}
            # noinspection PyUnresolvedReferences, PyProtectedMember
            for threadId, stack in sys._current_frames().items():
                code.append("\n# Thread: %s(%d)" % (id2name.get(threadId, ""), threadId))
                for filename, lineno, name, line in traceback.extract_stack(stack):
                    code.append('File: "%s", line %d, in %s' % (filename, lineno, name))
                    if line:
                        code.append("  %s" % (line.strip()))
            return "\n".join(code)

    worker.log.debug("%s", DumpTraceback())
