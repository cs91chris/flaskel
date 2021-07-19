import psutil

from flaskel.http import HTTPClient, httpcode
from flaskel.http.batch import HTTPBatch
from flaskel.utils.datastruct import ObjectDict


def health_sqlalchemy(db, app, stm="SELECT 1"):
    """

    :param db:
    :param app:
    :param stm:
    :return:
    """
    try:
        with app.app_context():
            with db.engine.connect() as connection:
                connection.execute(stm)
    except Exception as exc:  # pragma: no cover pylint: disable=W0703
        return False, str(exc)
    return True, None


def health_mongo(db, app, cmd="ping"):
    """

    :param db:
    :param app:
    :param cmd:
    :return:
    """
    try:
        with app.app_context():
            db.db.command(cmd)
    except Exception as exc:  # pylint: disable=W0703
        return False, str(exc)
    return True, None  # pragma: no cover


def health_redis(db, app):
    """

    :param db:
    :param app:
    :return:
    """
    try:
        with app.app_context():
            db.ping()
    except Exception as exc:  # pylint: disable=W0703
        return False, str(exc)
    return True, None  # pragma: no cover


# noinspection PyUnusedLocal
def health_glances(conf=None, **__):
    """

    :param conf:
    :return:
    """
    conf = conf() if callable(conf) else (conf or {})
    default_conf = ObjectDict(
        SYSTEM_ENDPOINT="http://localhost:4000/api/2",
        SYSTEM_CPU_THRESHOLD=90,
        SYSTEM_MEM_THRESHOLD=90,
        SYSTEM_FS_THRESHOLD=85,
        SYSTEM_MEM_INCLUDE_SWAP=True,
        SYSTEM_FS_MOUNT_POINTS=("/",),
        SYSTEM_DUMP_ALL=False,
    )
    conf = ObjectDict(**{**default_conf, **conf})
    resp = ObjectDict(errors=[])
    units = ["cpu", "mem", "fs"]
    if conf.SYSTEM_MEM_INCLUDE_SWAP:
        units.append("memswap")

    th_mem = conf.SYSTEM_MEM_THRESHOLD
    th_cpu = conf.SYSTEM_CPU_THRESHOLD
    th_fs = conf.SYSTEM_FS_THRESHOLD

    responses = HTTPBatch().request(
        [dict(url=f"{conf.SYSTEM_ENDPOINT}/{u}") for u in units]
    )
    for i, r in enumerate(responses):
        if r.exception:
            return False, str(r.exception)
        resp[units[i]] = r.body

    if resp.cpu.total > th_cpu:
        resp.errors.append(f"high CPU usage: {resp.cpu.total}, threshold: {th_cpu}")

    if resp.mem.percent > th_mem:
        resp.errors.append(f"high RAM usage: {resp.mem.percent}, threshold: {th_mem}")
    if conf.SYSTEM_MEM_INCLUDE_SWAP:
        if resp.memswap.percent > th_mem:
            resp.errors.append(
                f"high SWAP usage: {resp.memswap.percent}, threshold: {th_mem}"
            )

    for f in resp.fs:
        if f.mnt_point in conf.SYSTEM_FS_MOUNT_POINTS and f.percent > th_fs:
            resp.errors.append(
                f"high DISK usage on {f.mnt_point}: {f.percent}, threshold: {th_fs}"
            )

    output = resp if conf.SYSTEM_DUMP_ALL else (resp.errors or None)
    return bool(not resp.errors), dict(messages=output)


# noinspection PyProtectedMember,PyUnusedLocal
def health_system(conf=None, **__):
    """

    :param conf:
    :return:
    """
    conf = conf() if callable(conf) else (conf or {})
    default_conf = dict(
        SYSTEM_FS_MOUNT_POINTS=("/",),
        SYSTEM_CPU_THRESHOLD=90,
        SYSTEM_MEM_THRESHOLD=90,
        SYSTEM_FS_THRESHOLD=85,
        SYSTEM_MEM_INCLUDE_SWAP=True,
        SYSTEM_DUMP_ALL=False,
    )
    conf = ObjectDict(**{**default_conf, **conf})
    resp = ObjectDict(errors=[])
    th_mem = conf.SYSTEM_MEM_THRESHOLD
    th_cpu = conf.SYSTEM_CPU_THRESHOLD
    th_fs = conf.SYSTEM_FS_THRESHOLD

    resp.mem = ObjectDict(**psutil.virtual_memory()._asdict())
    if resp.mem.percent > th_mem:
        resp.errors.append(f"high RAM usage: {resp.mem.percent}, threshold: {th_mem}")
    if conf.SYSTEM_MEM_INCLUDE_SWAP:
        resp.swap = ObjectDict(**psutil.swap_memory()._asdict())
        if resp.swap.percent > th_mem:
            resp.errors.append(
                f"high SWAP usage: {resp.swap.percent}, threshold: {th_mem}"
            )

    resp.cpu = psutil.cpu_percent()
    if resp.cpu > th_cpu:
        resp.errors.append(f"high CPU usage: {resp.cpu}, threshold: {th_cpu}")

    resp.disk = ObjectDict()
    for f in conf.SYSTEM_FS_MOUNT_POINTS:
        resp.disk[f] = ObjectDict(**psutil.disk_usage(f)._asdict())
        percent = resp.disk[f].percent
        if percent > th_mem:
            resp.errors.append(
                f"high DISK usage on '{f}': {percent}, threshold: {th_fs}"
            )

    output = resp if conf.SYSTEM_DUMP_ALL else (resp.errors or None)
    return bool(not resp.errors), dict(messages=output)


def health_services(app, *_, conf_key="SERVICES", **__):
    status = True
    response = {}
    services = app.config.get(conf_key) or {}

    for service, conf in services.items():
        conf.setdefault("uri", "/")
        conf.setdefault("method", "GET")
        client = HTTPClient(conf.pop("endpoint"), logger=app.logger)
        res = client.request(**conf)

        if not httpcode.is_success(res.status):
            status = False
            response[service] = dict(
                exception=str(res.exception or res.status), message=res.body
            )
        else:
            response[service] = dict(status=res.status, message=res.body)
    return status, response
