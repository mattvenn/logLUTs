#!/usr/bin/env python3
import git
import re
import csv
import os
import argparse
import sys

def check_logs():
    if not os.path.isfile(args.yosys_log):
        sys.exit("couldn't find yosys log %s" % args.yosys_log)
    if not os.path.isfile(args.nextpnr_log):
        sys.exit("couldn't find nextpnr log %s" % args.nextpnr_log)

def parse_logs():
    flops = 0
    luts = 0
    max_freq = 0
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
    return flops, luts, max_freq

def add_to_log(commit, flops, luts, max_freq):
    csvfile_created = False
    if os.path.isfile(args.csvfile):
        print("found existing csvfile %s" % args.csvfile)
        csvfile_created = True
        
    with open(args.csvfile, 'a+') as csvfile:
        fieldnames = ['commit', 'flops', 'luts', 'freq']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if not csvfile_created:
            print("writing header")
            writer.writeheader()

        writer.writerow({   'commit'    : commit.hexsha,
                            'flops'     : flops,
                            'luts'      : luts,
                            'freq'      : max_freq })

def load_csv():
    with open(args.csvfile) as csvfile:
        fieldnames = ['commit', 'flops', 'luts', 'freq']
        reader = csv.DictReader(csvfile, fieldnames=fieldnames)
        return list(reader)[1:] # skip header

def plot(data):
    import matplotlib.pyplot as plt
    import matplotlib

    fig, ax = plt.subplots()

    repo = git.Repo(args.git)
    dates =  [repo.commit(d['commit']).committed_datetime for d in data]
    mesgs =  [repo.commit(d['commit']).message for d in data]
    flops = [int(d['flops'])  for d in data]
    luts  =  [int(d['luts'])   for d in data]
    freqs =  [float(d['freq']) for d in data]

    ax.grid()
    ax.plot(dates, flops, label='flops', marker='o')
    ax.plot(dates, luts,  label='luts', marker='o')
    ax.set_ylabel('count')
    ax_legend = ax.legend()
    ax_legend.remove()
    ax.set_title("flip-flops, LUTS and max frequency vs commits")

    ax2 = ax.twinx()
    freq_line, = ax2.plot(dates, freqs,  label='freq', color='green', marker='o')
    ax2.set_ylabel('MHz')
    ax2.legend()
    ax2.add_artist(ax_legend) # mess about to get the first ax legend on top of 2nd ax line

    commit_line = plt.axvline(dates[0], linewidth=2, color="gray", linestyle="--" )

    plt.gcf().autofmt_xdate()
    commit_details = fig.text(.5, .02, "hover over points to see commit info", ha='center')
    

    last_index = 0
    def hover(event):
        if event.inaxes == ax2:
            for index, d in enumerate(dates):
                if(matplotlib.dates.num2date(event.xdata) < d):
                    break
            new_text = "%s: %s" % (data[index]['commit'], mesgs[index])
            if commit_details.get_text() != new_text:
                commit_details.set_text(new_text)
                commit_line.set_xdata(dates[index])
                fig.canvas.draw_idle()

    fig.canvas.mpl_connect("motion_notify_event", hover)
    plt.show()

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="logLUTs - parse yosys and nextpnr logs to log FPGA resource usage")
    parser.add_argument('--csvfile', action='store', default="LUTs.csv")
    parser.add_argument('--yosys-log', action='store', default="yosys.log")
    parser.add_argument('--nextpnr-log', action='store', default="nextpnr.log")
    parser.add_argument('--add-commit', action='store_const', const=True, help="add latest commit to the log")
    parser.add_argument('--git', action='store', default=".git", help="where the git repo is")
    parser.add_argument('--plot', action='store_const', const=True, help="show data in a plot")
    args = parser.parse_args()

    try:
        repo = git.Repo(args.git)
    except git.exc.NoSuchPathError:
        sys.exit("couldn't find git repo")

    if args.add_commit:
        check_logs()
        flops, luts, max_freq = parse_logs()
        commit = repo.commit('master')
        add_to_log(commit, flops, luts, max_freq)
    elif args.plot:
        plot(load_csv()) 
    else:
        print("nothing to do")
