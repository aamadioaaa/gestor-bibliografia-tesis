from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from common_cap3 import load_subjects, optm_stationary_indicator, classify_stat_ms, N_12_DAYS

BASE_DIR = Path('.').resolve()
OUT_DIR = BASE_DIR / 'figuras_cap3'
OUT_DIR.mkdir(exist_ok=True)
subjects = load_subjects(base_dir=BASE_DIR, n_points=N_12_DAYS)

rows = []
for grupo, data in subjects.items():
    for sid, G in data.items():
        stat_ms, P, vS = optm_stationary_indicator(G, D=3, tau=1)
        rows.append({'grupo': grupo, 'sujeto': sid, 'Stat_MS': stat_ms, 'diagnostico_por_umbral': classify_stat_ms(stat_ms)})
res = pd.DataFrame(rows).sort_values(['grupo','sujeto'])
print(res)

# Tabla pivote similar a la del documento.
pivot = res.pivot(index='sujeto', columns='grupo', values='Stat_MS')
print('\nTabla Stat_MS por sujeto:')
print(pivot)

fig, ax = plt.subplots(figsize=(10, 4.8))
for grupo, marker in [('NDBT2', 'o'), ('DBT2', 's')]:
    sub = res[res.grupo == grupo]
    ax.scatter(sub['sujeto'], sub['Stat_MS'], marker=marker, s=45, label=grupo)
ax.axhline(0.49, linestyle='--', linewidth=1, label='Umbral sano/dudoso')
ax.axhline(0.505, linestyle='--', linewidth=1, label='Umbral dudoso/diabetes')
ax.set_xlabel('Sujeto')
ax.set_ylabel(r'$||v_S||$')
ax.set_title('Indicador OPTM basado en vector estacionario')
ax.grid(alpha=0.25)
ax.legend()
plt.tight_layout()
plt.savefig(OUT_DIR / 'figura_3_4_OPTM_Stat_MS.png', dpi=300)
plt.show()
