# filings/2022/QTR2/1001085/0000950123-22-004046.txt


# PARSE SEC-DOCUMENT, enforce SEC DOCUMENT TAG OPENER

# FOLLOWED BY LOGIC TO PARSE SEC-HEADER
# parse metadata until first blank line
# parse filer
import sys
import pandas as pd
import xml.etree.ElementTree as ET
from xml.etree import ElementTree
from enum import Enum


class ParsingMode(Enum):
    HEADER = 1
    FILER = 2
    DOCUMENT = 3

class DocParser():
    def __init__(self, file_path, file_type):
        self.file_path = file_path
        self.type = "13F" 

        self.lines = []
        self.mode = ParsingMode.HEADER
        self.parsed_data = {}

        # this is True after we find a xml tag
        # and then False after we find a xml closing tag
        self.curr_header = ""
        self.xml_tag_found_line = None

        # documeny within text file.
        self.curr_doc = {}

    @staticmethod
    def split_by_semicolon(line: str):
        # split by colon and return two entries
        # if no colon, return None
        if ":" not in line:
            return None, None
        else:
            return line.split(":")[0], line.split(":")[1]

    @staticmethod
    def strip_tag(line: str):
        """
            Example: <SEC-DOCUMENT>0000950123-22-004046.txt : 20220415
            Returns: 0000950123-22-004046.txt : 20220415
        """
        # strip tag from line
        # if no tag, return None
        if "<" not in line:
            return None
        else:
            try:
                return line.split(">")[1]
            except IndexError as e:
                print(e)
                return line

    @staticmethod
    def strip_xml_ns(line: str):
        """
            Example: <ns0:infoTable>, for an xml tag the namespace would be "{http://www.sec.gov/edgar/document/thirteenf/informationtable}nameOfIssuer"
            Returns: nameOfIssuer
        """
        # strip xml namespace from line
        # if no namespace, return None
        if "}" not in line:
            return None
        else:
            return line.split("}")[1]

    @staticmethod
    def iter_docs(doc_table: ElementTree):
        for info_table in doc_table:
            doc_dict = {}
            # move inner text from info_table to doc_dict for each element that has no children
            for child in info_table:
                # check if child has children
                # if child has no children, move text to doc_dict
                tag = DocParser.strip_xml_ns(child.tag)
                if len(child) == 0 and child.text is not None:
                    # get tag without namespace
                    doc_dict[tag] = child.text
                
                # for shrsOrPrnAmt
                # <sshPrnamt>76200</sshPrnamt>
				# <sshPrnamtType>SH</sshPrnamtType>
                # add sshPrnamt and sshPrnamtType to doc_dict
                if tag == "shrsOrPrnAmt":
                    for elem in child:
                        new_tag = DocParser.strip_xml_ns(elem.tag)
                        # get tag without namespace
                        doc_dict[new_tag] = elem.text
            yield doc_dict
        else:
            return

    def parse(self):
        with open(self.file_path, "r") as f:
            # sec files are somewhat short so we can read them all into memory
            lines = [line.rstrip('\n') for line in f]
        # enumerate across lines
        for i, line in enumerate(lines):
            # check if line is a tag
            if line.startswith("<"):
                clean_line = DocParser.strip_tag(line)
                # check if tag is sec-document
                if line.startswith("<SEC-DOCUMENT>"):
                    document_name, date = DocParser.split_by_semicolon(clean_line)
                    self.parsed_data["document_name"] = document_name
                    self.parsed_data["date"] = date
                    continue
                    # parse sec-document
                    # extract
                if line.startswith("<SEC-HEADER>"):
                    header_name, date = DocParser.split_by_semicolon(clean_line)
                    self.parsed_data["header_name"] = header_name
                    self.parsed_data["date"] = date
                    continue
                    # parse sec-header
                if line.startswith("<ACCEPTANCE-DATETIME>"):
                    self.parsed_data["acceptance_datetime"] = clean_line
                    continue
            
            if self.parsed_data.get("header_name") is not None and self.mode == ParsingMode.HEADER:
                if line.strip() == "":
                    self.mode = ParsingMode.FILER
                    continue
                raw_header, label = DocParser.split_by_semicolon(line)
                # replace spaces with underscores
                metadata_header = raw_header.replace(" ", "_").lower()
                self.parsed_data[metadata_header] = label.replace("\t", "")

            if self.mode == ParsingMode.FILER:
                # remove tabs
                if line.strip() == "":
                    continue
                # check for colon in line
                if ":" in line:
                    clean_line = line.replace("\t", "")
                    label, data = DocParser.split_by_semicolon(clean_line)
                    # clean \t from data
                    # replace spaces with underscores
                    if label is not None:
                        label = label.replace(" ", "_").lower()
                        if label == "filer":
                            self.parsed_data[label] = {}
                            continue
                        if data.strip() == "":
                            data_label = label
                            # check if filer.label exists
                            if self.parsed_data["filer"].get(label) is None:
                                self.parsed_data["filer"][data_label] = {}
                            else:
                                # check if filer_data_label is an object, if so, make it an array
                                if isinstance(self.parsed_data["filer"][label], dict):
                                    self.parsed_data["filer"][label] = [self.parsed_data["filer"][label]]
                            self.curr_header = data_label
                        else:
                            # check if filter_label is an array, if so append to array
                            if isinstance(self.parsed_data["filer"][self.curr_header], list):
                                self.parsed_data["filer"][self.curr_header].append({label: data})
                            else:
                                self.parsed_data["filer"][self.curr_header][label] = data
                        continue
                    else:
                        self.curr_header = ""
                        continue

                        

                if line.startswith("</SEC-HEADER>"):
                    self.curr_header = ""
                    self.mode = ParsingMode.DOCUMENT
                    continue

            if self.mode == ParsingMode.DOCUMENT:
                if line.startswith("<DOCUMENT>"):
                    continue
                if line.startswith("<TYPE>"):
                    raw_line = DocParser.strip_tag(line)
                    self.curr_doc["type"] = raw_line.replace(" ", "_")
                    continue
                if line.startswith("<SEQUENCE>"):
                    self.curr_doc["sequence"] = DocParser.strip_tag(line)
                    continue
                if line.startswith("<FILENAME>"):
                    self.curr_doc["filename"] = DocParser.strip_tag(line)
                    continue
                if line.startswith("<TEXT>"):
                    continue
                if line.startswith("<XML>"):
                    self.xml_tag_found_line = i+1
                    continue
                if line.startswith("</XML>"):
                    # line is current line
                    # grab all lines from xml_tag_found_line to current line
                    xml_lines = lines[self.xml_tag_found_line:i]
                    # join lines with newlines
                    xml = "\n".join(xml_lines)
                    # parse xml
                    self.curr_doc["raw_xml"] = xml
                    # parse xml using xml.eTree
                    etree = ET.fromstring(xml)
                    self.curr_doc["xml"] = etree
 
                    if self.curr_doc["type"] == "INFORMATION_TABLE":
                        # iterate across each infoTable element
                        parsed_data = list(DocParser.iter_docs(etree))
                        doc_df = pd.DataFrame(parsed_data)
                        # doc_df.to_csv("data/test/burry.csv", index=False)
                        self.curr_doc["df"] = doc_df
                    if self.curr_doc["type"] == "13F-HR":
                        pass

                    if self.parsed_data.get("documents") is None:
                        self.parsed_data["documents"] = []
                    self.parsed_data["documents"].append(self.curr_doc)
                    self.curr_doc = {}
        return self.parsed_data["documents"]

    def get_parsed_data(self):
        return self.parsed_data


if __name__ == "__main__":
    parser = DocParser("data/test/burry.txt", "13F")
    parser.parse()
