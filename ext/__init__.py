# import flask extension here
#
from ext.default import errors
from ext.default import logger


EXTENSIONS = (
    # (extension, parameters)
    (logger,),
    (errors,),
)
