import xml.etree.ElementTree as ET

from ..__init__ import __version__ as reporter_version
from .ci import CI
from .file_coverage import FileCoverage
from .git_command import GitCommand
import os

class Formatter:
    def __init__(self, xml_report_path, debug=False):
        self.debug = debug
        tree = ET.parse(xml_report_path)
        self.root = tree.getroot()

    def payload(self):
        total_line_counts = {"covered": 0, "missed": 0, "total": 0}
        total_covered_strength = 0.0
        total_covered_percent = 0.0

        source_files = self.__source_files()

        for source_file in source_files:
            total_covered_strength += source_file["covered_strength"]
            total_covered_percent += source_file["covered_percent"]

            for key, value in source_file["line_counts"].items():
                total_line_counts[key] += value

        total_covered_strength = round(total_covered_strength / len(source_files), 2)
        total_covered_percent = round(total_covered_percent / len(source_files), 2)

        return {
            "run_at": self.__timestamp(),
            "covered_percent": total_covered_percent,
            "covered_strength": total_covered_strength,
            "line_counts": total_line_counts,
            "partial": False,
            "git": self.__git_info(),
            "environment": {
                "pwd": self.root.find("sources").find("source").text,
                "reporter_version": reporter_version
            },
            "ci_service": self.__ci_data(),
            "source_files": source_files
        }

    def __ci_data(self):
        return CI().data()

    def __source_files(self):
        source_files = []

        for file_node in self.__file_nodes():
            if self.debug:
                print("Processing file path=%s" % file_node.get("filename"))
            file_coverage = FileCoverage(file_node)
            payload = file_coverage.payload()
            source_files.append(payload)

        return source_files

    def __source_dir(self):
        source_dir=self.root.find("sources/source").text
        return os.path.relpath(source_dir,os.getcwd())

    def __file_nodes(self):
        source_dir=self.__source_dir()
        file_nodes=self.root.findall("packages/package/classes/class")
        if source_dir:
            [ f.set( "filename", os.path.join( source_dir, f.get("filename") ) ) for f in file_nodes ]
        return file_nodes

    def __timestamp(self):
        return self.root.get("timestamp")

    def __git_info(self):
        ci_data = self.__ci_data()
        command = GitCommand()

        return {
            "branch": ci_data.get("branch") or command.branch(),
            "committed_at": command.committed_at(),
            "head": ci_data.get("commit_sha") or command.head()
        }
