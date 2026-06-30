from pathlib import Path
import matplotlib.pyplot as plt
from common_cap3 import load_subjects, day_slice, time_axis, local_energy, dct_smooth_energy, N_12_DAYS

BASE_DIR = Path('.').resolve()
OUT_DIR = BASE_DIR / 'figuras_cap3'
OUT_DIR.mkdir(exist_ok=True)
subjects = load_subjects(base_dir=BASE_DIR, n_points=N_12_DAYS)

grupo = 'DBT2'
sujeto = 5
dia = 0
G = subjects[grupo][sujeto][day_slice(dia, 0, 24)]
E = local_energy(G, window=10)
E_s = dct_smooth_energy(E, keep_fraction=0.10)
t = time_axis(len(G), unit='hours')

fig, axes = plt.subplots(2, 1, figsize=(10, 6.5), sharex=True)
axes[0].plot(t, G, linewidth=1.8)
axes[0].set_ylabel('Glucosa (mg/dL)')
axes[0].set_title('Excursión glucémica')
axes[0].grid(alpha=0.25)

axes[1].plot(t, E, linewidth=1.0, alpha=0.45, label='Energía local cruda')
axes[1].plot(t, E_s, linewidth=2.0, label='Energía local reconstruida por DCT')
axes[1].set_xlabel('Tiempo (h)')
axes[1].set_ylabel(r'Varianza local $(mg/dL)^2$')
axes[1].set_title('Energía local mediante enventanado y suavizado DCT')
axes[1].grid(alpha=0.25)
axes[1].legend()

plt.tight_layout()
plt.savefig(OUT_DIR / 'figura_3_2_3_energia_local_DCT.png', dpi=300)
plt.show()
