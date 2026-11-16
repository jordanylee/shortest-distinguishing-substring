"""Write two Markdown reports from explicitly selected saved comparison runs."""
from pathlib import Path
import hashlib
import json

from result_summary import summarize

ROOT=Path(__file__).resolve().parents[1]
OLD_SOURCE='2026-11-15_19-36-35-433280_UTC'
FULL='2026-11-15_19-55-50-157162_UTC'
SUBSET='2026-11-15_21-22-02-784266_UTC'
NEW_SOURCE='2026-11-15_21-32-55-118406_UTC'
NEW_RESULTS='2026-11-15_21-33-59-533782_UTC'


def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','|'+'---|'*len(headers)]+
                     ['| '+' | '.join(str(v) for v in row)+' |' for row in rows])


def load(source,result,states,subset=False):
    records=[]
    for a in (2,3):
        for s in states:
            directory=ROOT/'data'/f'alphabet_{a}'/f'states_{s}'/source
            p=directory/('comparisons_below_half' if subset else 'comparisons')/result
            m=json.loads((p/'manifest.json').read_text(encoding='utf-8'))
            if (m['status'],m['source_run_id'],m['results_id'],m['alphabet_size'],m['state_count'],m['calculations']) != ('complete',source,result,a,s,'both'):
                raise ValueError(f'Unexpected run: {p}')
            for name,digest in m['source_sha256'].items():
                if hashlib.sha256((directory/name).read_bytes()).hexdigest()!=digest:
                    raise ValueError('Source hash mismatch')
            summary=summarize(p)
            h=summary['length_histogram']
            if {str(k):v for k,v in h.items()}!=m['length_histogram'] or summary['equivalent_pair_count']!=m['equivalent_pair_count']:
                raise ValueError('Saved counts disagree')
            n=m['dfa_count']
            if m['pair_count']!=n*(n-1)//2:
                raise ValueError('Incorrect all-pairs denominator')
            if subset:
                selected=m['dfa_selection']
                if selected['name']!='strictly_below_half_accepting' or len(selected['selected_ids'])!=n or any(2*d['accepting_states']>=d['raw_states'] for d in selected['selected_dfas']):
                    raise ValueError('Incorrect selection')
            finite=sum(h.values()); positive=finite-h.get(0,0)
            weighted=sum(k*v for k,v in h.items())
            records.append(dict(a=a,s=s,m=m,summary=summary,h=h,finite_mean=weighted/finite,
                                positive_mean=weighted/positive,positive=positive,
                                tail=sum(v for k,v in h.items() if k>=3)/positive*100))
            print(f'Checked {p.relative_to(ROOT)}',flush=True)
    return records


def count_tables(records):
    max_length=max(max(r['h']) for r in records)
    lines=[]
    for a in (2,3):
        lines += [f'## Exact SDS counts — alphabet {a}','',table(
            ['States']+[f'SDS {i}' for i in range(max_length+1)]+['Equivalent','Total pairs'],
            [[r['s']]+[f"{r['h'].get(i,0):,}" for i in range(max_length+1)]+
             [f"{r['m']['equivalent_pair_count']:,}",f"{r['m']['pair_count']:,}"] for r in records if r['a']==a]),'']
    return lines


