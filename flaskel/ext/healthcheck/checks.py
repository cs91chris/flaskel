import psutil

from flaskel.http.batch import HTTPBatch
from flaskel.utils.datastruct import ObjectDict


def health_sqlalchemy(db):
    """

    :param db:
    :return:
    """
    try:
        with db.engine.connect() as connection:
            connection.execute('SELECT 1')
    except Exception as exc:
        return False, str(exc)
    return True, None  # pragma: no cover


def health_mongo(db):
    """

    :param db:
    :return:
    """
    try:
        db.db.command('ping')
    except Exception as exc:
        return False, str(exc)
    return True, None  # pragma: no cover


def health_redis(db):
    """

    :param db:
    :return:
    """
    try:
        db.ping()
    except Exception as exc:
        return False, str(exc)
    return True, None  # pragma: no cover


def health_glances(conf=None):
    """

    :param conf:
    :return:
    """
    conf = conf() if callable(conf) else (conf or {})
    default_conf = ObjectDict(
        SYSTEM_ENDPOINT='http://localhost:4000/api/2',
        SYSTEM_CPU_THRESHOLD=90,
        SYSTEM_MEM_THRESHOLD=90,
        SYSTEM_FS_THRESHOLD=85,
        SYSTEM_MEM_INCLUDE_SWAP=True,
        SYSTEM_FS_MOUNT_POINTS=('/',),
        SYSTEM_DUMP_ALL=False
    )
    conf = ObjectDict(**{**default_conf, **conf})
    resp = ObjectDict(errors=[])
    units = ['cpu', 'mem', 'fs']
    if conf.SYSTEM_MEM_INCLUDE_SWAP:
        units.append('memswap')

    th_mem = conf.SYSTEM_MEM_THRESHOLD
    th_cpu = conf.SYSTEM_CPU_THRESHOLD
    th_fs = conf.SYSTEM_FS_THRESHOLD

    responses = HTTPBatch().request([dict(url=f"{conf.SYSTEM_ENDPOINT}/{u}") for u in units])
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
            resp.errors.append(f"high SWAP usage: {resp.memswap.percent}, threshold: {th_mem}")

    for f in resp.fs:
        if f.mnt_point in conf.SYSTEM_FS_MOUNT_POINTS and f.percent > th_fs:
            resp.errors.append(f"high DISK usage on {f.mnt_point}: {f.percent}, threshold: {th_fs}")

    return bool(not resp.errors), resp if conf.SYSTEM_DUMP_ALL else (resp.errors or None)


# noinspection PyProtectedMember
def health_system(conf=None):
    """

    :param conf:
    :return:
    """
    conf = conf() if callable(conf) else (conf or {})
    default_conf = dict(
        SYSTEM_FS_MOUNT_POINTS=('/',),
        SYSTEM_CPU_THRESHOLD=90,
        SYSTEM_MEM_THRESHOLD=90,
        SYSTEM_FS_THRESHOLD=85,
        SYSTEM_MEM_INCLUDE_SWAP=True,
        SYSTEM_DUMP_ALL=False
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
            resp.errors.append(f"high SWAP usage: {resp.swap.percent}, threshold: {th_mem}")

    resp.cpu = psutil.cpu_percent()
    if resp.cpu > th_cpu:
        resp.errors.append(f"high CPU usage: {resp.cpu}, threshold: {th_cpu}")

    resp.disk = ObjectDict()
    for f in conf.SYSTEM_FS_MOUNT_POINTS:
        resp.disk[f] = ObjectDict(**psutil.disk_usage(f)._asdict())
        percent = resp.disk[f].percent
        if percent > th_mem:
            resp.errors.append(f"high DISK usage on '{f}': {percent}, threshold: {th_fs}")

    return bool(not resp.errors), resp if conf.SYSTEM_DUMP_ALL else (resp.errors or None)



if __name__ == '__main__':
    print(*health_system())
