from engine import append, append_times, between, between_times
from engine import one_of, one_of_times, one_of_unique, one_of_unique_times
from engine import lower, lower_times, upto, upto_times
from engine import init_child, NullManager
from contextlib import nullcontext
import random
from string import ascii_letters, digits, punctuation, whitespace
from itertools import repeat
import sys
import time
import platform
import json

finalset = ascii_letters + digits + punctuation
r = random

class bcolors:

    if platform.system() == 'Windows':
        MAGENTA = ''
        OKBLUE = ''
        OKGREEN = ''
        WARNING = ''
        FAIL = ''
        ENDC = ''
        BOLD = ''
        UNDERLINE = ''
        COLORLENGTH = 0
    else:
        MAGENTA = '\033[95m'
        OKBLUE = '\033[94m'
        OKGREEN = '\033[92m'
        WARNING = '\033[93m'
        FAIL = '\033[91m'
        ENDC = '\033[0m'
        BOLD = '\033[1m'
        UNDERLINE = '\033[4m'
        COLORLENGTH = len(MAGENTA + ENDC)

def bold(t):
    return bcolors.BOLD + t + bcolors.ENDC

def magenta(t):
    return bcolors.MAGENTA + t + bcolors.ENDC

def blue(t):
    return bcolors.OKBLUE + t + bcolors.ENDC

def red(t):
    return bcolors.FAIL + t + bcolors.ENDC

def green(t):
    return bcolors.OKGREEN + t + bcolors.ENDC

def yellow(t):
    return bcolors.WARNING + t + bcolors.ENDC

def generate_random_string_list(r, finalset, wordlength=100, numwords=100):
    return [''.join(r.choices(finalset, k=wordlength)) for _ in range(numwords)]

def test_append(times,  numlists=100):
    for _ in range(times):
        s = [generate_random_string_list(r, finalset) for _ in range(numlists)]
        elapsed = time.perf_counter()
        reslist = append(s, r)[0] # select only the result
        elapsed = time.perf_counter() - elapsed
        if len(reslist) != len(s):
            errstr = "Expected length %d, received %d" % (len(s), len(reslist))
            yield (False, errstr)
        else:
            success = True
            errstr = ''
            for (origlist, res) in zip(s, reslist):
                if ''.join(origlist) != res:
                    errstr = "String not matched!"
                    success = False
                    break
            yield (success, errstr, elapsed)

def test_append_times(times, numlists=100):
    for _ in range(times):
        s = generate_random_string_list(r, finalset)
        result = ''.join(s)
        elapsed = time.perf_counter()
        reslist = append_times([s], (numlists, r))[0]
        elapsed = time.perf_counter() - elapsed
        success = True
        errstr = ''
        while numlists > 0:
            try:
                x = next(reslist)
                if x != result:
                    errstr = "Unexpected result!"
                    success = False
                    break
                numlists -= 1
            except StopIteration:
                errstr = "Unexpected end of list!"
                success = False
                break
        yield (success, errstr, elapsed)


def test_between(times, numlists=100):
    for _ in range(times):
        ranges = [(random.randint(100, 500), random.randint(500, 1000)) for _ in range(numlists)]
        elapsed = time.perf_counter()
        res = between(ranges, r)[0]
        elapsed = time.perf_counter() - elapsed
        if len(ranges) != len(res):
            errstr = "Unexpected length!"
            yield (False, errstr)
        else:
            together = zip(ranges, res)
            success = True
            errstr = ''
            for x in together:
                if x[1] not in range(x[0][0], x[0][1] + 1):
                    errstr = "%d is not between(%d, %d)!" % (int(x[1]), int(x[0][0]), int(x[0][1]))
                    success = False
                    break
            yield (success, errstr, elapsed)

def test_between_times(times, numlists=100):
    for _ in range(times):
        down = random.randint(100, 500)
        up = random.randint(500, 1000)
        ranges = (down, up)
        elapsed = time.perf_counter()
        res = between_times(ranges, (numlists, r))[0]
        elapsed = time.perf_counter() - elapsed
        if len(res) != numlists:
            errstr = "Unexpected length!"
            yield (False, errstr)
        else:
            for x in res:
                success = True
                errstr = ''
                if x not in range(down, up + 1):
                    errstr = "%d is not between(%d, %d)" % (x, down, up)
                    success = False
                    break
            yield (success, errstr, elapsed)

