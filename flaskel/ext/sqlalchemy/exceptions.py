# taken from: https://github.com/openstack/oslo.db

#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
Define exception redefinitions for SQLAlchemy DBAPI exceptions
"""
from sqlalchemy.exc import SQLAlchemyError


class DBError(SQLAlchemyError):
    """
    Base exception for all custom database exceptions.

    :kwarg inner_exception: an original exception which was wrapped with
        DBError or its subclasses.
    """

    def __init__(self, inner_exception=None):
        self.inner_exception = inner_exception
        super().__init__(str(inner_exception))

    @property
    def error_type(self):
        return self.__class__.__name__

    def as_dict(self):
        return {
            "error": self.error_type,
        }


class DBDuplicateEntry(DBError):
    """
    Duplicate entry at unique column error.
    Raised when made an attempt to write to a unique column the same entry as
    existing one. :attr: `columns` available on an instance of the exception
    and could be used at error handling::
       try:
           instance_type_ref.save()
       except DBDuplicateEntry as e:
           if 'colname' in e.columns:
               # Handle error.

    :kwarg columns: a list of unique columns have been attempted to write a
        duplicate entry.
    :type columns: list
    :kwarg value: a value which has been attempted to write. The value will
        be None, if we can't extract it for a particular database backend. Only
        MySQL and PostgreSQL 9.x are supported right now.
    """

    def __init__(self, columns=None, inner_exception=None, value=None):
        self.value = value
        self.columns = columns or []
        super().__init__(inner_exception)

    def as_dict(self):
        return {
            "error": self.error_type,
            "columns": self.columns,
            "value": self.value,
        }


class DBConstraintError(DBError):
    """
    Check constraint fails for column error.
    Raised when made an attempt to write to a column a value that does not
    satisfy a CHECK constraint.

    :kwarg table: the table name for which the check fails
    :type table: str
    :kwarg check_name: the table of the check that failed to be satisfied
    :type check_name: str
    """

    def __init__(self, table, check_name, inner_exception=None):
        self.table = table
        self.check_name = check_name
        super().__init__(inner_exception)

    def as_dict(self):
        return {
            "error": self.error_type,
            "table": self.table,
            "check_name": self.check_name,
        }


class DBReferenceError(DBError):
    """
    Foreign key violation error.

    :param table: a table name in which the reference is directed.
    :type table: str
    :param constraint: a problematic constraint name.
    :type constraint: str
    :param key: a broken reference key name.
    :type key: str
    :param key_table: a table name which contains the key.
    :type key_table: str
    """

    def __init__(self, table, constraint, key, key_table, inner_exception=None):
        self.key = key
        self.table = table
        self.key_table = key_table
        self.constraint = constraint
        super().__init__(inner_exception)

    def as_dict(self):
        return {
            "error": self.error_type,
            "table": self.table,
            "key_table": self.key_table,
            "key": self.key,
            "constraint": self.constraint,
        }


class DBNonExistentConstraint(DBError):
    """
    Constraint does not exist.

    :param table: table name
    :type table: str
    :param constraint: constraint name
    :type table: str
    """

    def __init__(self, table, constraint, inner_exception=None):
        self.table = table
        self.constraint = constraint
        super().__init__(inner_exception)

    def as_dict(self):
        return {
            "error": self.error_type,
            "table": self.table,
            "constraint": self.constraint,
        }


class DBNonExistentTable(DBError):
    """
    Table does not exist.

    :param table: table name
    :type table: str
    """

    def __init__(self, table, inner_exception=None):
        self.table = table
        super().__init__(inner_exception)

    def as_dict(self):
        return {
            "error": self.error_type,
            "table": self.table,
        }


class DBNonExistentDatabase(DBError):
    """
    Database does not exist.

    :param database: database name
    :type database: str
    """

    def __init__(self, database, inner_exception=None):
        self.database = database
        super().__init__(inner_exception)

    def as_dict(self):
        return {
            "error": self.error_type,
            "database": self.database,
        }


class DBDeadlock(DBError):
    """
    Database dead lock error.
    Deadlock is a situation that occurs when two or more different database
    sessions have some data locked, and each database session requests a lock
    on the data that another, different, session has already locked.
    """


class DBInvalidUnicodeParameter(Exception):
    """
    Database unicode error.
    Raised when unicode parameter is passed to a database
    without encoding directive.
    """

    def __init__(self):
        super().__init__("Invalid Parameter: Encoding directive wasn't provided.")


class DBConnectionError(DBError):
    """
    Wrapped connection specific exception.
    Raised when database connection is failed.
    """


class DBDataError(DBError):
    """
    Raised for errors that are due to problems with the processed data.
    E.g. division by zero, numeric value out of range, incorrect data type, etc
    """


class DBNotSupportedError(DBError):
    """
    Raised when a database backend has raised sqla.exc.NotSupportedError
    """
