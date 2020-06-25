from scanner import Scanner, ScanError
from my_parser import Parser, ParseError, PrettyPrinter, VisitorError
from engine import Engine, EngineError
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

def try_run(source, engine, store_res=False):
    scanner = Scanner(source)
    res = []
    try:
        parser = Parser(scanner)
        ast = parser.parse_all()
        for a in ast:
            r = a.accept(engine)
            if r != None and store_res:
                res.extend(r)
        return (res, True)
    except ParseError as pe:
        print("[Error] Error occurred while parsing!")
        print(pe)
    except ScanError as se:
        print("[Error] Error occurred while scanning!")
        print(se)
    except EngineError as ee:
        print("[Error] Error occurred while evaluating!")
        print(ee)
    except VisitorError as ve:
        print("[Error] Error in implementation!")
        print(ve)
    return (None, False)


def main():

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

    e = Engine(given.generate, given.process[0])
    bootstrap_loaded = False
    with open("bootstrap.format", "r") as f:
        source = f.read()
        res, bootstrap_loaded = try_run(source, e, False)

    if bootstrap_loaded == False:
        print("[Warn] Loading bootstrap module failed!")
        print("[Warn] One or more default rules may not be available!")

    with open(given.input_file, "r") as g:
        source = g.read()
        scanner = Scanner(source)
        parser = Parser(scanner)
        if given.time:
            start = time.perf_counter()
        res, success = try_run(source, e, given.generate == False)
        if success == False:
            print("[Error] Generation failed!")
            return
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

if __name__ == "__main__":
    main()
