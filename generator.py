from scanner import Scanner
from my_parser import Parser, ParseError, PrettyPrinter
from engine import Engine
import sys
import argparse
import time


def check_positive_generator(string):
    def check_positive(value):
        try:
            ivalue = int(value)
            if ivalue <= 0:
                raise argparse.ArgumentTypeError(
                    "%s should be positive!" % string)
            return ivalue
        except ValueError:
            raise argparse.ArgumentTypeError(
                "%s should be integer!" % string)
    return check_positive


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    testgroup = parser.add_mutually_exclusive_group(required=True)
    muexgroup = parser.add_mutually_exclusive_group()

    testgroup.add_argument('input_file', nargs='?',
                           help="input file to read the format from")
    muexgroup.add_argument('output_file', nargs='?',
                           help="file to save generated data (default is stdout)")
    muexgroup.add_argument('-g', '--generate', action='store_true', required=False,
                           help="generate, but don't write the generated data")
    parser.add_argument('-p', '--process', default=[-1], nargs=1, required=False,
                        type=check_positive_generator("Number of processes"),
                        help='use P processes to generate the data', metavar='P')
    parser.add_argument('-t', '--time', action='store_true', required=False,
                        help="measure the time taken to generate the data")
    testgroup.add_argument('-c', '--check', default=[], nargs=2, required=False,
                           type=check_positive_generator(
                               "Both of number of tests and lists"),
                           help="perform T tests on core methods with N lists in each test",
                           metavar=('T', 'N'))
    given = parser.parse_args()

    if len(given.check) > 0:
        import tester
        tester.test_all(given.check[0], given.check[1])
        sys.exit(0)

    with open("bootstrap.format", "r") as f:
        source = f.read()
        scanner = Scanner(source)
        parser = Parser(scanner)
        ast = parser.parse_all()
        p = PrettyPrinter()
        e = Engine(given.generate, given.process[0])
        for a in ast:
            a.accept(e)

        res = []

        with open(given.input_file, "r") as g:
            source = g.read()
            scanner = Scanner(source)
            parser = Parser(scanner)
            if given.time:
                start = time.perf_counter()
            for a in parser.parse_all():
                r = a.accept(e)
                if r != None and given.generate == False:
                    for s in r:
                        res.append(s)
            if given.time:
                print("Time elapsed: %0.5f" %
                      (time.perf_counter() - start) + "s")

            if given.generate == False:
                if given.output_file != None:
                    with open(given.output_file, "w") as h:
                        for line in res:
                            h.write(str(line) + "\n")
                else:
                    for line in res:
                        print(line)
