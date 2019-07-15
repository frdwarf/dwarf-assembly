#!/usr/bin/env python3

import sys
import re


class Match:
    def __init__(self, re_str, negate=False):
        self.re = re.compile(re_str)
        self.negate = negate

    def matches(self, line):
        return self.re.search(line) is not None


class Matcher:
    def __init__(self, match_objs):
        self.match_objs = match_objs
        self.match_pos = 0
        self.matches = 0

        if not self.match_objs:
            raise Exception("No match expressions provided")
        if self.match_objs[-1].negate:
            raise Exception("The last match object must be a positive expression")

    def feed(self, line):
        for cur_pos, exp in enumerate(self.match_objs[self.match_pos :]):
            cur_pos = cur_pos + self.match_pos
            if not exp.negate:  # Stops the for here, whether matching or not
                if exp.matches(line):
                    self.match_pos = cur_pos + 1
                    print(
                        "Passing positive {}, advance to {}".format(
                            cur_pos, self.match_pos
                        )
                    )
                    if self.match_pos >= len(self.match_objs):
                        print("> Complete match, reset.")
                        self.matches += 1
                        self.match_pos = 0
                return
            else:
                if exp.matches(line):
                    print("Failing negative [{}] {}, reset".format(exp.negate, cur_pos))
                    old_match_pos = self.match_pos
                    self.match_pos = 0
                    if old_match_pos != 0:
                        print("> Refeed: ", end="")
                        self.feed(line)
                    return


def get_args(args):
    out_args = []
    for arg in args:
        negate = False
        if arg[0] == "~":
            negate = True
            arg = arg[1:]
        out_args.append(Match(arg, negate))
    return out_args


if __name__ == "__main__":
    matcher = Matcher(get_args(sys.argv[1:]))
    for line in sys.stdin:
        matcher.feed(line)
    print(matcher.matches)
