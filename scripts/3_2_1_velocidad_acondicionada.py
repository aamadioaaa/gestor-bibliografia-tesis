from pathlib import Path
import matplotlib.pyplot as plt
from common_cap3 import load_subjects, day_slice, time_axis, centered_velocity, conditioned_velocity, N_12_DAYS

BASE_DIR = Path('.').resolve()
OUT_DIR = BASE_DIR / 'figuras_cap3'
OUT_DIR.mkdir(exist_ok=True)
subjects = load_subjects(base_dir=BASE_DIR, n_points=N_12_DAYS)

grupo = 'DBT2'
sujeto = 5
dia = 0
G = subjects[grupo][sujeto][day_slice(dia, 0, 24)]
v = centered_velocity(G)
vc = conditioned_velocity(v, kappa=1.0)
t = time_axis(len(G), unit='hours')

fig, axes = plt.subplots(2, 1, figsize=(10, 6.5), sharex=True)
axes[0].plot(t, G, linewidth=1.8)
axes[0].set_ylabel('Glucosa (mg/dL)')
axes[0].set_title('Glucosa observada')
axes[0].grid(alpha=0.25)

axes[1].plot(t, v, linewidth=1.1, alpha=0.55, label='v(t) por diferencias centradas')
axes[1].plot(t, vc, linewidth=1.8, label=r'$v_c(t)$ acondicionada')
axes[1].axhline(0, linestyle='--', linewidth=1)
axes[1].set_xlabel('Tiempo (h)')
axes[1].set_ylabel('mg/dL/min')
axes[1].set_title('Velocidad de cambio acondicionada')
axes[1].grid(alpha=0.25)
axes[1].legend()

plt.tight_layout()
plt.savefig(OUT_DIR / 'figura_3_2_1_velocidad_acondicionada.png', dpi=300)
plt.show()
