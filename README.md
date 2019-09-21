# log FPGA resource usage to CSV file

1. add -l switches to log output to files for yosys and nextpnr in your Makefile
2. add a post-commit hook to your git repo like this:


    vi post-commit # edit the hook to fit your repo
    cp post-commit .git/hooks/post-commit


3. now everytime you commit, the resource usage will be added to the log file

![luts](luts.png)
