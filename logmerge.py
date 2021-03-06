#!/usr/bin/python

import argparse
import sys
import re
import datetime


def parse_args(args):
    parser = argparse.ArgumentParser(
            description='logmerge - merge multiple log files chronologically',
            argument_default=argparse.SUPPRESS)

    parser.add_argument('files', nargs='*', help='files to merge', default=[])
    parser.add_argument('-v', '--verbose', help='increase verbosity', action='count')
    parser.add_argument('-f', '--print_filename', type=int, help='print filename (printout length)')
    parser.add_argument('-l', '--print_linenum', help='print line number', action='store_true', default=False)

    opts = parser.parse_args(args)

    if len(opts.files) < 2:
        parser.error('Need at least two files to merge')

    return opts


class LogFile:

    class DateReader:
        def __init__(self):
            self.func = None

        def get(self, line):
            if not self.func:
                self.func = self._get_dateformat(line)

            if self.func:
                try:
                    return self.func(line)
                except ValueError:
                    return None

            return None


        def _get_dateformat(self, line):
            if not line:
                return None

            days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            if line[1:4] in days:
                def _apache(line):
                    return datetime.datetime.strptime(line[5:32], '%b %d %H:%M:%S.%f %Y')
                return _apache

            match = re.match(r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}.[0-9]{2}:[0-9]{2}', line[1:26])
            if match:
                def _chefclient(line):
                    return datetime.datetime.strptime(line[:20], '[%Y-%m-%dT%H:%M:%S')
                return _chefclient

            months = ['Jan', 'Feb', 'Mar', 'Apr', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            if line[:3] in months:
                def _pacemaker(line):
                    dt = datetime.datetime.strptime(line[:15], '%b %d %H:%M:%S')
                    return dt.replace(year=datetime.date.today().year)
                return _pacemaker

            match = re.match(r'[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}', line)
            if match:
                def _nova(line):
                    return datetime.datetime.strptime(line[:23], '%Y-%m-%d %H:%M:%S.%f')
                return _nova

            match = re.match(r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}Z', line)
            if match:
                def _ovs(line):
                    return datetime.datetime.strptime(line[:23], '%Y-%m-%dT%H:%M:%S.%f')
                return _ovs

            match = re.match(r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}\+[0-9]{2}:[0-9]{2}', line)
            if match:
                def _messages(line):
                    return datetime.datetime.strptime(line[:26], '%Y-%m-%dT%H:%M:%S.%f')
                return _messages

            match = re.match(r'[ID], \[[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}', line)
            if match:
                def _crowbar_production(line):
                    return datetime.datetime.strptime(line[4:30], '%Y-%m-%dT%H:%M:%S.%f')
                return _crowbar_production

            match = re.match(r'[[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2} .[0-9]{4}', line)
            if match:
                def _crowbar_join(line):
                    return datetime.datetime.strptime(line[:19], '%Y-%m-%d %H:%M:%S')
                return _crowbar_join

            match = re.match(r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}.[0-9]{2}:[0-9]{2}', line)
            if match:
                def _node(line):
                    return datetime.datetime.strptime(line[:19], '%Y-%m-%dT%H:%M:%S')
                return _node

            match = re.match(r'#(1?[0-9]{9})', line)
            if match:
                def _bash_history(line):
                    return datetime.datetime.utcfromtimestamp(int(match.group(1)))
                return _bash_history

            return None



    def __init__(self, file):
        self.file = file
        self.datetime = datetime.datetime.min
        self.line = ''
        self.linenum = 0
        self.dateread = self.DateReader()

    def update(self):
        self.line = ''
        while True:
            tmpline = self.file.readline()
            if not tmpline or tmpline == '\n':
                break

            self.line += tmpline

            tmpdatetime = self.dateread.get(tmpline)
            if tmpdatetime is not None:
                self.datetime = tmpdatetime
                self.linenum += 1
                break
            else:
                #print "Found unknown date format in: {}:{}".format(self.file.name, self.linenum)
                break


    def output(self, filename_length, print_linenum=False):
        outstr = ''
        if filename_length > 0:
            filename = self.file.name.rsplit('/', 1)[-1] + " "
            if len(filename) > filename_length:
                filename = filename[:(filename_length - 1)] + '+'
            outstr += "{:<{}} ".format(filename, filename_length)

        if print_linenum and self.line:
            outstr += "{} ".format(self.linenum)

        outstr += self.line.rstrip()
        print outstr

        self.update()

    def has_lines(self):
        return self.line


def main():
    opts = parse_args(sys.argv[1:])

    files = []
    for filename in opts.files:
        file = LogFile(open(filename, 'r'))
        file.update()
        files.append(file)

    while files:
        files = sorted(files, key=lambda logfile: logfile.datetime)
        filename_length = 0
        if 'print_filename' in opts:
            filename_length = opts.print_filename

        files[0].output(filename_length, opts.print_linenum)
        if not files[0].has_lines():
            del files[0]


if __name__ == '__main__':
    main()
