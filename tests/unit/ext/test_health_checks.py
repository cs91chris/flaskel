from unittest.mock import MagicMock, patch

import responses
from vbcore.datastruct import ObjectDict
from vbcore.http import httpcode
from vbcore.http.headers import ContentTypeEnum, HeaderEnum
from vbcore.system import (
    CpuFreq,
    CpuStat,
    CpuTimes,
    DiskStat,
    MemoryStat,
    NetStat,
    SwapStat,
)
from vbcore.tester.asserter import Asserter

from flaskel.ext.healthcheck import HealthCheck
from flaskel.ext.healthcheck.checkers import (
    check_cpu_stat,
    check_disks_stat,
    check_mem_stat,
    check_nets_stat,
    check_swap_stat,
    health_mongo,
    health_redis,
    health_services,
    health_sqlalchemy,
    health_system,
    SuccessResponse,
)
from flaskel.ext.healthcheck.health import CheckStatus


def test_health_sqlalchemy(flaskel_app):
    Asserter.assert_equals(
        health_sqlalchemy(db=MagicMock(), app=flaskel_app), SuccessResponse
    )


def test_health_mongo(flaskel_app):
    Asserter.assert_equals(
        health_mongo(db=MagicMock(), app=flaskel_app), SuccessResponse
    )


def test_health_redis(flaskel_app):
    Asserter.assert_equals(
        health_redis(db=MagicMock(), app=flaskel_app), SuccessResponse
    )


@patch("flaskel.ext.healthcheck.checkers.SysStats")
def test_check_mem_stat(mock_sys_stats):
    threshold = 10
    stat = MemoryStat(
        total=1,
        available=1,
        percent=threshold + 1,
        used=1,
        free=1,
        active=1,
        inactive=1,
        buffers=1,
        cached=1,
        shared=1,
        slab=1,
        swap=MagicMock(),
    )
    mock_sys_stats.memory_stats.return_value = stat
    expected = (
        stat,
        {
            "resource": "MEM",
            "usage": stat.percent,
            "threshold": threshold,
        },
    )
    Asserter.assert_equals(check_mem_stat(threshold), expected)


@patch("flaskel.ext.healthcheck.checkers.SysStats")
def test_check_swap_stat(mock_sys_stats):
    threshold = 10
    stat = MemoryStat(
        total=1,
        available=1,
        percent=threshold + 1,
        used=1,
        free=1,
        active=1,
        inactive=1,
        buffers=1,
        cached=1,
        shared=1,
        slab=1,
        swap=SwapStat(
            total=1,
            percent=threshold + 1,
            used=1,
            free=1,
        ),
    )

    mock_sys_stats.memory_stats.return_value = stat
    expected = (
        stat.swap,
        {
            "resource": "SWAP",
            "usage": stat.swap.percent,
            "threshold": threshold,
        },
    )
    Asserter.assert_equals(check_swap_stat(threshold), expected)


@patch("flaskel.ext.healthcheck.checkers.SysStats")
def test_check_cpu_stat(mock_sys_stats):
    threshold = 10
    stat = CpuStat(
        count=1,
        percent=threshold + 1,
        freq=MagicMock(),
        times=MagicMock(),
    )
    mock_sys_stats.cpu_stats.return_value = stat
    expected = (
        stat,
        {
            "resource": "CPU",
            "usage": stat.percent,
            "threshold": threshold,
        },
    )
    Asserter.assert_equals(check_cpu_stat(threshold), expected)


@patch("flaskel.ext.healthcheck.checkers.SysStats")
def test_check_disks_stat(mock_sys_stats):
    threshold = 10
    stats = {
        "/home": DiskStat(
            percent=threshold + 1,
            total=1,
            used=1,
            free=1,
        )
    }
    mock_sys_stats.disk_stats.return_value = stats
    expected = (
        stats,
        [
            {
                "resource": "DISK",
                "mount_point": "/home",
                "usage": threshold + 1,
                "threshold": threshold,
            }
        ],
    )
    Asserter.assert_equals(check_disks_stat(threshold, ("/home",)), expected)


@patch("flaskel.ext.healthcheck.checkers.SysStats")
def test_check_nets_stat(mock_sys_stats):
    threshold = 10
    stats = {
        "eth0": NetStat(
            bytes_sent=0,
            bytes_recv=0,
            packets_sent=0,
            packets_recv=0,
            errin=threshold + 1,
            errout=0,
        )
    }
    mock_sys_stats.net_stats.return_value = stats
    expected = (
        stats,
        [
            {
                "resource": "NIC",
                "nic": "eth0",
                "errors_out": 0,
                "errors_in": threshold + 1,
                "threshold": threshold,
            }
        ],
    )
    Asserter.assert_equals(check_nets_stat(threshold, ("eth0",)), expected)


