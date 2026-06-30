from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from common_cap3 import load_subjects, metabolic_force, colored_noise_beta, N_12_DAYS

BASE_DIR = Path('.').resolve()
OUT_DIR = BASE_DIR / 'figuras_cap3'
OUT_DIR.mkdir(exist_ok=True)
subjects = load_subjects(base_dir=BASE_DIR, n_points=N_12_DAYS)

rows = []
psd = {'NDBT2': [], 'DBT2': []}
for grupo, data in subjects.items():
    for sid, G in data.items():
        S = metabolic_force(G, formula='vc_times_Ehat')['S']
        beta_low, f, pxx, _ = colored_noise_beta(S, fit_range=(0.5, 4.0))
        beta_high, _, _, _ = colored_noise_beta(S, fit_range=(12.0, 40.0))
        rows.append({'grupo': grupo, 'sujeto': sid, 'beta_baja_0_5_4_ciclos_dia': beta_low, 'beta_alta_12_40_ciclos_dia': beta_high})
        psd[grupo].append((f, pxx))
res = pd.DataFrame(rows)
print(res)
print(res.groupby('grupo')[['beta_baja_0_5_4_ciclos_dia', 'beta_alta_12_40_ciclos_dia']].agg(['mean','std','count']))

fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
for grupo in ['NDBT2', 'DBT2']:
    curves = []
    f_ref = None
    for f, pxx in psd[grupo]:
        mask = (f > 0) & (pxx > 0)
        axes[0].loglog(f[mask], pxx[mask], alpha=0.22, linewidth=0.8)
        if f_ref is None:
            f_ref = f
        curves.append(pxx)
    if curves:
        mean_pxx = np.nanmean(np.vstack(curves), axis=0)
        mask = (f_ref > 0) & (mean_pxx > 0)
        axes[1].loglog(f_ref[mask], mean_pxx[mask], linewidth=2.2, label=f'Promedio {grupo}')

axes[0].set_title('A. PSD individual de S(t)')
axes[1].set_title('B. PSD promedio de S(t)')
for ax in axes:
    ax.set_xlabel('Frecuencia (ciclos/día)')
    ax.set_ylabel('PSD')
    ax.grid(alpha=0.25, which='both')
axes[1].legend()
plt.tight_layout()
plt.savefig(OUT_DIR / 'figura_3_2_5_PSD_S_t.png', dpi=300)
plt.show()
