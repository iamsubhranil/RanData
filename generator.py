from scanner import Scanner
from my_parser import Parser, ParseError, PrettyPrinter
from engine import Engine
import sys

if __name__ == "__main__":

    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("[Error] Usage : %s <input_file> [<output_file>]" % sys.argv[0])
        sys.exit(1)

    with open("bootstrap.format", "r") as f:
        source = f.read()
        # print(source)
        scanner = Scanner(source)
        parser = Parser(scanner)
        ast = parser.parse_all()
        p = PrettyPrinter()
        e = Engine()
        for a in ast:
            a.accept(e)

        res = []

        with open(sys.argv[1], "r") as g:
            source = g.read()
            scanner = Scanner(source)
            parser = Parser(scanner)
            for a in parser.parse_all():
                r = a.accept(e)
                if r != None:
                    for s in r:
                        res.append(s)

        if len(sys.argv) > 2:
            with open(sys.argv[2], "w") as h:
                for line in res:
                    h.write(str(line) + "\n")
        else:
            for line in res:
                print(line)
