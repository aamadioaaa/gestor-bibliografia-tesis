from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from common_cap3 import load_subjects, permutation_distribution, h_complexity, hx_c_bounds, N_12_DAYS

BASE_DIR = Path('.').resolve()
OUT_DIR = BASE_DIR / 'figuras_cap3'
OUT_DIR.mkdir(exist_ok=True)
subjects = load_subjects(base_dir=BASE_DIR, n_points=N_12_DAYS)

rows = []
for grupo, data in subjects.items():
    for sid, G in data.items():
        p = permutation_distribution(G, D=3, tau=1)
        H, C = h_complexity(p)
        rows.append({'grupo': grupo, 'sujeto': sid, 'H': H, 'C': C})
res = pd.DataFrame(rows)
print(res)
print(res.groupby('grupo')[['H','C']].agg(['mean','std','count']))
centroids = res.groupby('grupo')[['H','C']].mean()
print('\nCentroides:')
print(centroids)

Hgrid, Cmin, Cmax = hx_c_bounds(M=6, n_random=30000, seed=123)
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
for ax in axes:
    ax.plot(Hgrid, Cmin, linewidth=1.2, label=r'$C_{min}$ aprox.')
    ax.plot(Hgrid, Cmax, linewidth=1.2, label=r'$C_{max}$ aprox.')
    for grupo, marker in [('NDBT2', 'o'), ('DBT2', 's')]:
        sub = res[res.grupo == grupo]
        ax.scatter(sub['H'], sub['C'], marker=marker, s=45, label=grupo, alpha=0.85)
    ax.scatter(centroids.loc['NDBT2','H'], centroids.loc['NDBT2','C'], s=140, marker='X', label='Centroide NDBT2')
    ax.scatter(centroids.loc['DBT2','H'], centroids.loc['DBT2','C'], s=140, marker='X', label='Centroide DBT2')
    ax.set_xlabel('Entropía normalizada H')
    ax.set_ylabel('Complejidad estadística C')
    ax.grid(alpha=0.25)
axes[0].set_title('A. Plano H×C global')
axes[0].set_xlim(0, 1)
axes[0].set_ylim(0, max(np.nanmax(Cmax), res.C.max()) * 1.1)
axes[1].set_title('B. Ampliación de zona de interés')
axes[1].set_xlim(0.7, 1.0)
axes[1].set_ylim(0, 0.22)
axes[1].legend(loc='best', fontsize=8)
plt.tight_layout()
plt.savefig(OUT_DIR / 'figura_3_4_HxC.png', dpi=300)
plt.show()
