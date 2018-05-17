# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from wolframclient.language.expression import wl
from wolframclient.serializers import available_formats, export
from wolframclient.utils import six
from wolframclient.utils.functional import identity
from wolframclient.utils.tests import TestCase as BaseTestCase

import os
import tempfile

class TestCase(BaseTestCase):

    def test_export(self):

        #checking that export is able to return bytes if no second argument is provided

        self.assertEqual(export(2),     b'2')
        self.assertEqual(export("foo"), b'"foo"')

        _, path = tempfile.mkstemp()

        for test in ["foo", wl.Symbol, {"a": [1, 2, 3], 2:2}]:

            for export_format in available_formats:

                expected = export(test, format = export_format)

                #checking that export is able to write to a path if a string is provided

                export(test, path, format = export_format)

                with open(path,'rb') as stream:
                    self.assertEqual(stream.read(), expected)

                #checking that export is writing to a byteio

                stream = six.BytesIO()

                export(test, stream, format = export_format)

                stream.seek(0)

                self.assertEqual(stream.read(), expected)

                #checking that export is able to write to a filelike object

                with open(path,'wb') as stream:
                    export(test, stream, format = export_format)

                with open(path,'rb') as stream:
                    self.assertEqual(stream.read(), expected)

        os.remove(path)

    def test_serialization_custom(self):

        class MyStuff(object):

            def __init__(self, *stuff):
                self.stuff = stuff

        def normalizer(o):
            if isinstance(o, six.integer_types):
                return 'o'
            if isinstance(o, MyStuff):
                return wl.RandomThings(*o.stuff)
            return o

        expr       = [1, 2, 'a', {1:"a"}, MyStuff(1, 2, MyStuff(1, 'a'))]
        normalized = ["o", "o", "a", {"o": "a"}, wl.RandomThings("o", "o", wl.RandomThings("o", "a"))]

        for export_format in available_formats:

            with self.assertRaises(NotImplementedError) as context:
                export(
                    expr,
                    normalizer = identity,
                    format = export_format
                )

            self.assertEqual(
                export(
                    expr,
                    normalizer = normalizer,
                    format = export_format
                ),
                export(
                    normalized,
                    normalizer = identity,
                    format = export_format
                ),
            )