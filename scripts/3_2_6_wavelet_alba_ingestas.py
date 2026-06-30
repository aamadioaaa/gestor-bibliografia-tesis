from pathlib import Path
import matplotlib.pyplot as plt
from common_cap3 import (
    load_subjects, metabolic_force, morlet_band_energy, detect_dawn,
    detect_meal_like_events, time_axis, FS_PER_DAY, N_12_DAYS
)

BASE_DIR = Path('.').resolve()
OUT_DIR = BASE_DIR / 'figuras_cap3'
OUT_DIR.mkdir(exist_ok=True)
subjects = load_subjects(base_dir=BASE_DIR, n_points=N_12_DAYS)

# Sujeto representativo usado para alba/ingestas. Cambiar a NDBT2 si corresponde al documento final.
grupo = 'DBT2'
sujeto = 5
G = subjects[grupo][sujeto]
S = metabolic_force(G, formula='vc_times_Ehat')['S']
t_days = time_axis(len(G), unit='days')

slow_energy, _, _ = morlet_band_energy(S, (3.0, 8.0))
fast_energy, _, _ = morlet_band_energy(S, (0.5, 2.0))
dawn = detect_dawn(G, S)
# min_score=15 reproduce 29 ventanas no solapadas para DBT2 sujeto 5 con estos datos y esta implementación.
meals = detect_meal_like_events(G, S, window_samples=10, min_delta_g=20, min_score=15)
print('Fenómeno del alba')
print(dawn)
print('\nEventos compatibles con ingesta')
print(meals)
print('\nConteo ingestas por clasificación')
print(meals['clasificacion'].value_counts() if not meals.empty else 'Sin eventos')
if grupo == 'DBT2' and sujeto == 5 and len(meals) != 29:
    print('ATENCIÓN: el texto menciona 29 ventanas; revisar fórmula exacta de S(t), umbrales y score si este número cambia.')

# Figura alba: 12 días continuos, G(t), S(t), energía wavelet lenta.
fig, axes = plt.subplots(3, 1, figsize=(15, 8.5), sharex=True)
axes[0].plot(t_days, G, linewidth=1.2)
axes[1].plot(t_days, S, linewidth=1.0)
axes[2].plot(t_days, slow_energy, linewidth=1.2)
axes[0].set_ylabel('G(t) mg/dL')
axes[1].set_ylabel('S(t)')
axes[2].set_ylabel('Energía lenta')
axes[2].set_xlabel('Tiempo (días)')
for ax in axes:
    ax.grid(alpha=0.22)
for _, row in dawn.iterrows():
    start = (row['dia'] - 1) + row['inicio_h'] / 24
    end = (row['dia'] - 1) + row['fin_h'] / 24
    for ax in axes:
        ax.axvspan(start, end, alpha=0.15)
    axes[0].text((start + end) / 2, axes[0].get_ylim()[1], row['clasificacion'], ha='center', va='top', fontsize=8, rotation=90)
axes[0].set_title(f'Fenómeno del alba en {grupo} sujeto {sujeto}')
plt.tight_layout()
plt.savefig(OUT_DIR / 'figura_3_2_6_1_alba_sujeto_5.png', dpi=300)
plt.show()

# Figura ingestas: 12 días continuos, G(t), S(t), energía wavelet rápida.
fig, axes = plt.subplots(3, 1, figsize=(15, 8.5), sharex=True)
axes[0].plot(t_days, G, linewidth=1.2)
axes[1].plot(t_days, S, linewidth=1.0)
axes[2].plot(t_days, fast_energy, linewidth=1.2)
axes[0].set_ylabel('G(t) mg/dL')
axes[1].set_ylabel('S(t)')
axes[2].set_ylabel('Energía rápida')
axes[2].set_xlabel('Tiempo (días)')
for ax in axes:
    ax.grid(alpha=0.22)
for _, row in meals.iterrows():
    start = row['inicio_idx'] / FS_PER_DAY
    end = row['fin_idx'] / FS_PER_DAY
    for ax in axes:
        ax.axvspan(start, end, alpha=0.13)
    axes[0].text((start + end) / 2, axes[0].get_ylim()[1], row['clasificacion'], ha='center', va='top', fontsize=7, rotation=90)
axes[0].set_title(f'Eventos compatibles con ingesta en {grupo} sujeto {sujeto}')
plt.tight_layout()
plt.savefig(OUT_DIR / 'figura_3_2_6_3_ingestas_sujeto_5.png', dpi=300)
plt.show()
