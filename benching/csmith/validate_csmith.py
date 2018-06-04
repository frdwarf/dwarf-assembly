#!/usr/bin/env python3

""" Checks whether a Csmith-generated file is complicated enough

This does not parse C code, but performs only string lookups. In particular, it
assumes functions are named `func_[0-9]+` or `main`, and that a function
implementation is of the form (whitespaces meaningful)

(static)? RETURN_TYPE func_[0-9]+(.*)
{
    ...
}
"""

import sys
import re


def build_graph(prog):
    func_declare_re = re.compile(r'(?:static )?\S.* (func_\d+|main) ?\(.*\)$')
    func_call_re = re.compile(r'func_\d+')

    graph = {}
    cur_function = None

    for line in prog:
        func_declare_groups = func_declare_re.match(line)
        if func_declare_groups:
            func_name = func_declare_groups.group(1)
            cur_function = func_name
            graph[func_name] = []

        elif line == '}':
            cur_function = None

        else:
            if cur_function is None:
                continue  # Not interresting outside of functions

            last_find_pos = 0
            call_match = func_call_re.search(line, pos=last_find_pos)

            while call_match is not None:
                graph[cur_function].append(call_match.group(0))
                last_find_pos = call_match.end()
                call_match = func_call_re.search(line, pos=last_find_pos)

    reachable = set()
    def mark_reachable(node):
        nonlocal reachable, graph
        if node in reachable:
            return
        reachable.add(node)

        for child in graph[node]:
            mark_reachable(child)
    mark_reachable('main')

    delete = []
    for node in graph:
        if node not in reachable:
            delete.append(node)
    for node in delete:
        graph.pop(node)

    return graph


def get_depth(graph):
    entry_point = 'main'

    depth_of = {}
    def find_depth(node):
        nonlocal depth_of

        if node in depth_of:
            return depth_of[node]

        callees = graph[node]
        if callees:
            depth = max(map(find_depth, callees)) + 1
        else:
            depth = 1
        depth_of[node] = depth
        return depth

    return find_depth(entry_point)


def get_prog_lines():
    def do_read(handle):
        return handle.readlines()

    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r') as handle:
            return do_read(handle)
    else:
        return do_read(sys.stdin)


def main():
    prog = get_prog_lines()
    graph = build_graph(prog)

    if len(graph) < 5 or get_depth(graph) < 5:
        print("Graph is too simple.", file=sys.stderr)
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    main()
