from ipaddress import IPv4Address
from unittest.mock import MagicMock

from vbcore.http import httpcode
from vbcore.tester.mixins import Asserter

from flaskel.ext.ipban import BanRepoLocal, BanRepoRedis, ipban, IpBanService


def test_ipban_init(flaskel_app):
    ipban.init_app(flaskel_app)

    Asserter.assert_true(flaskel_app.config.IPBAN_ENABLED)
    Asserter.assert_equals(flaskel_app.config.IPBAN_STATUS_CODE, httpcode.FORBIDDEN)
    Asserter.assert_equals(flaskel_app.config.IPBAN_ENABLED, True)
    Asserter.assert_equals(
        flaskel_app.config.IPBAN_KEY_PREFIX, flaskel_app.config.APP_NAME
    )
    Asserter.assert_equals(flaskel_app.config.IPBAN_KEY_SEP, "/")
    Asserter.assert_equals(flaskel_app.config.IPBAN_BACKEND, "local")
    Asserter.assert_equals(flaskel_app.config.IPBAN_BACKEND_OPTS, {})
    Asserter.assert_equals(flaskel_app.config.IPBAN_COUNT, 20)
    Asserter.assert_equals(flaskel_app.config.IPBAN_SECONDS, 86400)
    Asserter.assert_equals(flaskel_app.config.IPBAN_STATUS_CODE, httpcode.FORBIDDEN)


def test_ban_service():
    service = IpBanService(
        BanRepoLocal,
        key_prefix="TEST",
        max_attempts=2,
        default_ttl=10,
    )

    ip_banned = "192.168.1.1"
    not_banned = "79.1.1.1"
    ip_whitelisted = "127.0.0.1"
    ip_blacklisted = "10.100.0.1"

    service.load_whitelist(ip=(ip_whitelisted,))
    service.add_blacklist(ip_blacklisted)

    Asserter.assert_true(service.is_blacklisted(ip_blacklisted))
    Asserter.assert_equals(service.white_list, {IPv4Address(ip_whitelisted)})

    service.ban(ip_banned)
    Asserter.assert_false(service.is_banned(ip_banned))

    Asserter.assert_none(service.ban(ip_whitelisted))
    Asserter.assert_none(service.ban(ip_blacklisted))
    Asserter.assert_true(service.is_banned(ip_blacklisted))
    Asserter.assert_false(service.is_banned(ip_whitelisted))

    service.ban(ip_banned)
    Asserter.assert_true(service.is_banned(ip_banned))
    Asserter.assert_false(service.is_banned(not_banned))

    service.repo.unban(ip_banned)
    Asserter.assert_false(service.is_banned(ip_banned))


def test_repo_redis():
    ip = "localhost"
    cache_key = f"TEST/{ip}"
    client_redis = MagicMock()
    client_redis.get.return_value = "1"
    repo = BanRepoRedis(client_redis, key_prefix="TEST")

    Asserter.assert_equals(repo.attempts(ip), 1)
    client_redis.get.assert_called_once_with(cache_key)

    repo.unban(ip)
    client_redis.delete.assert_called_once_with(cache_key)

    mock_pipeline = MagicMock()
    mock_pipeline.execute.return_value = [3, 1]
    client_redis.pipeline.side_effect = lambda: mock_pipeline

    Asserter.assert_equals(repo.ban(ip, ttl=100), 3)
    mock_pipeline.incr.assert_called_once_with(cache_key)
    mock_pipeline.expire.assert_called_once_with(cache_key, 100)
