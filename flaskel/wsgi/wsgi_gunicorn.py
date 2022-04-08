import sys
import threading
import traceback
import typing as t
from multiprocessing import cpu_count

from gunicorn.app.base import BaseApplication as WSGIServer

from flaskel import Flaskel
from flaskel.config import config

from .base import BaseApplication


class WSGIGunicorn(BaseApplication, WSGIServer):
    default_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

    def __init__(self, app: Flaskel, options: t.Optional[dict] = None):
        BaseApplication.__init__(self, app, options)
        WSGIServer.__init__(self)

    def init(self, parser, opts, args):
        self.options = opts or {}

    def run(self):
        WSGIServer.run(self)

    def set_default_config(self):
        self.cfg.set("preload_app", True)
        self.cfg.set("post_fork", self.post_fork)
        self.cfg.set("pre_fork", self.pre_fork)
        self.cfg.set("pre_exec", self.pre_exec)
        self.cfg.set("when_ready", self.when_ready)
        self.cfg.set("worker_abort", self.worker_abort)
        self.cfg.set("worker_int", self.worker_int)

        host = config("APP_HOST", default="127.0.0.1")
        port = config("APP_PORT", default="5000", cast=int)
        self.cfg.set("bind", config("BIND", default=f"{host}:{port}"))
        self.cfg.set("pidfile", config("PID_FILE", default=".gunicorn.pid"))
        self.cfg.set("proc_name", config("PROC_NAME", default=None))
        self.cfg.set("timeout", config("TIMEOUT", default=30, cast=int))
        self.cfg.set("backlog", config("BACKLOG", default=2048, cast=int))
        self.cfg.set("keepalive", config("KEEPALIVE", default=3, cast=int))

        nw = 1 + 2 * cpu_count()
        worker_class = config("WORKER_CLASS", default="sync")
        self.cfg.set("worker_class", worker_class)

        self.cfg.set(
            "workers",
            config("WORKERS", default=nw if worker_class == "sync" else 1, cast=int),
        )
        self.cfg.set(
            "threads",
            config("THREADS", default=nw if worker_class == "gthread" else 1, cast=int),
        )

        self.cfg.set(
            "worker_connections", config("WORKER_CONNECTIONS", default=1000, cast=int)
        )

        self.cfg.set("errorlog", "-")
        self.cfg.set("accesslog", "-")
        self.cfg.set("loglevel", config("LOG_LEVEL", default="info").lower())
        self.cfg.set("access_log_format", self.default_log_format)

    def load_config(self):
        self.set_default_config()

        config_items = (
            (key, value)
            for key, value in self.options.items()
            if key in self.cfg.settings and value is not None
        )
        for key, value in config_items:
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application

    @staticmethod
    def post_fork(server, worker):
        server.log.info("Worker spawned (pid: %s)", worker.pid)

    @staticmethod
    def pre_fork(server, worker):
        server.log.info("pre fork (pid: %s)", worker.pid)

    @staticmethod
    def pre_exec(server):
        server.log.info("Forked child, re-executing.")

    @staticmethod
    def when_ready(server):
        server.log.info("Server is ready. Spawning workers")

    @staticmethod
    def worker_abort(worker):
        worker.log.info("worker received SIGABRT signal")

    @staticmethod
    def nworkers_changed(server, new_value, old_value):
        server.log.info(f"number of workers changed from {old_value} to {new_value}")

    @staticmethod
    def worker_int(worker):
        worker.log.info("worker received INT or QUIT signal")

        class DumpTraceback:
            def __str__(self):
                code = []
                id2name = {th.ident: th.name for th in threading.enumerate()}
                # noinspection PyUnresolvedReferences, PyProtectedMember
                for thread_id, stack in sys._current_frames().items():
                    thread_name = id2name.get(thread_id, "")
                    code.append(f"\n# Thread: {thread_name}({thread_id})")
                    for filename, lineno, name, line in traceback.extract_stack(stack):
                        code.append(f"File: '{filename}', line {lineno}, in {name}")
                        if line:
                            code.append(f"\t{line.strip()}")
                return "\n".join(code)

        worker.log.warning("%s", DumpTraceback())