@patch("flaskel.ext.healthcheck.checkers.check_mem_stat")
@patch("flaskel.ext.healthcheck.checkers.check_swap_stat")
@patch("flaskel.ext.healthcheck.checkers.check_cpu_stat")
@patch("flaskel.ext.healthcheck.checkers.check_disks_stat")
@patch("flaskel.ext.healthcheck.checkers.check_nets_stat")
def test_health_system(
    mock_check_nets_stat,
    mock_check_disks_stat,
    mock_check_cpu_stat,
    mock_check_swap_stat,
    mock_check_mem_stat,
):
    swap_stat = SwapStat(
        total=1,
        percent=1,
        used=1,
        free=1,
    )
    mem_stat = MemoryStat(
        total=1,
        available=1,
        percent=1,
        used=1,
        free=1,
        active=1,
        inactive=1,
        buffers=1,
        cached=1,
        shared=1,
        slab=1,
        swap=swap_stat,
    )
    cpu_stat = CpuStat(
        count=1,
        percent=11.0,
        freq=CpuFreq(
            current=1,
            min=1.0,
            max=1.0,
        ),
        times=CpuTimes(
            user=1.0,
            nice=1.0,
            system=1.0,
            idle=1.0,
            iowait=1.0,
            irq=1.0,
            softirq=1.0,
            steal=1.0,
            guest=1.0,
            guest_nice=1.0,
        ),
    )
    disks_stat = {
        "/home": DiskStat(
            percent=1,
            total=1,
            used=1,
            free=1,
        )
    }
    nets_stat = {
        "eth0": NetStat(
            bytes_sent=0,
            bytes_recv=0,
            packets_sent=0,
            packets_recv=0,
            errin=11,
            errout=0,
        )
    }

    mock_check_mem_stat.return_value = mem_stat, None
    mock_check_swap_stat.return_value = swap_stat, None
    mock_check_cpu_stat.return_value = cpu_stat, {
        "resource": "CPU",
        "usage": 11.0,
        "threshold": 10,
    }
    mock_check_disks_stat.return_value = disks_stat, None
    mock_check_nets_stat.return_value = nets_stat, [
        {
            "resource": "NIC",
            "nic": "eth0",
            "errors_out": 0,
            "errors_in": 11,
            "threshold": 10,
        }
    ]

    status, data = health_system(ObjectDict(SYSTEM_DUMP_ALL=True))
    Asserter.assert_false(status)
    Asserter.assert_equals(
        data,
        ObjectDict(
            mem=mem_stat,
            swap=swap_stat,
            cpu=cpu_stat,
            disks=disks_stat,
            nets=nets_stat,
            errors=[
                {
                    "resource": "CPU",
                    "usage": 11.0,
                    "threshold": 10,
                },
                {
                    "resource": "NIC",
                    "nic": "eth0",
                    "errors_out": 0,
                    "errors_in": 11,
                    "threshold": 10,
                },
            ],
        ),
    )


@responses.activate
def test_health_services(flaskel_app):
    responses.add(
        responses.GET,
        url="http://fake-endpoint-pass.com",
        json={},
        status=httpcode.SUCCESS,
    )
    responses.add(
        responses.GET,
        url="http://fake-endpoint-fail.com",
        json={"message": "error"},
        status=httpcode.INTERNAL_SERVER_ERROR,
    )
    flaskel_app.config.HEALTH_SERVICES = {
        "test-service-pass": {
            "url": "http://fake-endpoint-pass.com",
        },
        "test-service-fail": {
            "url": "http://fake-endpoint-fail.com",
        },
    }
    response = health_services(flaskel_app)
    Asserter.assert_equals(
        response,
        (
            False,
            {
                "test-service-pass": {
                    "status": httpcode.SUCCESS,
                    "message": {},
                },
                "test-service-fail": {
                    "status": httpcode.INTERNAL_SERVER_ERROR,
                    "message": {"message": "error"},
                    "exception": None,
                },
            },
        ),
    )


def test_health_checks_perform(flaskel_app):
    def check_pass(*_, **__):
        return True, None

    def check_fail(*_, **__):
        return False, {"message": "error"}

    handler = HealthCheck(
        flaskel_app,
        checkers=((check_pass, None), (check_fail, None)),
    )

    with flaskel_app.test_request_context():
        Asserter.assert_equals(
            handler.perform(),
            (
                {
                    "status": CheckStatus.FAIL,
                    "checks": {
                        "check_pass": {
                            "status": CheckStatus.PASS,
                            "output": None,
                        },
                        "check_fail": {
                            "status": CheckStatus.FAIL,
                            "output": {"message": "error"},
                        },
                    },
                    "links": {"about": None},
                },
                httpcode.MULTI_STATUS,
                {HeaderEnum.CONTENT_TYPE: ContentTypeEnum.JSON_HEALTH},
            ),
        )
