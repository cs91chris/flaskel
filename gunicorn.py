import os
import yaml
import multiprocessing

import flaskel.config as conf


ENV = os.environ


raw_env = [
]

bind = '{}:{}'.format(
    ENV.get('APP_HOST') or '127.0.0.1',
    ENV.get('APP_PORT') or '5000'
)

spew = False
timeout = ENV.get('TIMEOUT') or 30
keepalive = ENV.get('KEEPALIVE') or 2
backlog = ENV.get('BACKLOG') or 2048
daemon = ENV.get('DAEMON') or True

worker_connections = ENV.get('WORKER_CONNECTIONS') or 1000
workers = ENV.get('WORKERS') or (multiprocessing.cpu_count() * 2 + 1)
worker_class = 'meinheld.gmeinheld.MeinheldWorker'

umask = 0
proc_name = conf.APP_NAME
user = ENV.get('USER')
group = ENV.get('GROUP')
pidfile = os.path.join('.pid', 'app.pid')
tmp_upload_dir = "/tmp/{}_tmp_upload".format(conf.APP_NAME)


with open(conf.LOG_FILE_CONF) as f:
    logconfig_dict = yaml.load(f.read())


def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)


def pre_fork(server, worker):
    pass


def pre_exec(server):
    server.log.info("Forked child, re-executing.")


def when_ready(server):
    server.log.info("Server is ready. Spawning workers")


def worker_int(worker):
    worker.log.info("worker received INT or QUIT signal")

    import threading, sys, traceback
    id2name = {th.ident: th.name for th in threading.enumerate()}
    code = []

    for threadId, stack in sys._current_frames().items():
        code.append("\n# Thread: %s(%d)" % (id2name.get(threadId, ""), threadId))
        for filename, lineno, name, line in traceback.extract_stack(stack):
            code.append('File: "%s", line %d, in %s' % (filename, lineno, name))
            if line:
                code.append("  %s" % (line.strip()))
    worker.log.debug("\n".join(code))


def worker_abort(worker):
    worker.log.info("worker received SIGABRT signal")

