# import flask extension here
#
from ext.default import errors
from ext.default import logger
from ext.default import cors


EXTENSIONS = (
    # (extension, parameters)
    (logger,),
    (errors,),
)
