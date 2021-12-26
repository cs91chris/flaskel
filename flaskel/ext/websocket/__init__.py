from flaskel.config import config

try:
    from flask_socketio import SocketIO

    IO_ASYNC_MODE = config("IO_ASYNC_MODE", default=None)
    IO_CORS_ORIGINS = config("IO_CORS_ORIGINS", default="*")
    IO_LOG_ENABLED = config("IO_LOG_ENABLED", default=True, cast=bool)

    socketio = SocketIO(
        async_mode=IO_ASYNC_MODE,
        logger=IO_LOG_ENABLED,
        engineio_logger=IO_LOG_ENABLED,
        cors_allowed_origins=IO_CORS_ORIGINS,
    )
except ImportError:
    socketio = None  # pylint: disable=invalid-name
