from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from common_cap3 import load_subjects, lyapunov_rosenstein, N_12_DAYS

BASE_DIR = Path('.').resolve()
OUT_DIR = BASE_DIR / 'figuras_cap3'
OUT_DIR.mkdir(exist_ok=True)
subjects = load_subjects(base_dir=BASE_DIR, n_points=N_12_DAYS)

rows = []
example_curve = None
for grupo, data in subjects.items():
    for sid, G in data.items():
        lam, TL, t_h, logd = lyapunov_rosenstein(G, m=4, tau=4, min_tsep=96, max_k=40, fit_k=(1, 12))
        rows.append({'grupo': grupo, 'sujeto': sid, 'lambda_h_inv': lam, 'T_L_horas': TL})
        if grupo == 'DBT2' and sid == 5:
            example_curve = (t_h, logd, lam)
res = pd.DataFrame(rows)
print(res)
print(res.groupby('grupo')[['lambda_h_inv', 'T_L_horas']].agg(['mean','std','count']))

fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
if example_curve is not None:
    t_h, logd, lam = example_curve
    axes[0].plot(t_h, logd, marker='o', markersize=3, linewidth=1.2)
    axes[0].set_title(fr'Divergencia media: $\lambda={lam:.3f}$ h$^{{-1}}$')
    axes[0].set_xlabel('Tiempo de evolución (h)')
    axes[0].set_ylabel(r'$\langle \ln d(k) \rangle$')
    axes[0].grid(alpha=0.25)

vals_s = res.loc[res.grupo == 'NDBT2', 'lambda_h_inv'].dropna()
vals_e = res.loc[res.grupo == 'DBT2', 'lambda_h_inv'].dropna()
axes[1].boxplot([vals_s, vals_e], labels=['NDBT2', 'DBT2'], showmeans=True)
axes[1].set_ylabel(r'$\lambda$ (h$^{-1}$)')
axes[1].set_title('Exponente máximo de Lyapunov por grupo')
axes[1].grid(alpha=0.25)

plt.tight_layout()
plt.savefig(OUT_DIR / 'figura_3_3_lyapunov.png', dpi=300)
plt.show()
