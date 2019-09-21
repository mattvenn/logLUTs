#!/usr/bin/env python

import re
import csv
import os
import argparse
import datetime
import sys

flops = 0
luts = 0
max_freq = 0

print(os.getcwd())

parser = argparse.ArgumentParser(description="logLUTs - parse yosys and nextpnr logs to log FPGA resource usage")
parser.add_argument('--yosys-log', action='store', default="yosys.log")
parser.add_argument('--nextpnr-log', action='store', default="nextpnr.log")
parser.add_argument('--csvfile', action='store', default="LUTs.csv")
parser.add_argument('--message', action='store', default="no message")
parser.add_argument('--commit', action='store', default="no commit")
args = parser.parse_args()

if not os.path.isfile(args.yosys_log):
    sys.exit("couldn't find yosys log %s" % args.yosys_log)
if not os.path.isfile(args.nextpnr_log):
    sys.exit("couldn't find yosys log %s" % args.yosys_log)

with open(args.yosys_log) as fh:
    for line in fh.readlines():
        m = re.search("SB_DFF[ESR]*[ ]+(\d+)", line)
        if m is not None:
            flops += int(m.group(1))
        m = re.search("SB_LUT4[ ]+(\d+)", line)
        if m is not None:
            luts += int(m.group(1))

with open(args.nextpnr_log) as fh:
    for line in fh.readlines():
        m = re.search("Info: Max frequency.*?(\d+.\d+) MHz", line)
        if m is not None:
            max_freq = float(m.group(1))

print("flops %d" % flops)
print("luts %d" % luts)
print("max freq %2.2f MHz" % max_freq)

csvfile_created = False
if os.path.isfile(args.csvfile):
    print("found existing csvfile %s" % args.csvfile)
    csvfile_created = True
    
with open(args.csvfile, 'a+') as csvfile:
    fieldnames = ['date', 'commit', 'message', 'flops', 'luts', 'freq']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    if not csvfile_created:
        print("writing header")
        writer.writeheader()

    writer.writerow({
                        'date'      : datetime.date.today(),
                        'commit'    : args.commit,
                        'message'   : args.message,
                        'flops'     : flops,
                        'luts'      : luts,
                        'freq'      : max_freq })
