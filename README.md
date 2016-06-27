logmerge
--------

merge multiple log files chronologically

features:
- can detect file timestamp format
- can merge files with different timestamp formats
- recognizes multiline entries (i.e. stack traces)
- can add filename to output
- can add line number to output

limitations:
- file contents must be sorted chronologically
- cannot open compressed files
