# log FPGA resource usage to CSV file

1. add -l switches to log output to files for yosys and nextpnr in your Makefile
1. add a post-commit hook to your git repo like this:
    1. vi post-commit # edit the hook to fit your repo
    1. cp post-commit .git/hooks/post-commit
1. now everytime you commit, the resource usage will be added to the log file

![luts](luts.png)
