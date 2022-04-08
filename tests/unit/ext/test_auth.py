from unittest.mock import MagicMock, patch

from vbcore.datastruct import ObjectDict
from vbcore.tester.mixins import Asserter

from flaskel.ext.auth import BaseTokenHandler, DBTokenHandler, RedisTokenHandler


@patch("flaskel.ext.auth.create_access_token")
@patch("flaskel.ext.auth.create_refresh_token")
@patch("flaskel.ext.auth.decode_token")
def test_token_create(
    mock_decode_token,
    mock_create_refresh_token,
    mock_create_access_token,
    flaskel_app,
):
    mock_create_access_token.return_value = "fake-access-token"
    mock_create_refresh_token.return_value = "fake-refresh-token"
    mock_decode_token.return_value = ObjectDict(exp=11111, iat=22222)

    flaskel_app.config.JWT_DEFAULT_TOKEN_TYPE = "bearer"
    flaskel_app.config.JWT_DEFAULT_SCOPE = "test-scope"

    with flaskel_app.app_context():
        token_data = BaseTokenHandler().create(
            identity=ObjectDict(id=1, role="ADMIN"),
            refresh=True,
        )

    Asserter.assert_equals(
        token_data.to_dict(),
        ObjectDict(
            expires_in=11111,
            issued_at=22222,
            token_type="bearer",
            scope="test-scope",
            access_token="fake-access-token",
            refresh_token="fake-refresh-token",
        ),
    )


@patch("flaskel.ext.auth.create_access_token")
@patch("flaskel.ext.auth.decode_token")
@patch("flaskel.ext.auth.get_jwt_identity")
def test_token_refresh(
    mock_get_jwt_identity,
    mock_decode_token,
    mock_create_access_token,
    flaskel_app,
):
    mock_create_access_token.return_value = "fake-access-token"
    mock_get_jwt_identity.return_value = dict(id=1, role="ADMIN")
    mock_decode_token.return_value = ObjectDict(exp=11111, iat=22222)

    flaskel_app.config.JWT_DEFAULT_TOKEN_TYPE = "bearer"
    flaskel_app.config.JWT_DEFAULT_SCOPE = "test-scope"

    with flaskel_app.app_context():
        token_data = BaseTokenHandler().refresh()

    Asserter.assert_equals(
        token_data.to_dict(),
        ObjectDict(
            expires_in=11111,
            issued_at=22222,
            token_type="bearer",
            scope="test-scope",
            access_token="fake-access-token",
        ),
    )


@patch("flaskel.ext.auth.decode_token")
def test_db_token_handler(mock_decode_token):
    mock_decode_token.return_value = ObjectDict(exp=11111, iat=22222, jti="fake")

    handler = DBTokenHandler(model=MagicMock(), session=MagicMock())
    handler.check_token_block_listed(jwt_headers=MagicMock(), jwt_data={"jti": "fake"})
    handler.model.is_block_listed.assert_called_once_with("fake")

    handler.revoke("fake-token")
    handler.session.add.assert_called_once()


@patch("flaskel.ext.auth.decode_token")
def test_redis_token_handler(mock_decode_token):
    mock_decode_token.return_value = ObjectDict(exp=11111, iat=22222, jti="fake-jti")
    mock_redis = MagicMock()

    handler = RedisTokenHandler(redis=mock_redis)
    mock_redis.get.return_value = handler.entry_value
    Asserter.assert_true(
        handler.check_token_block_listed(
            jwt_headers=MagicMock(), jwt_data={"jti": "fake-jti"}
        )
    )

    handler.revoke("fake-token")
    handler.redis.set.assert_called_once_with(
        f"{handler.key_prefix}fake-jti", handler.entry_value
    )
