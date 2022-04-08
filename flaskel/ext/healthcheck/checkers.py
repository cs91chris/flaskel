import dataclasses
import typing as t

from vbcore.datastruct import ObjectDict
from vbcore.http import httpcode, HttpMethod
from vbcore.http.client import HTTPClient
from vbcore.system import CpuStat, DiskStat, MemoryStat, NetStat, SwapStat, SysStats

ConfigType = t.Optional[t.Union[t.Callable, dict]]
CheckerResponseType = t.Tuple[bool, t.Optional[t.Any]]
SuccessResponse = True, None


def health_sqlalchemy(db, app, stm: str = "SELECT 1") -> CheckerResponseType:
    try:
        with app.app_context():
            with db.engine.connect() as connection:
                connection.execute(stm)
    except Exception as exc:  # pylint: disable=broad-except
        app.logger.exception(exc)
        return False, str(exc)
    return SuccessResponse


def health_mongo(db, app, cmd: str = "ping") -> CheckerResponseType:
    try:
        with app.app_context():
            db.db.command(cmd)
    except Exception as exc:  # pylint: disable=broad-except
        app.logger.exception(exc)
        return False, str(exc)
    return SuccessResponse


def health_redis(db, app) -> CheckerResponseType:
    try:
        with app.app_context():
            db.ping()
    except Exception as exc:  # pylint: disable=broad-except
        app.logger.exception(exc)
        return False, str(exc)
    return SuccessResponse


def prepare_config(conf: ConfigType = None) -> ObjectDict:
    if not conf:
        return ObjectDict()
    return ObjectDict(**conf) if isinstance(conf, dict) else conf()


def check_mem_stat(
    threshold: float,
) -> t.Tuple[MemoryStat, t.Optional[t.Dict[str, t.Any]]]:
    stat = SysStats.memory_stats()
    if stat.percent > threshold:
        return stat, {
            "resource": "MEM",
            "usage": stat.percent,
            "threshold": threshold,
        }
    return stat, None


def check_swap_stat(
    threshold: float,
) -> t.Tuple[SwapStat, t.Optional[t.Dict[str, t.Any]]]:
    stat = SysStats.memory_stats().swap
    if stat.percent > threshold:
        return stat, {
            "resource": "SWAP",
            "usage": stat.percent,
            "threshold": threshold,
        }
    return stat, None


def check_cpu_stat(
    threshold: float,
) -> t.Tuple[CpuStat, t.Optional[t.Dict[str, t.Any]]]:
    stat = SysStats.cpu_stats()
    if stat.percent > threshold:
        return stat, {
            "resource": "CPU",
            "usage": stat.percent,
            "threshold": threshold,
        }
    return stat, None


def check_disks_stat(
    threshold: float,
    mount_points: t.Optional[t.Tuple[str, ...]] = None,
) -> t.Tuple[t.Dict[str, DiskStat], t.List[t.Dict[str, t.Any]]]:
    stats: t.Dict[str, DiskStat] = {}
    errors: t.List[t.Dict[str, t.Any]] = []

    for mount_point, stat in SysStats.disk_stats().items():
        if mount_points and mount_point not in mount_points:
            continue
        stats[mount_point] = stat
        if stat.percent > threshold:
            errors.append(
                {
                    "resource": "DISK",
                    "mount_point": mount_point,
                    "usage": stat.percent,
                    "threshold": threshold,
                }
            )
    return stats, errors


def check_nets_stat(
    threshold: float,
    nics: t.Optional[t.Tuple[str, ...]] = None,
) -> t.Tuple[t.Dict[str, NetStat], t.List[t.Dict[str, t.Any]]]:
    stats: t.Dict[str, NetStat] = {}
    errors: t.List[t.Dict[str, t.Any]] = []

    for nic, stat in SysStats.net_stats().items():
        if nics and nic not in nics:
            continue
        stats[nic] = stat
        if stat.errin > threshold or stat.errout > threshold:
            errors.append(
                {
                    "resource": "NIC",
                    "nic": nic,
                    "errors_in": stat.errin,
                    "errors_out": stat.errout,
                    "threshold": threshold,
                }
            )
    return stats, errors


def health_system(config: ConfigType = None, **__) -> CheckerResponseType:
    conf = ObjectDict(
        SYSTEM_NICS=(),
        SYSTEM_NET_ERROR_THRESHOLD=1000,
        SYSTEM_CPU_THRESHOLD=90,
        SYSTEM_MEM_THRESHOLD=90,
        SYSTEM_FS_THRESHOLD=85,
        SYSTEM_FS_MOUNT_POINTS=(),
        SYSTEM_DUMP_ALL=False,
    )
    conf.update(prepare_config(config))
    resp = ObjectDict(errors=[])

    mem_stat, mem_error = check_mem_stat(conf.SYSTEM_MEM_THRESHOLD)
    if mem_error:
        resp.errors.append(mem_error)

    swap_stat, swap_error = check_swap_stat(conf.SYSTEM_MEM_THRESHOLD)
    if swap_error:
        resp.errors.append(swap_error)

    cpu_stat, cpu_error = check_cpu_stat(conf.SYSTEM_CPU_THRESHOLD)
    if cpu_error:
        resp.errors.append(cpu_error)

    disks_stat, disks_error = check_disks_stat(
        conf.SYSTEM_FS_THRESHOLD, conf.SYSTEM_FS_MOUNT_POINTS
    )
    resp.errors.extend(disks_error or [])

    nets_stat, nets_error = check_nets_stat(
        conf.SYSTEM_NET_ERROR_THRESHOLD, conf.SYSTEM_NICS
    )
    resp.errors.extend(nets_error or [])

    resp.mem = mem_stat
    resp.swap = swap_stat
    resp.cpu = cpu_stat
    resp.disks = disks_stat
    resp.nets = nets_stat

    output = resp if conf.SYSTEM_DUMP_ALL else (resp.errors or None)
    return bool(not resp.errors), output


@dataclasses.dataclass(frozen=True)
class ServiceRequest:
    url: str
    method: str = HttpMethod.GET
    user: t.Optional[str] = None
    password: t.Optional[str] = None
    token: t.Optional[str] = None
    headers: t.Optional[dict] = None
    params: t.Optional[dict] = None
    json: t.Optional[dict] = None


def health_services(
    app, *_, conf_key: str = "HEALTH_SERVICES", **__
) -> CheckerResponseType:
    status = True
    services = app.config[conf_key]
    response: t.Dict[str, t.Dict[str, t.Any]] = {}

    for service, conf in services.items():
        request = ServiceRequest(**conf)
        client = HTTPClient(
            None,
            token=request.token,
            username=request.user,
            password=request.password,
            logger=app.logger,
        )
        res = client.request(
            uri=request.url,
            method=request.method,
            json=request.json,
            headers=request.headers,
            params=request.params,
        )

        response[service] = {"status": res.status, "message": res.body}
        if res.status != httpcode.SUCCESS:
            status = False
            response[service]["exception"] = (
                str(res.exception) if res.exception else None
            )

    return status, response
