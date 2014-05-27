import sys
import os
import logging

LOG_FILE = sys.argv[0].strip("./").split(".")[0] + ".log"
LOG_FILE_PATH = os.getcwd()

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
# log to file
fh = logging.FileHandler(LOG_FILE, mode='w')
fh.setLevel(logging.DEBUG)
fh_format = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
fh.setFormatter(fh_format)
log.addHandler(fh)
# log to console
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch_format = logging.Formatter('%(message)s')
ch.setFormatter(ch_format)
log.addHandler(ch)

