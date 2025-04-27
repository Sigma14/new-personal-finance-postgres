#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""Unit test for goslate module"""

from __future__ import unicode_literals

import doctest
import io
import itertools
import os
import sys
import types
import unittest
import warnings

import goslate
from goslate import *
from goslate import _get_current_thread, _main

__author__ = "ZHUO Qiang"
__date__ = "2013-05-14"

import concurrent.futures

executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)

gs = Goslate(debug=False, executor=executor)


class UnitTest(unittest.TestCase):
    if sys.version < "3":
        pass
    else:
        assertRaisesRegexp = unittest.TestCase.assertRaisesRegex

    def assertIsGenerator(self, generator):
        if not isinstance(generator, types.GeneratorType) and not isinstance(
            generator, itertools.chain
        ):
            raise self.failureException(
                "type is not generator: %s, %s" % (type(generator), generator)
            )

    def assertGeneratorEqual(self, expectedResult, generator):
        self.assertIsGenerator(generator)
        self.assertListEqual(list(expectedResult), list(generator))

    def test_get_current_thread(self):
        with warnings.catch_warnings(record=True) as w:
            # Cause all warnings to always be triggered.
            warnings.simplefilter("always")
            current_thread = _get_current_thread()
            self.assertEqual(len(w), 0)
            self.assertTrue(current_thread is not None)

    def test_translate_space(self):
        self.assertEqual(
            "hallo\n welt", gs.translate("hello\n world", "de", "en").lower()
        )

    def test_translate_roman(self):
        gs = Goslate(writing=WRITING_ROMAN)
        self.assertEqual("", gs.translate(b"\n \n\t\n", "en"))
        self.assertEqual(
            "N\u01d0 h\u01ceo sh\xecji\xe8.".lower(),
            gs.translate(b"hello world.", "zh").lower(),
        )
        self.assertEqual("heˈlō,həˈlō", gs.translate(b"hello", "de"))
        self.assertGeneratorEqual(
            ["Nín h\u01ceo", "sh\xecji\xe8"], gs.translate(
                [b"hello", "world"], "zh")
        )

    def test_translate_native_and_roman(self):
        gs = Goslate(WRITING_NATIVE_AND_ROMAN)
        self.assertEqual(("", ""), gs.translate(b"\n \n\t\n", "en"))
        self.assertEqual(
            ("你好世界。", "N\u01d0 h\u01ceo sh\xecji\xe8."),
            gs.translate(b"hello world.", "zh"),
        )
        self.assertEqual(("Hallo", ""), gs.translate(b"Hello", "de"))

        self.assertGeneratorEqual(
            [("您好", "Nín h\u01ceo"), ("世界", "sh\xecji\xe8")],
            gs.translate([b"hello", "world"], "zh"),
        )

    def test_lookup_dictionary(self):
        r = gs.lookup_dictionary("apple", "zh")
        self.assertTrue(isinstance(r, list))
        self.assertEqual(r[0][0][0], "苹果")
        self.assertEqual(r[1][0][0], "noun")
        self.assertEqual(r[1][0][0], "noun")
        self.assertEqual(r[1][0][1][0], "苹果")

    def test_translate(self):
        self.assertEqual("", gs.translate(b"\n \n\t\n", "en"))

        self.assertEqual("你好世界。", gs.translate(b"hello world.", "zh"))
        self.assertEqual("Hello World.", gs.translate("你好世界。", "en", "zh"))
        self.assertEqual(
            "Hello World.", gs.translate("你好世界。".encode("utf-8"), "en")
        )
        self.assertEqual("你好世界。", gs.translate(b"hello world.", "zh-cn", "en"))
        self.assertEqual("你好世界。", gs.translate(b"hallo welt.", "zh-CN"))
        self.assertEqual("你好世界。", gs.translate("hallo welt.", "zh-CN", "de"))

        self.assertRaisesRegexp(
            Error, "invalid target language", gs.translate, "", "")

        self.assertNotEqual("你好世界。", gs.translate(
            b"hallo welt.", "zh-CN", "en"))

        test_string = b"helloworld"
        exceed_allowed_times = int(
            gs._MAX_LENGTH_PER_QUERY / len(test_string) + 10)
        self.assertRaisesRegexp(
            Error,
            "input too large",
            gs.translate,
            test_string * exceed_allowed_times,
            "zh",
        )

        self.assertRaisesRegexp(
            Error, "invalid target language", gs.translate, "hello", ""
        )

        self.assertEqual(
            "你好世界。\n\n您好", gs.translate(
                "\n\nhello world.\n\nhello\n\n", "zh-cn")
        )

        test_string = "hello!    "
        exceed_allowed_times = int(
            gs._MAX_LENGTH_PER_QUERY / len(test_string) + 10)
        self.assertEqual(
            "您好！" * exceed_allowed_times,
            gs.translate(test_string * exceed_allowed_times, "zh"),
        )

    def test_translate_batch_input(self):
        self.assertGeneratorEqual([], gs.translate((), "en"))
        self.assertGeneratorEqual([""], gs.translate([b"\n \n\t\n"], "en"))
        self.assertGeneratorEqual(
            ["你好世界。"], gs.translate(["hello world."], "zh-cn")
        )
        self.assertGeneratorEqual(
            ["你好世界。"], gs.translate([b"hello world."], "zh-CN", "en")
        )
        self.assertGeneratorEqual(
            ["你好世界。"], gs.translate([b"hallo welt."], "zh-CN")
        )
        self.assertGeneratorEqual(
            ["你好世界。\n\n您好"],
            gs.translate([b"\n\nhello world.\n\nhello\n\n"], "zh-cn"),
        )
        self.assertNotEqual(
            ["你好世界。"], gs.translate([b"hallo welt."], "zh-CN", "en")
        )
        self.assertRaisesRegexp(
            Error, "invalid target language", gs.translate, [""], ""
        )

        test_string = b"hello!    "
        exceed_allowed_times = int(
            gs._MAX_LENGTH_PER_QUERY / len(test_string) + 10)
        self.assertGeneratorEqual(
            ["您好！" * exceed_allowed_times] * 3,
            gs.translate((test_string * exceed_allowed_times,) * 3, "zh"),
        )
        self.assertGeneratorEqual(
            ["你好世界。", "您好"],
            gs.translate([b"\n\nhello world.\n", b"\nhello\n\n"], "zh-cn"),
        )

    def test_translate_batch_input_exceed(self):
        test_string = b"helloworld"
        exceed_allowed_times = int(
            gs._MAX_LENGTH_PER_QUERY / len(test_string) + 1)
        self.assertRaisesRegexp(
            Error,
            "input too large",
            list,
            gs.translate(
                (
                    "hello",
                    test_string * exceed_allowed_times,
                ),
                "zh",
            ),
        )

    def test_translate_batch_input_with_empty_string(self):
        self.assertGeneratorEqual(
            ["你好世界。", ""], gs.translate(["hello world.", ""], "zh-cn")
        )
        self.assertGeneratorEqual(
            ["你好世界。", "", "你好"],
            gs.translate(["hello world.", "", "hello"], "zh-cn"),
        )
        self.assertGeneratorEqual(
            ["", "你好世界。"], gs.translate(["", "hello world."], "zh-cn")
        )

    def test_detect(self):
        self.assertEqual("en", gs.detect(b""))
        self.assertEqual("en", gs.detect(b"\n\r  \n"))
        self.assertEqual("en", gs.detect(b"hello world"))
        self.assertEqual("zh-CN", gs.detect("你好世界".encode("utf-8")))
        self.assertEqual("de", gs.detect("hallo welt."))

        self.assertEqual("zh-CN", gs.detect("你好世界".encode("utf-8") * 1000))

    def test_detect_batch_input(self):
        times = 10
        self.assertGeneratorEqual(
            ["en", "zh-CN", "de", "en"] * 10,
            gs.detect(
                ("hello world", "你好世界".encode("utf-8"), "hallo welt.", "") * 10
            ),
        )

        self.assertGeneratorEqual(
            ["en", "zh-CN", "de", "en"] * 10,
            gs.detect(
                [
                    b"hello world" * 10,
                    "你好世界" * 100,
                    b"hallo welt." * times,
                    "\n\r \t" * times,
                ]
                * 10
            ),
        )

    def test_translate_massive_input(self):
        times = 10
        source = ("hello world. " for i in range(times))
        result = gs.translate((i.encode("utf-8") for i in source), "zh-cn")
        self.assertGeneratorEqual(("你好世界。" for i in range(times)), result)

    def test_main(self):
        encoding = sys.getfilesystemencoding()
        # sys.stdout = StringIO()

        sys.stdout = io.BytesIO()
        sys.stdin = io.BytesIO(b"hello world")
        sys.stdin.buffer = sys.stdin
        _main([sys.argv[0], "-t", "zh-CN"])
        self.assertEqual("你好世界\n".encode(encoding), sys.stdout.getvalue())

        sys.stdout = io.BytesIO()
        sys.stdin = io.BytesIO("苹果".encode(encoding))
        sys.stdin.buffer = sys.stdin
        _main([sys.argv[0], "-t", "en"])
        self.assertEqual("apple\n".encode(encoding), sys.stdout.getvalue())

        sys.stdout = io.BytesIO()
        sys.stdin = io.BytesIO(b"hello world")
        sys.stdin.buffer = sys.stdin
        _main([sys.argv[0], "-t", "zh-CN", "-o", "utf-8"])
        self.assertEqual("你好世界\n".encode("utf-8"), sys.stdout.getvalue())

        sys.stdout = io.BytesIO()
        sys.stdin = io.BytesIO("苹果".encode("utf-8"))
        sys.stdin.buffer = sys.stdin
        _main([sys.argv[0], "-t", "en", "-i", "utf-8"])
        self.assertEqual("apple\n".encode(encoding), sys.stdout.getvalue())

        sys.stdout = io.BytesIO()
        with open("for_test.tmp", "w") as f:
            f.write("hello world")
        _main([sys.argv[0], "-t", "zh-CN", f.name])
        self.assertEqual("你好世界\n".encode(encoding), sys.stdout.getvalue())

        sys.stdout = io.BytesIO()
        with open("for_test.tmp", "w") as f:
            f.write("hello world")
        _main([sys.argv[0], "-t", "zh-CN", "-o", "utf-8", f.name])
        self.assertEqual("你好世界\n".encode("utf-8"), sys.stdout.getvalue())

        sys.stdout = io.BytesIO()
        with io.open("for_test.tmp", "w", encoding=encoding) as f:
            f.write("苹果")
        _main([sys.argv[0], "-t", "en", f.name])
        self.assertEqual("Apple\n".encode(encoding), sys.stdout.getvalue())

        sys.stdout = io.BytesIO()
        with io.open("for_test.tmp", "w", encoding="utf-8") as f:
            f.write("苹果")
        _main([sys.argv[0], "-t", "en", "-i", "utf-8", f.name])
        self.assertEqual("Apple\n".encode(encoding), sys.stdout.getvalue())

        sys.stdout = io.BytesIO()
        with io.open("for_test.tmp", "w", encoding="utf-8") as f:
            f.write("苹果")
        with io.open("for_test_2.tmp", "w", encoding="utf-8") as f2:
            f2.write("世界")

        _main([sys.argv[0], "-t", "en", "-i", "utf-8", f.name, f2.name])
        self.assertEqual("apple\nworld\n".encode(
            encoding), sys.stdout.getvalue())

    def test_get_languages(self):
        expected = {
            "el": "Greek",
            "eo": "Esperanto",
            "en": "English",
            "zh": "Chinese",
            "af": "Afrikaans",
            "sw": "Swahili",
            "ca": "Catalan",
            "it": "Italian",
            "iw": "Hebrew",
            "cy": "Welsh",
            "ar": "Arabic",
            "ga": "Irish",
            "cs": "Czech",
            "et": "Estonian",
            "gl": "Galician",
            "id": "Indonesian",
            "es": "Spanish",
            "ru": "Russian",
            "nl": "Dutch",
            "pt": "Portuguese",
            "mt": "Maltese",
            "tr": "Turkish",
            "lt": "Lithuanian",
            "lv": "Latvian",
            "tl": "Filipino",
            "th": "Thai",
            "vi": "Vietnamese",
            "ro": "Romanian",
            "is": "Icelandic",
            "pl": "Polish",
            "yi": "Yiddish",
            "be": "Belarusian",
            "fr": "French",
            "bg": "Bulgarian",
            "uk": "Ukrainian",
            "sl": "Slovenian",
            "hr": "Croatian",
            "de": "German",
            "ht": "Haitian Creole",
            "da": "Danish",
            "fa": "Persian",
            "hi": "Hindi",
            "fi": "Finnish",
            "hu": "Hungarian",
            "ja": "Japanese",
            "zh-TW": "Chinese (Traditional)",
            "sq": "Albanian",
            "no": "Norwegian",
            "ko": "Korean",
            "sv": "Swedish",
            "mk": "Macedonian",
            "sk": "Slovak",
            "zh-CN": "Chinese (Simplified)",
            "ms": "Malay",
            "sr": "Serbian",
        }

        result = gs.get_languages()
        expected_keys = set(expected.keys())
        result_keys = set(result.keys())
        self.assertLessEqual(expected_keys, result_keys)
        for key, value in expected.items():
            self.assertEqual(value, result.get(key, None))

        # self.assertDictEqual(expected, gs.get_languages())


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(goslate))
    return tests


if __name__ == "__main__":
    unittest.main()
