from elftools.dwarf import callframe
import gather_stats
import itertools
import functools

REGS_IDS = {
    'RAX': 0,
    'RDX': 1,
    'RCX': 2,
    'RBX': 3,
    'RSI': 4,
    'RDI': 5,
    'RBP': 6,
    'RSP': 7,
    'R8':  8,
    'R9':  9,
    'R10': 10,
    'R11': 11,
    'R12': 12,
    'R13': 13,
    'R14': 14,
    'R15': 15,
    'RIP': 16
}

ID_TO_REG = [
    'RAX',
    'RDX',
    'RCX',
    'RBX',
    'RSI',
    'RDI',
    'RBP',
    'RSP',
    'R8',
    'R9',
    'R10',
    'R11',
    'R12',
    'R13',
    'R14',
    'R15',
    'RIP',
]

HANDLED_REGS = list(map(lambda x: REGS_IDS[x], [
    'RIP',
    'RSP',
    'RBP',
    'RBX',
]))

ONLY_HANDLED_REGS = True  # only analyzed handled regs columns

PLT_EXPR = [119, 8, 128, 0, 63, 26, 59, 42, 51, 36, 34]  # Handled exp


def accumulate_regs(reg_list):
    out = [0] * 17
    for lst in reg_list:
        for pos in range(len(lst)):
            out[pos] += lst[pos]

    return out


def filter_none(lst):
    for x in lst:
        if x:
            yield x


def deco_filter_none(fct):
    def wrap(lst):
        return fct(filter_none(lst))
    return wrap


class FdeProcessor:
    def __init__(self, fct, reducer=None):
        self._fct = fct
        self._reducer = reducer

    def __call__(self, path, elftype, cfi):
        out = []
        for entry in cfi:
            if isinstance(entry, callframe.FDE):
                decoded = entry.get_decoded()
                out.append(self._fct(path, entry, decoded))
        if self._reducer is not None and len(out) >= 2:
            out = [self._reducer(out)]
        return out


class FdeProcessorReduced:
    def __init__(self, reducer):
        self._reducer = reducer

    def __call__(self, fct):
        return FdeProcessor(fct, self._reducer)


def fde_processor(fct):
    return FdeProcessor(fct)


def fde_processor_reduced(reducer):
    return FdeProcessorReduced(reducer)


def is_handled_expr(expr):
    if expr == PLT_EXPR:
        return True

    if len(expr) == 2 and 0x70 <= expr[0] <= 0x89:
        if expr[0] - 0x70 in HANDLED_REGS:
            return True
    return False


# @fde_processor
def find_non_cfa(path, fde, decoded):
    regs_seen = 0
    non_handled_regs = 0
    non_handled_exp = 0
    cfa_dat = [0, 0]  # Seen, expr
    rule_type = {
        callframe.RegisterRule.UNDEFINED: 0,
        callframe.RegisterRule.SAME_VALUE: 0,
        callframe.RegisterRule.OFFSET: 0,
        callframe.RegisterRule.VAL_OFFSET: 0,
        callframe.RegisterRule.REGISTER: 0,
        callframe.RegisterRule.EXPRESSION: 0,
        callframe.RegisterRule.VAL_EXPRESSION: 0,
        callframe.RegisterRule.ARCHITECTURAL: 0,
    }
    problematic_paths = set()

    for row in decoded.table:
        for entry in row:
            reg_def = row[entry]

            if entry == 'cfa':
                cfa_dat[0] += 1
                if reg_def.expr:
                    cfa_dat[1] += 1
                    if not is_handled_expr(reg_def.expr):
                        non_handled_exp += 1
                        problematic_paths.add(path)
                elif reg_def:
                    if reg_def.reg not in HANDLED_REGS:
                        non_handled_regs += 1
                        problematic_paths.add(path)
            if not isinstance(entry, int):  # CFA or PC
                continue

            if ONLY_HANDLED_REGS and entry not in HANDLED_REGS:
                continue

            rule_type[reg_def.type] += 1
            reg_rule = reg_def.type

            if reg_rule in [callframe.RegisterRule.OFFSET,
                            callframe.RegisterRule.VAL_OFFSET]:
                regs_seen += 1  # CFA
            elif reg_rule == callframe.RegisterRule.REGISTER:
                regs_seen += 1
                if reg_def.arg not in HANDLED_REGS:
                    problematic_paths.add(path)
                    non_handled_regs += 1
            elif reg_rule in [callframe.RegisterRule.EXPRESSION,
                              callframe.RegisterRule.VAL_EXPRESSION]:
                expr = reg_def.arg
                if not is_handled_expr(reg_def.arg):
                    problematic_paths.add(path)
                    with open('/tmp/exprs', 'a') as handle:
                        handle.write('[{} - {}] {}\n'.format(
                            path, fde.offset,
                            ', '.join(map(lambda x: hex(x), expr))))
                    non_handled_exp += 1

    return (regs_seen, non_handled_regs, non_handled_exp, rule_type, cfa_dat,
            problematic_paths)


def reduce_non_cfa(lst):
    def merge_dict(d1, d2):
        for x in d1:
            d1[x] += d2[x]
        return d1

    def merge_list(l1, l2):
        out = []
        for pos in range(len(l1)):  # Implicit assumption len(l1) == len(l2)
            out.append(l1[pos] + l2[pos])
        return out

    def merge_elts(accu, elt):
        accu_regs, accu_nh, accu_exp, accu_rt, accu_cfa, accu_paths = accu
        elt_regs, elt_nh, elt_exp, elt_rt, elt_cfa, elf_paths = elt
        return (
            accu_regs + elt_regs,
            accu_nh + elt_nh,
            accu_exp + elt_exp,
            merge_dict(accu_rt, elt_rt),
            merge_list(accu_cfa, elt_cfa),
            accu_paths.union(elf_paths),
        )

    return functools.reduce(merge_elts, lst)


@deco_filter_none
def flatten_non_cfa(result):
    flat = itertools.chain.from_iterable(result)
    out = reduce_non_cfa(flat)
    out_cfa = {
        'seen': out[4][0],
        'expr': out[4][1],
        'offset': out[4][0] - out[4][1],
    }
    out = (out[0],
           (out[1], out[0] + out_cfa['offset']),
           (out[2], out[3]['EXPRESSION'] + out_cfa['expr']),
           out[3],
           out_cfa,
           out[5])
    return out
