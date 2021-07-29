import errno
import getopt
import json
import logging
import os
import sys

from publisher.src.publish_documents import PublishDocuments
METADATA_FILE_NAME = "metadata.json"
AUTOMATION_DOCUMENT_FINAL_NAME = 'AutomationDocumentFinal.yml'

default_logger = logging.getLogger('GenerateDocuments')

USAGE = "usage: generate_document.py -l <log-level>  [--clean]"


class GenerateDocuments:
    @staticmethod
    def generate():
        for document_dir in GenerateDocuments.collect_files():
            final_document_name = os.path.join(document_dir, AUTOMATION_DOCUMENT_FINAL_NAME)
            with open(os.path.join(document_dir, METADATA_FILE_NAME)) as metadata_file:
                document_metadata = json.load(metadata_file)
                document_content = PublishDocuments.get_final_document_content(document_dir,
                                                                               document_metadata)
                with open(final_document_name, 'w') as automation_document_output:
                    automation_document_output.write(document_content)
                logging.info(f"Generated {final_document_name}")

    @staticmethod
    def clean():
        for document_dir in GenerateDocuments.collect_files():
            final_document_name = os.path.join(document_dir, AUTOMATION_DOCUMENT_FINAL_NAME)
            try:
                os.remove(final_document_name)
                logging.info(f"Removing {final_document_name}")
            except OSError as e:  # this would be "except OSError, e:" before Python 2.6
                if e.errno != errno.ENOENT:  # errno.ENOENT = no such file or directory
                    raise  # re-raise exception if a different error occurred

    @staticmethod
    def collect_files():
        script_dir = os.path.dirname(os.path.abspath(__file__))
        for root, dirs, files in os.walk(os.path.abspath(os.path.join(script_dir, '../../documents'))):
            if "alarm" in dirs:
                dirs.remove("alarm")

            for f in files:
                if f == METADATA_FILE_NAME:
                    yield root


def main(argv):
    log_level = logging.INFO
    clean_only = False
    try:
        opts, args = getopt.getopt(argv, "hcl:", ["log-level=", "clean"])
    except getopt.GetoptError:
        print(USAGE)
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print(USAGE)
            sys.exit()
        elif opt in ("-l", "--log-level"):
            log_level = arg
        elif opt in ("-c", "--clean"):
            clean_only = True

    logging.basicConfig(
        format='%(asctime)s %(name)s %(levelname)s:%(message)s',
        level=log_level,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ])

    if clean_only:
        GenerateDocuments.clean()
    else:
        GenerateDocuments.generate()


if __name__ == "__main__":
    main(sys.argv[1:])
