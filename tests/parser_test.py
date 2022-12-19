import unittest
import sys
sys.path.append("../")
from parser import DocParser

class TestDocParser(unittest.TestCase):
    def test_parse(self):
        # Create a DocParser instance
        parser = DocParser("data/test/burry.txt", "13F")

        # Call the parse method with the test data
        parser.parse()

        # Check that the parsed data is correct
        self.assertEqual(parser.parsed_data["document_name"].strip(), "0001567619-22-010747.txt")
        self.assertEqual(parser.parsed_data["date"].strip(), "20220516")
        self.assertEqual(parser.parsed_data["header_name"].strip(), "0001567619-22-010747.hdr.sgml")
        # self.assertEqual(parser.parsed_data["acceptance_datetime"], "20220416162719")
        # self.assertEqual(parser.parsed_data["filer"], "Test Company")
        # self.assertEqual(parser.parsed_data["filer-cik"], "0001048685")
        # self.assertEqual(parser.parsed_data["filer-type"], "Form 13F")
        # self.assertEqual(parser.parsed_data["filer-company-data"], "Test Company Data")
        # self.assertEqual(parser.curr_doc["document"], "This is a test document.\nIt has multiple lines of text.")