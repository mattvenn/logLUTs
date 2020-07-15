#!/usr/bin/env python3
import git
import re
import csv
import os
import argparse
import sys

regex = {
    'ice40' : {
        "flops" : "SB_DFF[ESR]*[ ]+(\d+)",
        "luts"  : "SB_LUT4[ ]+(\d+)",
        "freq"  : "Info: Max frequency.*?(\d+.\d+) MHz",
        },
    'ecp5'  : {
        "flops" : "TRELLIS_FF[ ]+(\d+)",
        "luts"  : "LUT4[ ]+(\d+)",
        "freq"  : "Info: Max frequency.*?(\d+.\d+) MHz",
        },
    }

def get_latest_stats():
    if not os.path.isfile(args.yosys_log):
        sys.exit("couldn't find yosys log %s" % args.yosys_log)
    if not os.path.isfile(args.nextpnr_log):
        sys.exit("couldn't find nextpnr log %s" % args.nextpnr_log)

    flops = 0
    luts = 0
    max_freq = 0
    print("target is %s" % args.target)

    with open(args.yosys_log) as fh:
        for line in fh.readlines():
            m = re.search(regex[args.target]['flops'], line)
            if m is not None:
                flops += int(m.group(1))
            m = re.search(regex[args.target]['luts'], line)
            if m is not None:
                luts += int(m.group(1))

    with open(args.nextpnr_log) as fh:
        for line in fh.readlines():
            m = re.search(regex[args.target]['freq'], line)
            if m is not None:
                max_freq = float(m.group(1))

    print("flops %d" % flops)
    print("luts %d" % luts)
    print("max freq %2.2f MHz" % max_freq)

    sha = repo.commit(repo.active_branch).hexsha
    short_sha = repo.git.rev_parse(sha, short=True)

    return {    'commit'    : short_sha,
                'flops'     : flops,
                'luts'      : luts,
                'freq'      : max_freq }

def add_to_log(row):
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

        writer.writerow(row)

def load_history():
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
    mesgs =  [repo.commit(d['commit']).message.strip() for d in data]
    flops = [int(d['flops'])  for d in data]
    luts  =  [int(d['luts'])   for d in data]
    freqs =  [float(d['freq']) for d in data]

    ax.grid()
    ax.plot(dates, flops, label='flops', marker='o')
    ax.plot(dates, luts,  label='luts', marker='o')
    ax.set_ylabel('count')
    ax_legend = ax.legend()
    ax_legend.remove()
    ax.set_title("flip-flops, LUTs and max frequency vs commits")

    ax2 = ax.twinx()
    freq_line, = ax2.plot(dates, freqs,  label='freq', color='green', marker='o')
    ax2.set_ylabel('MHz')
    ax2.legend()
    ax2.add_artist(ax_legend) # mess about to get the first ax legend on top of 2nd ax line

    commit_line = plt.axvline(dates[0], linewidth=2, color="gray", linestyle="--" )

    plt.gcf().autofmt_xdate()
    commit_details = fig.text(.5, .02, "hover over points to see commit info", ha='center')
    
    def hover(event):
        if event.inaxes == ax2:
            for i, d in enumerate(dates):
                if(matplotlib.dates.num2date(event.xdata) < d):
                    break
            new_text = "%s: %s\nflops %4d LUTs %4d freq %3d" % (data[i]['commit'], mesgs[i], flops[i], luts[i], freqs[i])
            if commit_details.get_text() != new_text:
                commit_details.set_text(new_text)
                commit_line.set_xdata(dates[i])
                fig.canvas.draw_idle()

    fig.canvas.mpl_connect("motion_notify_event", hover)
    fig.subplots_adjust(bottom=0.25) # bit of space at the bottom for the hover text
    plt.show()


if __name__ == '__main__':

    targets = ['ice40', 'ecp5']
    parser = argparse.ArgumentParser(description="logLUTs - parse yosys and nextpnr logs to log FPGA resource usage")
    parser.add_argument('--csvfile', action='store', default="LUTs.csv")
    parser.add_argument('--yosys-log', action='store', default="yosys.log")
    parser.add_argument('--nextpnr-log', action='store', default="nextpnr.log")
    parser.add_argument('--add-commit', action='store_const', const=True, help="add latest commit to the log")
    parser.add_argument('--git', action='store', default=".git", help="where the git repo is")
    parser.add_argument('--plot', action='store_const', const=True, help="show data in a plot")
    parser.add_argument('--target', choices=targets, default=targets[0], help="what type FPGA")
    args = parser.parse_args()

    try:
        repo = git.Repo(args.git)
    except git.exc.NoSuchPathError:
        sys.exit("couldn't find git repo")

    if args.add_commit:
        add_to_log(get_latest_stats())
    elif args.plot:
        plot(load_history() + [get_latest_stats()]) 
    else:
        print("nothing to do")
