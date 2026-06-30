from pathlib import Path
import matplotlib.pyplot as plt
from common_cap3 import load_subjects, day_slice, time_axis, metabolic_force, N_12_DAYS

BASE_DIR = Path('.').resolve()
OUT_DIR = BASE_DIR / 'figuras_cap3'
OUT_DIR.mkdir(exist_ok=True)
subjects = load_subjects(base_dir=BASE_DIR, n_points=N_12_DAYS)

grupo = 'DBT2'
sujeto = 5
dia = 0
G = subjects[grupo][sujeto][day_slice(dia, 0, 24)]
res = metabolic_force(G, window_energy=10, keep_fraction=0.10, kappa=1.0, formula='vc_times_Ehat')
S = res['S']
t = time_axis(len(G), unit='hours')

fig, axes = plt.subplots(2, 1, figsize=(10, 6.5), sharex=True)
axes[0].plot(t, G, linewidth=1.8)
axes[0].set_ylabel('Glucosa (mg/dL)')
axes[0].set_title('Perfil de glucosa')
axes[0].grid(alpha=0.25)

axes[1].plot(t, S, linewidth=1.8, label='S(t)')
axes[1].axhline(0, linestyle='--', linewidth=1)
axes[1].set_xlabel('Tiempo (h)')
axes[1].set_ylabel('mg/dL/min')
axes[1].set_title('Indicador de forzamiento metabólico S(t)')
axes[1].grid(alpha=0.25)
axes[1].legend()

plt.tight_layout()
plt.savefig(OUT_DIR / 'figura_3_2_4_indicador_S_t.png', dpi=300)
plt.show()
