from pathlib import Path
import matplotlib.pyplot as plt
from common_cap3 import load_subjects, day_slice, time_axis, N_12_DAYS

BASE_DIR = Path('.').resolve()
OUT_DIR = BASE_DIR / 'figuras_cap3'
OUT_DIR.mkdir(exist_ok=True)
subjects = load_subjects(base_dir=BASE_DIR, n_points=N_12_DAYS)

# Figura 3: ejemplo de 24 h. Cambiar estos valores si en el documento se usaron otros sujetos/días.
sujeto_ndbt2 = 1
sujeto_dbt2 = 1
dia = 0

G_s = subjects['NDBT2'][sujeto_ndbt2][day_slice(dia, 0, 24)]
G_e = subjects['DBT2'][sujeto_dbt2][day_slice(dia, 0, 24)]
t = time_axis(len(G_s), unit='hours')

plt.figure(figsize=(10, 4.8))
plt.plot(t, G_s, marker='o', markersize=3, linewidth=1.6, label=f'NDBT2 sujeto {sujeto_ndbt2}')
plt.plot(t, G_e, marker='o', markersize=3, linewidth=1.6, label=f'DBT2 sujeto {sujeto_dbt2}')
plt.axhline(70, linestyle='--', linewidth=1, label='70 mg/dL')
plt.axhline(180, linestyle='--', linewidth=1, label='180 mg/dL')
plt.xlabel('Tiempo (h)')
plt.ylabel('Glucosa (mg/dL)')
plt.title('Ejemplo de registros CGM durante 24 h')
plt.xlim(0, 24)
plt.grid(alpha=0.25)
plt.legend(ncol=2)
plt.tight_layout()
plt.savefig(OUT_DIR / 'figura_3_registros_24h.png', dpi=300)
plt.show()
