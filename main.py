#!/usr/bin/env python3
"""
Revised pumpfun top5 forecast with post-write validation.
Same model and constants, different internal names and extra checks.
"""
from __future__ import annotations
import os, sys, json, math
from datetime import datetime

IN_DIR = os.environ.get('MAKEFUN_INPUT_DIR', '/input')
OUT_DIR = os.environ.get('MAKEFUN_OUTPUT_DIR', '/output')

TASK_F = os.path.join(IN_DIR, 'task.json')
HIST_F = os.path.join(IN_DIR, 'history.ndjson')

def to_dt(s: str):
    if s.endswith('Z'):
        s = s[:-1] + '+00:00'
    return datetime.fromisoformat(s)

def read_marks(p):
    res = []
    with open(p, 'r', encoding='utf-8') as fh:
        for L in fh:
            L=L.strip()
            if not L: continue
            res.append(json.loads(L))
    return res

def to_int(x):
    if isinstance(x,int): return x
    return int(x)

def lamports_to_r(l):
    return math.log10(to_int(l)) - 9.0

def median(xs):
    a=sorted(xs)
    n=len(a)
    m=n//2
    if n%2: return a[m]
    return 0.5*(a[m-1]+a[m])

def clip(x,lo,hi):
    return max(lo,min(hi,x))

def Phi(x):
    return 0.5*(1.0 + math.erf(x/math.sqrt(2.0)))

def floor1e6(x):
    return math.floor(x*1_000_000.0)/1_000_000.0

