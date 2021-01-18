import unittest
import os
from pathlib import Path
import pad

class AspBasicParserTests(unittest.TestCase):

    def test_ut_files(self):
        path = os.path.join(str(Path(__file__).parent), "unittests")
        for file in os.listdir(path):
            if file.endswith(".ut"):
                with open(os.path.join(path, file), 'r') as file_content:
                    content = file_content.readlines()
                    asp_end_index = content.index("%>\n") + 1
                    source = content[:asp_end_index]
                    result = content[asp_end_index:]
                    with self.subTest(file):
                        lexer = pad.Lexer()
                        lexer.lex(source)
                        if len(lexer.errors) > 0:
                            self.assertEqual(lexer.errors, result)
                        else:
                            parser = pad.Parser()
                            parser.parse(lexer.source_tokens)
                            self.assertEqual(parser.errors, result)

    #def test_sample(self):
    #    self.assertTrue('FOO'.isupper())
    #    self.assertFalse('Foo'.isupper())
    #    self.assertEqual('foo'.upper(), 'FOO')
    #    s = 'hello world'
    #    self.assertEqual(s.split(), ['hello', 'world'])
    #    with self.assertRaises(TypeError):
    #        s.split(2)

if __name__ == '__main__':
    unittest.main()
