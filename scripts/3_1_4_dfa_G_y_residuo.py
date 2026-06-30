from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from common_cap3 import load_subjects, savgol_trend, dfa_alpha, N_12_DAYS

BASE_DIR = Path('.').resolve()
OUT_DIR = BASE_DIR / 'figuras_cap3'
OUT_DIR.mkdir(exist_ok=True)
subjects = load_subjects(base_dir=BASE_DIR, n_points=N_12_DAYS)

rows = []
curves_G = {'NDBT2': [], 'DBT2': []}
curves_r = {'NDBT2': [], 'DBT2': []}
for grupo, data in subjects.items():
    for sid, G in data.items():
        trend = savgol_trend(G, window=51, polyorder=3)
        r = G - trend
        aG, scalesG, FG, _ = dfa_alpha(G, order=1)
        ar, scalesr, Fr, _ = dfa_alpha(r, order=1)
        rows.append({'grupo': grupo, 'sujeto': sid, 'alpha_G': aG, 'alpha_residuo': ar})
        curves_G[grupo].append((scalesG, FG))
        curves_r[grupo].append((scalesr, Fr))
res = pd.DataFrame(rows)
print(res)
print(res.groupby('grupo')[['alpha_G', 'alpha_residuo']].agg(['mean','std','count']))

fig, axes = plt.subplots(2, 2, figsize=(12, 9))
for grupo in ['NDBT2', 'DBT2']:
    for sc, F in curves_G[grupo]:
        axes[0, 0].loglog(sc, F, alpha=0.25, linewidth=0.8)
    for sc, F in curves_r[grupo]:
        axes[1, 0].loglog(sc, F, alpha=0.25, linewidth=0.8)

for ax, col, title in [(axes[0, 1], 'alpha_G', 'B. DFA de G(t)'), (axes[1, 1], 'alpha_residuo', 'D. DFA del residuo')]:
    vals_s = res.loc[res.grupo == 'NDBT2', col].dropna()
    vals_e = res.loc[res.grupo == 'DBT2', col].dropna()
    ax.boxplot([vals_s, vals_e], labels=['NDBT2', 'DBT2'], showmeans=True)
    ax.set_ylabel(r'Exponente $\alpha$')
    ax.set_title(title)
    ax.grid(alpha=0.25)

axes[0, 0].set_title('A. Curvas DFA para G(t)')
axes[0, 0].set_xlabel('Escala n (muestras)')
axes[0, 0].set_ylabel('F(n)')
axes[0, 0].grid(alpha=0.25, which='both')
axes[1, 0].set_title('C. Curvas DFA para componente fluctuante')
axes[1, 0].set_xlabel('Escala n (muestras)')
axes[1, 0].set_ylabel('F(n)')
axes[1, 0].grid(alpha=0.25, which='both')
plt.tight_layout()
plt.savefig(OUT_DIR / 'figura_3_1_4_dfa.png', dpi=300)
plt.show()
