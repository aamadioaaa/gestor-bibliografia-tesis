from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import ttest_ind
from common_cap3 import load_subjects, savgol_trend, colored_noise_beta, N_12_DAYS

BASE_DIR = Path('.').resolve()
OUT_DIR = BASE_DIR / 'figuras_cap3'
OUT_DIR.mkdir(exist_ok=True)
subjects = load_subjects(base_dir=BASE_DIR, n_points=N_12_DAYS)

rows = []
psd_data = {'NDBT2': [], 'DBT2': []}
for grupo, data in subjects.items():
    for sid, G in data.items():
        r = G - savgol_trend(G, window=51, polyorder=3)
        # Rango equivalente al 0.01-0.4 indicado en el texto, expresado en ciclos/día.
        beta, f, pxx, _ = colored_noise_beta(r, fit_range=(0.96, 38.4))
        rows.append({'grupo': grupo, 'sujeto': sid, 'beta': beta})
        psd_data[grupo].append((f, pxx))
res = pd.DataFrame(rows)
print(res)

b_s = res.loc[res.grupo == 'NDBT2', 'beta'].dropna()
b_e = res.loc[res.grupo == 'DBT2', 'beta'].dropna()
stat, pval = ttest_ind(b_e, b_s, equal_var=False, nan_policy='omit')
print(f'Beta NDBT2: {b_s.mean():.3f} ± {b_s.std(ddof=1):.3f}')
print(f'Beta DBT2:  {b_e.mean():.3f} ± {b_e.std(ddof=1):.3f}')
print(f't={stat:.3f}, p={pval:.4g}')

fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
for grupo in ['NDBT2', 'DBT2']:
    arrs = []
    f_ref = None
    for f, pxx in psd_data[grupo]:
        mask = (f > 0) & (pxx > 0)
        axes[0].loglog(f[mask], pxx[mask], alpha=0.25, linewidth=0.8)
        if f_ref is None:
            f_ref = f
        arrs.append(pxx)
    if arrs:
        mean_pxx = np.nanmean(np.vstack(arrs), axis=0)
        mask = (f_ref > 0) & (mean_pxx > 0)
        axes[0].loglog(f_ref[mask], mean_pxx[mask], linewidth=2.4, label=f'Promedio {grupo}')
axes[0].set_xlabel('Frecuencia (ciclos/día)')
axes[0].set_ylabel('PSD')
axes[0].set_title('A. PSD individual y promedio')
axes[0].grid(alpha=0.25, which='both')
axes[0].legend()

positions = [1, 2]
axes[1].boxplot([b_s, b_e], positions=positions, labels=['NDBT2', 'DBT2'], showmeans=True)
for i, vals in zip(positions, [b_s, b_e]):
    axes[1].scatter(np.full(len(vals), i) + np.linspace(-0.06, 0.06, len(vals)), vals, s=28)
axes[1].set_ylabel(r'Exponente espectral $\beta$')
axes[1].set_title('B. Distribución de beta por grupo')
axes[1].grid(alpha=0.25)

plt.tight_layout()
plt.savefig(OUT_DIR / 'figura_3_1_3_ruido_coloreado.png', dpi=300)
plt.show()
