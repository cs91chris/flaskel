from vbcore.tester.mixins import Asserter

from flaskel.ext.default import argon2


def test_init_app(flaskel_app):
    argon2.init_app(flaskel_app)
    Asserter.assert_equals(flaskel_app.extensions["argon2"], argon2)
    Asserter.assert_equals(flaskel_app.config.ARGON2_ENCODING, "utf-8")


def test_verify(flaskel_app):
    argon2.init_app(flaskel_app)
    argon2.verify(argon2.hash("password"), "password")