def test_one_of(times, numlist=100):
    for _ in range(times):
        sources = [generate_random_string_list(r, finalset) for _ in range(numlist)]
        elapsed = time.perf_counter()
        of = one_of(sources, r)[0]
        elapsed = time.perf_counter() - elapsed
        if len(of) != numlist:
            errstr = "Unexpected length!"
            yield (False, errstr)
        else:
            final = zip(sources, of)
            success = True
            errstr = ''
            for (x, y) in final:
                if y not in x:
                    errstr = "'%s' is not in the list!" % y
                    success = False
                    break
            yield (success, errstr, elapsed)

def test_one_of_times(times, numlist=100):
    for _ in range(times):
        sources = generate_random_string_list(r, finalset)
        elapsed = time.perf_counter()
        res = one_of_times(sources, (numlist, r))[0]
        elapsed = time.perf_counter() - elapsed
        if len(res) != numlist:
            errstr = "Unexpected length!"
            yield (False, errstr)
        else:
            success = True
            errstr = ''
            for x in res:
                if x not in sources:
                    errstr = "Error in one_of_times: '%s' is not in the list!" % x
                    success = False
                    break
            yield (success, errstr, elapsed)

def test_one_of_unique(times, numlist=100):
    init_child({}, nullcontext())
    for j in range(times):
        numitems = 100
        namelist = ["dict_test_one_of_unqiue_%d_%d" % (j,i) for i in range(numlist)]
        sources = [generate_random_string_list(r, finalset, numwords=numitems) for _ in range(numlist)]
        maxitems = max([len(set(l)) for l in sources])
        res = []
        elapsed = time.perf_counter()
        for _ in range(maxitems):
            res.append(one_of_unique(sources, r, namelist)[0])
        elapsed = time.perf_counter() - elapsed
        if len(res) != maxitems:
            errstr = "Unexpected length!"
            yield (False, errstr)
        else:
            finalres = zip(*res)
            col = iter(sources)
            success = True
            errstr = ''
            for one in finalres:
                lib = next(col)
                if len(set(one)) != len(one):
                    errstr = "Picked up duplicate items!"
                    success = False
                    break
                else:
                    for o in one:
                        bak = lib
                        if o not in bak:
                            errstr = "Chosen item is not in original set!"
                            success = False
                            break
                    if not success:
                        break
            yield (success, errstr, elapsed)

def test_one_of_unique_times(times, numlist=100):
    init_child({}, nullcontext())
    for j in range(times):
        sources = generate_random_string_list(r, finalset)
        unqitems = set(sources)
        callfor = len(unqitems)
        elapsed = time.perf_counter()
        res = one_of_unique_times(sources, (callfor, r), "dict_test_one_of_unqiue_times%d" % j)[0]
        elapsed = time.perf_counter() - elapsed
        ret = set(res)
        if len(unqitems - ret) > 0:
            errstr = "Not all unique items got picked up!"
            yield (False, errstr)
        else:
            yield (True, '', elapsed)

def test_upto(times, numlist=100):
    for _ in range(times):
        uptolist = [random.randint(100, 500) for _ in range(numlist)]
        elapsed = time.perf_counter()
        res = upto(uptolist, r)[0]
        elapsed = time.perf_counter() - elapsed
        if len(res) != numlist:
            errstr = "Unexpected length!"
            yield (False, errstr)
        else:
            final = zip(res, uptolist)
            success = True
            errstr = ''
            for x in final:
                if x[0] not in range(x[1] + 1):
                    errstr = '%d is not in range upto %d' % (x[0], x[1])
                    success = False
                    break
            yield (success, errstr, elapsed)

def test_upto_times(times, numlist=100):
    for _ in range(times):
        upt = [random.randint(100, 500)]
        elapsed = time.perf_counter()
        res = upto_times(upt, (numlist, r))[0]
        elapsed = time.perf_counter() - elapsed
        if len(res) != numlist:
            yield (False, "Unexpected length!")
        else:
            success = True
            errstr = ''
            for x in res:
                if x not in range(upt[0] + 1):
                    errstr = '%d is not in range upto %d' % (x, upt[0])
                    success = False
                    break
            yield (success, errstr, elapsed)


