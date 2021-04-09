from dsv import dsv_reader, dsv_generator
from sys import stdout, stderr, stdin
r=dsv_reader(stdin, delimiter=',')
c=list(r)[1:]
source_fields = 'name,last_name,nick,email,cad_id,has_hs_keys,has_gate_keys,groups,membership_declaration,entry_date'.split(',')
pm = []
for h in c:
    ph=[]
    group_vals=False
    for v in h:
        if group_vals:
            if v.endswith('"'):
                group_vals = False
            ph[-1].append(v[:-1])
        elif v.startswith('"'):
            group_vals = True
            ph.append([v[1:], ])
        else:
            ph.append(v)
    pm.append(ph)
from data_structures import Hacker
pm = filter(lambda m: m[source_fields.index('membership_declaration')].strip()!='nie', pm)
hackers=[]
for m in pm:
    kwargs=dict()
    for f in Hacker.fields:
        try:
            kwargs[f] = m[source_fields.index(f)]
        except (ValueError, IndexError):
            kwargs[f] = None
        if f == 'groups' and isinstance(kwargs[f], str):
            kwargs[f] = [kwargs[f], ]
    hackers.append(Hacker(**kwargs))
    if hackers[-1].entry_date == None:
        stderr.write(f"missing entry date for \"{hackers[-1].as_dsv()}\"\n")

stdout.writelines(dsv_generator(hackers))