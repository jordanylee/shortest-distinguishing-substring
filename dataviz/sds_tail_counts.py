"""Explain and plot finite SDS tail counts from saved result histograms."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, FuncFormatter

from state_distributions import ROOT, SOURCE_ID, RESULTS_ID, COLOR_FAMILIES, STATE_SHADES


def run(source_id=SOURCE_ID, results_id=RESULTS_ID, output=None):
    output = Path(output) if output is not None else ROOT/'dataviz'/'figures'/'sds_tail_counts'
    output.mkdir(parents=True, exist_ok=True)
    histograms, batches, inputs = {}, [], []
    for alphabet in (2,3):
        for states in (10,15,20,25,30):
            path = ROOT/'data'/f'alphabet_{alphabet}'/f'states_{states}'/source_id/'comparisons'/results_id/'manifest.json'
            m = json.loads(path.read_text(encoding='utf-8'))
            if (m['status'],m['source_run_id'],m['results_id'],m['alphabet_size'],m['state_count'],m['dfa_count'],m['calculations']) != ('complete',source_id,results_id,alphabet,states,500,'both'):
                raise ValueError(f'Unexpected results: {path}')
            hist = {int(k):v for k,v in m['length_histogram'].items()}
            if any(k < 0 or not isinstance(v,int) or v < 0 for k,v in hist.items()):
                raise ValueError('Invalid histogram')
            if sum(hist.values())+m['equivalent_pair_count'] != m['pair_count'] or m['pair_count'] != 124750:
                raise ValueError('Histogram denominator mismatch')
            histograms[alphabet,states] = hist
            batches.append(dict(alphabet_size=alphabet,generated_states=states,total_pairs=m['pair_count'],
                                equivalent_pairs=m['equivalent_pair_count'],finite_pairs=sum(hist.values())))
            inputs.append(dict(path=path.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    thresholds = list(range(2,max(max(h) for h in histograms.values())+1))
    tails = {key:[sum(n for length,n in hist.items() if length >= d) for d in thresholds] for key,hist in histograms.items()}
    rows = [dict(alphabet_size=a,generated_states=s,minimum_sds_length=d,pairs_with_sds_at_least_d=n)
            for (a,s),counts in tails.items() for d,n in zip(thresholds,counts)]
    with (output/'sds_tail_counts.csv').open('w',newline='',encoding='utf-8') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)

    fig=plt.figure(figsize=(15,10))
    fig.suptitle('How many pairs need a distinguishing string at least this long?',fontsize=19,y=.975)
    fig.text(.5,.935,'SDS = shortest distinguishing string length: the fewest symbols needed for exactly one DFA to accept.',ha='center',fontsize=12)
    markers={10:'o',15:'s',20:'^',25:'D',30:'v'}
    max_count=max(max(t) for t in tails.values())
    for alphabet,left in ((2,.075),(3,.565)):
        ax=fig.add_axes([left,.435,.395,.435])
        for states in (10,15,20,25,30):
            counts=tails[alphabet,states]
            color=plt.get_cmap(COLOR_FAMILIES[alphabet])(STATE_SHADES[states])
            ax.plot(thresholds,[n if n else float('nan') for n in counts],
                    marker=markers[states],color=color,linewidth=1.8,markersize=6,label=f'{states} states')
        ax.set(title=f'Alphabet size {alphabet}',xlabel='Minimum required SDS length d (symbols)',
               ylabel='Pairs with finite SDS >= d (logarithmic scale)',yscale='log',
               xlim=(thresholds[0]-.15,thresholds[-1]+.15),ylim=(.7,max_count*2))
        ax.set_xticks(thresholds)
        ax.yaxis.set_major_locator(FixedLocator([1,10,100,1000,10000]))
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v,pos:f'{v:,.0f}'))
        ax.grid(axis='y',which='major',alpha=.25)
        ax.spines[['top','right']].set_visible(False)
        ax.legend(title='Generated DFA size',frameon=False,fontsize=9,loc='upper right')
        fig.text(left,.386,'Exact counts at each threshold (0 means no finite pair qualifies):',fontsize=10)
        table_ax=fig.add_axes([left,.224,.395,.145]); table_ax.axis('off')
        table=table_ax.table(cellText=[[f'{s} states']+[f'{n:,}' for n in tails[alphabet,s]] for s in (10,15,20,25,30)],
                            colLabels=['DFA size']+[f'SDS >= {d}' for d in thresholds],cellLoc='center',bbox=[0,0,1,1])
        table.auto_set_font_size(False); table.set_fontsize(9)
        for (row,col),cell in table.get_celld().items():
            cell.set_edgecolor('#dddddd')
            if row==0: cell.set_facecolor('#eeeeee')
            elif col==0: cell.set_text_props(color=plt.get_cmap(COLOR_FAMILIES[alphabet])(STATE_SHADES[(10,15,20,25,30)[row-1]]),weight='bold')
    example=tails[2,10][thresholds.index(4)] if 4 in thresholds else None
    fig.text(.075,.174,'How to read this plot',fontsize=12,weight='bold')
    fig.text(.075,.143,'Each point counts ALL pairs whose shortest distinguishing string has d or more symbols, not just exactly d.',fontsize=11)
    if example is not None:
        fig.text(.075,.112,f'Example: for alphabet 2 and 10 states, d = 4 counts {example:,} pairs with SDS 4, 5, 6, or longer.',fontsize=11)
    fig.text(.075,.081,'Counts are nested: a pair counted at d = 6 is also counted at d = 5, 4, 3, and 2. Never add the points together.',fontsize=11)
    fig.text(.075,.050,'Vertical ticks multiply by 10 (1, 10, 100, ...). Zero cannot appear on a log axis; zeros are shown in the tables.',fontsize=11)
    fig.text(.075,.019,'Each configuration has 124,750 pairs of 500 DFAs. SDS 0/1 and equivalent pairs are excluded. Pairs share DFAs; counts are descriptive.',fontsize=10)
    fig.savefig(output/'sds_tail_counts.svg',facecolor='white')
    plt.close(fig)
    provenance=dict(created_utc=datetime.now(timezone.utc).isoformat(),source_id=source_id,results_id=results_id,
                    inputs=inputs,batches=batches,thresholds=thresholds,definition='Count of finite SDS lengths >= d; not exact-length frequencies',
                    equivalent_handling='Excluded: equivalent pairs have no finite SDS',
                    source='Saved complete manifest histograms, not recalculated pair results',
                    matplotlib=matplotlib.__version__,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (output/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n',encoding='utf-8')
    print(f'Saved tail-count SVG, exact CSV and provenance to {output}')
    return output


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-id',default=SOURCE_ID)
    parser.add_argument('--results-id',default=RESULTS_ID)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    run(args.source_id,args.results_id,args.output)