def main():
    output=ROOT/'data'/'reports'; output.mkdir(exist_ok=True)
    subset=load(OLD_SOURCE,SUBSET,(10,15,20,25,30),True)
    baseline=load(OLD_SOURCE,FULL,(10,15,20,25,30))
    additional=load(NEW_SOURCE,NEW_RESULTS,(5,10,15))
    if {r['m']['distribution']['horizon'] for r in subset+baseline+additional}!={5}:
        raise ValueError('Reports require matching H=5')
    for sub,base in zip(subset,baseline):
        if sub['m']['source_sha256']!=base['m']['source_sha256']:
            raise ValueError('Baseline/subset source mismatch')
    provenance=lambda source,result: table(['Setting','Value'],[
        ['Source run',f'`{source}`'],['Comparison run',f'`{result}`'],['Similarity horizon','H=5; uniform length 0–5, then uniform symbols'],
        ['Pairing','All unordered pairs within each alphabet/state batch'],['SDS convention','0 = empty-string distinction; equivalent = no finite SDS']])
    lines=['# DFAs with fewer than 50% accepting states','',
           '**Filter:** both DFAs have strictly <50% accepting raw states, including unreachable states. Exactly 50% is excluded. No DFAs were regenerated.','',
           provenance(OLD_SOURCE,SUBSET),'', '## Selected DFAs and pair counts','',
           table(['Alphabet','States','Source DFAs','Selected DFAs','Retained','Subset pairs'],
                 [[r['a'],r['s'],r['m']['source_dfa_count'],r['m']['dfa_count'],f"{r['m']['dfa_count']/r['m']['source_dfa_count']:.1%}",f"{r['m']['pair_count']:,}"] for r in subset]+[
                     ['Total','—',sum(r['m']['source_dfa_count'] for r in subset),sum(r['m']['dfa_count'] for r in subset),'—',f"{sum(r['m']['pair_count'] for r in subset):,}"]]),'']
    lines+=count_tables(subset)
    lines+=['## SDS: full sample versus filtered subset','',
            '“Positive” excludes SDS=0 and equivalent pairs. Tail percentages use positive finite pairs as the denominator.','',
            table(['Alphabet','States','SDS=0 % full','SDS=0 % subset','Positive mean full','Positive mean subset','SDS ≥3 % full','SDS ≥3 % subset'],
                  [[u['a'],u['s'],f"{b['h'].get(0,0)/b['m']['pair_count']*100:.2f}",f"{u['h'].get(0,0)/u['m']['pair_count']*100:.2f}",f"{b['positive_mean']:.4f}",f"{u['positive_mean']:.4f}",f"{b['tail']:.3f}",f"{u['tail']:.3f}"] for u,b in zip(subset,baseline)]),'',
            '## Mean similarities: full sample versus filtered subset','',
            'Means include all pairs, including length zero and equivalent pairs.','',
            table(['Alphabet','States','Agreement full','Agreement subset','Jaccard full','Jaccard subset'],
                  [[u['a'],u['s']]+[f"{r['summary']['mean_similarity'][metric]:.4f}" for metric in ('probability_of_agreement','weighted_jaccard') for r in (b,u)] for u,b in zip(subset,baseline)]),'',
            f'Full-sample comparison ID: `{FULL}`. These are descriptive, overlapping samples; pairs share DFAs.','',
            '## The missing length-5 count','',
            table(['Sample','Alphabet','States','Pairs with SDS=5'],
                  [['Filtered subset',2,10,0],['Filtered subset',2,15,0],['Earlier full sample',2,15,baseline[1]['h'].get(5,0)],
                   ['Earlier full sample',2,20,baseline[2]['h'].get(5,0)],['Additional seed-20 sample',2,5,additional[0]['h'].get(5,0)]]),'',
            'Length 5 is possible. Its absence in the filtered subset is a sample observation; no explanation for that particular gap has been established.','']
    (output/'below_half_accepting.md').write_text('\n'.join(lines),encoding='utf-8')
    lines=['# Additional comparisons: 5, 10 and 15 states','',provenance(NEW_SOURCE,NEW_RESULTS),'',
           table(['Sampling','Value'],[['Master seed','20 (earlier full sample used 42)'],['Filter','None; all generated DFAs retained'],
                                      ['Configurations','Alphabets 2/3 × states 5/10/15'],['DFAs per configuration','500'],
                                      ['Total DFAs','3,000'],['Pairs per configuration','124,750'],['Total pairs','748,500']]),'']
    lines+=count_tables(additional)
    lines+=['## SDS summary','',
            table(['Alphabet','States','Mean finite SDS','Mean positive SDS','Maximum SDS','SDS ≥3 pairs','SDS ≥3 % of positive pairs','Equivalent %'],
                  [[r['a'],r['s'],f"{r['finite_mean']:.4f}",f"{r['positive_mean']:.4f}",max(r['h']),f"{sum(v for k,v in r['h'].items() if k>=3):,}",f"{r['tail']:.3f}",f"{r['m']['equivalent_pair_count']/r['m']['pair_count']*100:.3f}"] for r in additional]),'',
            'Finite means include SDS=0; positive means exclude it. Both exclude equivalent pairs.','',
            '## Mean similarities (H=5)','',
            table(['Alphabet','States','Agreement','Weighted Jaccard'],
                  [[r['a'],r['s']]+[f"{r['summary']['mean_similarity'][m]:.4f}" for m in ('probability_of_agreement','weighted_jaccard')] for r in additional]),'',
            'Similarity means include all pairs. The new binary/5-state batch has **four pairs with SDS=5**, confirming that length 5 is not forbidden. Pairs sharing DFAs are dependent.','']
    (output/'additional_comparisons_seed20.md').write_text('\n'.join(lines),encoding='utf-8')
    print(f'Wrote two reports to {output}',flush=True)


if __name__=='__main__':
    main()
