"""Regenerate the README's major-provider chart from audited A+B outputs."""
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def plot_top10_rates(root=ROOT):
    """Plot within-brand rates; no outcomes or assignments are modified."""
    summary = pd.read_csv(root / 'reports/brand_summary.csv')
    brands = ['Nike', 'Under Armour', 'adidas']
    direct = summary.loc[summary.evidence_tiers.eq('A+B')].set_index('brand').loc[brands]
    counts = direct.n_school_seasons.astype(int)
    rates = 100 * direct.top10_finishes / counts
    fig, ax = plt.subplots(figsize=(10, 4.8), dpi=180)
    fig.subplots_adjust(left=0.18, right=0.94, top=0.72, bottom=0.23)
    positions = [2, 1, 0]
    ax.barh(positions, rates, height=0.56, color=['#172f34', '#89a89f', '#547b86'])
    ax.set_yticks(positions, brands, fontsize=14)
    ax.set_xlim(0, 25)
    ax.set_xticks([0, 5, 10, 15, 20, 25])
    ax.xaxis.set_major_formatter(PercentFormatter(xmax=100, decimals=0))
    ax.tick_params(axis='both', length=0, pad=9)
    ax.grid(axis='x', color='#e4e9e7', linewidth=0.8)
    ax.set_axisbelow(True)
    ax.spines[['top', 'right', 'left', 'bottom']].set_visible(False)
    ax.set_xlabel('Top-10 finishes within each brand’s school-seasons', fontsize=12, labelpad=14)
    for position, brand, rate in zip(positions, brands, rates):
        ax.text(rate + 0.5, position + 0.08, f'{rate:.1f}%', fontsize=15, weight='bold', va='center')
        ax.text(rate + 0.5, position - 0.14, f'n = {counts.loc[brand]}', fontsize=11, va='center', color='#52605e')
    fig.text(0.04, 0.92, 'Nike schools finish in the top 10 more often', fontsize=21, weight='bold', color='#172f34')
    fig.text(0.04, 0.84, 'Direct sponsor evidence (A+B) · major providers in the researched cohort', fontsize=12, color='#52605e')
    fig.text(0.04, 0.035, 'n = school-seasons. Within-brand rates, not national market shares. Descriptive, not causal.', fontsize=10, color='#52605e')
    target = root / 'docs/images/top10_finish_rates.png'
    target.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(target, facecolor='white')
    plt.close(fig)
    return target


if __name__ == '__main__':
    plot_top10_rates()