def test_lower(times, numlist=100):
    for _ in range(times):
        strlist = zip(generate_random_string_list(r, finalset, numwords=numlist))
        elapsed = time.perf_counter()
        res = lower(strlist, r)[0]
        elapsed = time.perf_counter() - elapsed
        if len(res) != numlist:
            yield (False, "Unexpected length!")
        else:
            final = zip(res, strlist)
            success = True
            errstr = ''
            for x in final:
                if x[0] != x[1].lower():
                    errstr = "Not lowered successfully!"
                    success = False
                    break
            yield (success, errstr, elapsed)

def test_lower_times(times, numlists=100):
    for _ in range(times):
        strlist = generate_random_string_list(r, finalset, numwords=1)[0]
        elapsed = time.perf_counter()
        res = lower_times([strlist], (numlists, r))[0]
        elapsed = time.perf_counter() - elapsed
        success = True
        errstr = ''
        result = strlist.lower()
        while numlists > 0:
            try:
                x = next(res)
                if x != result:
                    errstr = "Unexpected result!"
                    success = False
                    break
                numlists -= 1
            except StopIteration:
                errstr = "Unexpected end of list!"
                success = False
                break
        yield (success, errstr, elapsed)

def load_previous_result():
    fname = "randata." + platform.system() + "_bench"
    res = {}
    try:
        with open(fname, "r") as prev_res:
            res = json.load(prev_res)
    except:
        pass
    return res

def store_current_result(old, new, numlists):
    old[str(numlists)] = new
    fname = "randata." + platform.system() + "_bench"
    with open(fname, "w") as new_res:
        json.dump(old, new_res)

def test_all(total=100, numlists=100):
    tests = {"append": test_append, "append_times": test_append_times,
             "between": test_between, "between_times": test_between_times,
             "one_of": test_one_of, "one_of_times": test_one_of_times,
             "one_of_unique": test_one_of_unique, "one_of_unique_times": test_one_of_unique_times,
             "upto": test_upto, "upto_times": test_upto_times,
             "lower": test_lower, "lower_times": test_lower_times}
    comparison = load_previous_result()
    oldres = {}
    if str(numlists) in comparison:
        oldres = comparison[str(numlists)]
    newres = {}
    l = max([len(s) for s in tests.keys()])
    donestr = "Done (of %d)" % total
    donestrlen = len(donestr)
    topstring = "No.    {:^{width}}    ".format("Test", width=l) + donestr + "    Passed    Failed    Avg Time"
    print(topstring)
    print(''.join(['=']*len(topstring)))

    count = 1
    for k in tests:
        oldavg = 0.0
        if k in oldres:
            oldavg = oldres[k]
        print("{:^3d}    ".format(count) + bold("{:^{width}}").format(k, width=l) + "    ", end='')
        stat = blue("{:^{width}}") + "    " + green("{:^6d}") + "    " + red("{:^6d}") + "    " + magenta("{:^2.6f}s")
        if oldavg > 0.0:
            stat += "({:^7.2f}%)"
        first = stat.format(0, 0, 0, 0.0, 99.99, width=donestrlen)
        size = len(first) - (bcolors.COLORLENGTH * 4) # color sequences appear as separate characters,
                                    # but is interpreted as a no-length control sequence
        bk = ''.join(['\b']*size)
        print(first, end='')
        sys.stdout.flush()
        passed = 0
        failed = 0
        i = 0
        messages = {}
        avgtime = 0.0
        totaltime = 0.0
        percen = 0.0
        for res in tests[k](total, numlists):
            if res[0]:
                passed += 1
                totaltime += res[2]
                avgtime = totaltime / passed
                newres[k] = avgtime
                if oldavg > 0.0:
                    percen = ((oldavg - avgtime)*100/oldavg)
            else:
                failed += 1
                messages[i] = res[1]
            i += 1
            print(bk + stat.format(i, passed, failed, avgtime, percen, width=donestrlen), end='')
            sys.stdout.flush()
        count = count + 1
        if len(messages) > 0:
            for k in messages:
                print("\n" + red("[Fail]") + " #%d : %s" % (k+1, messages[k]), end='')
        print("")

    if len(oldres) == 0:
        store_current_result(comparison, newres, numlists)