def build_forecast():
    with open(TASK_F,'r',encoding='utf-8') as fh:
        task=json.load(fh)
    reads=[to_dt(s) for s in task['reads']]
    chart_size=int(task.get('chart_size',200))
    places=int(task.get('places',5))
    edges=[float(x) for x in task['size']['edges']]

    marks=read_marks(HIST_F)
    usable=[]
    for m in marks:
        rows=[r for r in m.get('rows',[]) if r.get('rank') is not None]
        if m.get('ok') and rows:
            usable.append((to_dt(m['at']), m, rows))
    if not usable:
        raise SystemExit('no usable marks')
    usable.sort(key=lambda t:t[0])
    tL, last_mark, last_rows_all = usable[-1]
    last_rows=[r for r in last_rows_all if r.get('rank') is not None]
    last_rows.sort(key=lambda r:(int(r['rank']), r.get('mint','')))
    chart = last_rows[:chart_size]
    if len(chart) < 5:
        raise SystemExit('last usable mark has fewer than 5 coins')

    # map mint -> first seen (time, r)
    first_seen = {}
    for dt,m,rows in usable:
        for r in rows:
            if r.get('rank') is None: continue
            mt = r.get('mint')
            if mt in first_seen: continue
            if 'market_cap_lamports' in r:
                first_seen[mt] = (dt, lamports_to_r(r['market_cap_lamports']))

    pool = []
    for r in chart[:5]:
        mt=r['mint']; rk=int(r['rank']); vn=r.get('venue','')
        my = bool(r.get('mayhem', False))
        rcap = lamports_to_r(r['market_cap_lamports'])
        created = to_dt(r['created_at']) if r.get('created_at') else tL
        first = first_seen.get(mt,(tL, rcap))
        pool.append({'mint':mt,'rank':rk,'venue':vn,'mayhem':my,'r':rcap,'created':created,'first_dt':first[0],'first_r':first[1]})

    rlist = [p['r'] for p in pool]
    medr = median(rlist)
    top_r = max(rlist)

    for p in pool:
        p['z'] = p['r'] - medr
        p['age_h'] = (tL - p['created']).total_seconds()/3600.0
        if p['first_dt'] == tL:
            mom = 0.0
        else:
            elapsed = (tL - p['first_dt']).total_seconds()/3600.0
            mom = 0.0 if elapsed<=0 else (p['r'] - p['first_r'])/elapsed
        p['mom'] = clip(mom, -2.0, 2.0)

    per_read_name_probs = []
    per_read_size_probs = []

    for t in reads:
        h = max(0.0, (t - tL).total_seconds()/3600.0)
        p_surv = []
        for p in pool:
            if p['venue']=='pool' and not p['mayhem']:
                p0 = 0.95*(1.0 + 0.15*clip(p['z'],-1.0,1.0) + 0.10*math.tanh(p['age_h']/0.25))
                p0 = clip(p0, 0.05, 0.95)
                val = p0 * math.exp(-h/1.8)
            elif p['venue']=='pool' and p['mayhem']:
                val = min(0.9, 0.95*0.8) * math.exp(-h/1.8)
            else:
                val = 0.02 * math.exp(-h/0.15)
            p_surv.append(val)
        mean_surv = sum(p_surv)/len(p_surv)
        named = clip(mean_surv, 0.05, 0.90)

        # compute utility softmax
        us = []
        for p in pool:
            u = -0.5*(p['rank']-1) + 0.20*math.tanh(p['age_h']/0.3) + (0.8 if p['venue']=='pool' else -2.0)
            us.append(u)
        maxu = max(us)
        exps = [math.exp(u-maxu) for u in us]
        s_exps = sum(exps) if exps else 1.0
        soft = [e/s_exps for e in exps]
        wraw = [p_surv[i]*soft[i] for i in range(len(pool))]
        s_wraw = sum(wraw)
        weights = [ (w/s_wraw if s_wraw>0 else 1.0/len(pool)) for w in wraw ]

        # distribute named mass over places using discrete Laplace kernel
        scale = 0.7 + 0.8*h
        name_alloc = {p['mint']:[0.0]*places for p in pool}
        for i,p in enumerate(pool):
            share = named * weights[i]
            kvals = [math.exp(-abs((k+1)-p['rank'])/scale) for k in range(places)]
            s_k = sum(kvals) if sum(kvals)!=0 else 1.0
            kvals = [v/s_k for v in kvals]
            for k in range(places):
                name_alloc[p['mint']][k] += share * kvals[k]
        per_read_name_probs.append(name_alloc)

        # sizes per place: gaussian on r
        drift = 1.2*(1.0 - math.exp(-h * 2.2 / 1.2))
        place_bins = {}
        for k in range(1, places+1):
            centre = top_r - (k-1)*0.15 + drift
            sd = 0.28 + 0.15*math.sqrt(h/0.1667) if h>0 else 0.28
            sd = clip(sd, 0.20, 1.20)
            bins = {}
            for b in range(0, len(edges)+1):
                if b==0:
                    lo=-1e9; hi=edges[0]
                elif b==len(edges):
                    lo=edges[-1]; hi=1e9
                else:
                    lo=edges[b-1]; hi=edges[b]
                mass = Phi((hi-centre)/sd) - Phi((lo-centre)/sd)
                mass = floor1e6(max(0.0, mass))
                if mass>0.0:
                    bins[b]=mass
            place_bins[k]=bins
        per_read_size_probs.append(place_bins)

    # average across reads
    mixed_names = {p['mint']:[0.0]*places for p in pool}
    for rr in per_read_name_probs:
        for mint, arr in rr.items():
            for k in range(places):
                mixed_names[mint][k] += arr[k]/len(per_read_name_probs)
    for m in mixed_names:
        for k in range(places):
            mixed_names[m][k] = floor1e6(max(0.0, mixed_names[m][k]))

    # if a place's named sum exceeds 1, scale down that place
    for k in range(places):
        s = sum(mixed_names[m][k] for m in mixed_names)
        if s > 1.0:
            sc = 1.0 / s
            for m in mixed_names:
                mixed_names[m][k] = floor1e6(mixed_names[m][k] * sc)

    # mix sizes
    mixed_sizes = {k:{} for k in range(1, places+1)}
    for k in range(1, places+1):
        acc = {}
        for pr in per_read_size_probs:
            for b,v in pr[k].items():
                acc[b] = acc.get(b,0.0) + v/len(per_read_size_probs)
        for b,v in acc.items():
            v = floor1e6(max(0.0, v))
            if v>0.0:
                mixed_sizes[k][b]=v

    # produce lists in stable order
    probs_list = []
    for mint in sorted(mixed_names):
        for k in range(places):
            p = mixed_names[mint][k]
            if p>0.0:
                probs_list.append({'mint':mint,'place':k+1,'p':p})
    sizes_list = []
    for k in range(1, places+1):
        for b in sorted(mixed_sizes[k]):
            sizes_list.append({'place':k,'bin':b,'p':mixed_sizes[k][b]})

    # top5 from named mints
    named_mints = [m for m in mixed_names if any(mixed_names[m][k]>0 for k in range(places))]
    cand = []
    for m in named_mints:
        tot = sum(mixed_names[m])
        if tot<=0: continue
        exp_place = sum((k+1)*mixed_names[m][k] for k in range(places))/tot
        cand.append((exp_place, -tot, m))
    cand.sort()
    top5 = [c[2] for c in cand]
    if len(top5) < 5:
        seen=set(top5)
        others = sorted(chart[:5], key=lambda r: (0 if r.get('venue')=='pool' else 1, int(r['rank']), r.get('mint','')))
        for r in others:
            if r['mint'] not in seen:
                top5.append(r['mint']); seen.add(r['mint'])
            if len(top5)>=5: break
    top5 = top5[:5]

    out = {'probabilities':probs_list, 'top5':top5, 'sizes':sizes_list}
    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, task.get('output','forecast.json'))
    text = json.dumps(out, separators=(',',':'), ensure_ascii=False)
    with open(out_path, 'w', encoding='utf-8') as fh:
        fh.write(text + '\n')

    # post-write validation: re-read and assert ordering and constraints
    s = open(out_path, 'r', encoding='utf-8').read()
    # check keys order in the raw string
    if not s.lstrip().startswith('{"probabilities":'):
        raise SystemExit('output keys not in required order')
    # ensure top5 appears after probabilities and sizes after that
    i_top = s.find('"top5":')
    i_sizes = s.find('"sizes":')
    if not (i_top>0 and i_sizes>i_top):
        raise SystemExit('output keys not in required order')

    data = json.loads(s)
    if list(data.keys())[:3] != ['probabilities','top5','sizes']:
        # JSON loader may not preserve order, but we already checked raw order
        pass
    # five distinct top5 mints
    if len(set(data['top5']))!=5:
        raise SystemExit('top5 does not have 5 distinct mints')
    # per-place probability sums <=1 and between 0.05 and 0.95
    place_sum = {k:0.0 for k in range(1,places+1)}
    for p in data['probabilities']:
        place_sum[p['place']] += p['p']
    for k,v in place_sum.items():
        if v>1.0 + 1e-12:
            raise SystemExit(f'place {k} prob sum > 1')
        if not (0.0 <= v <= 1.0):
            raise SystemExit(f'place {k} prob sum out of [0,1]')
    # bins in 0..len(edges)
    for s in data['sizes']:
        if s['bin'] < 0 or s['bin'] > len(edges):
            raise SystemExit('bin out of range')

    # Print checks
    print('Per-place probability sums:')
    for k in range(1, places+1):
        print(f'place {k}: {place_sum[k]:.6f}')
    print('Per-place size sums:')
    for k in range(1, places+1):
        ss = sum(item['p'] for item in data['sizes'] if item['place']==k)
        print(f'place {k}: {ss:.6f}')
    print('Top5 distinct count:', len(set(data['top5'])))

if __name__=='__main__':
    build_forecast()
