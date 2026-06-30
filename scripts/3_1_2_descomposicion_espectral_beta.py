from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from common_cap3 import load_subjects, savgol_trend, colored_noise_beta, time_axis, N_12_DAYS

BASE_DIR = Path('.').resolve()
OUT_DIR = BASE_DIR / 'figuras_cap3'
OUT_DIR.mkdir(exist_ok=True)
subjects = load_subjects(base_dir=BASE_DIR, n_points=N_12_DAYS)

# Ejemplo para la descomposición espectral. Cambiar grupo/sujeto si la figura del documento usó otro caso.
grupo = 'DBT2'
sujeto = 5
G = subjects[grupo][sujeto]
t = time_axis(len(G), unit='days')
trend = savgol_trend(G, window=51, polyorder=3)
r = G - trend
# El texto indica 0.01-0.4; con muestreo de 96 muestras/día equivale a 0.96-38.4 ciclos/día.
beta, f, pxx, fit = colored_noise_beta(r, fit_range=(0.96, 38.4))
slope, intercept, _ = fit

fig, axes = plt.subplots(3, 1, figsize=(10, 9), sharex=False)
axes[0].plot(t, G, linewidth=1.2, label='G(t)')
axes[0].plot(t, trend, linewidth=2.0, label='Tendencia Savitzky-Golay')
axes[0].set_ylabel('Glucosa (mg/dL)')
axes[0].set_title('A. Señal original y tendencia lenta')
axes[0].grid(alpha=0.25)
axes[0].legend()

axes[1].plot(t, r, linewidth=1.2)
axes[1].axhline(0, linestyle='--', linewidth=1)
axes[1].set_ylabel('r(t) (mg/dL)')
axes[1].set_title('B. Componente fluctuante')
axes[1].grid(alpha=0.25)

mask = (f > 0) & (pxx > 0)
axes[2].loglog(f[mask], pxx[mask], marker='o', markersize=3, linewidth=1.2, label='PSD Welch')
fit_mask = (f >= 0.96) & (f <= 38.4) & mask
if fit_mask.sum() >= 3:
    axes[2].loglog(f[fit_mask], 10 ** (intercept + slope * np.log10(f[fit_mask])), linewidth=2.0,
                   label=fr'Ajuste $\beta={beta:.2f}$')
axes[2].set_xlabel('Frecuencia (ciclos/día)')
axes[2].set_ylabel('PSD')
axes[2].set_title('C. Densidad espectral de potencia y ajuste log-log')
axes[2].grid(alpha=0.25, which='both')
axes[2].legend()

plt.tight_layout()
plt.savefig(OUT_DIR / 'figura_3_1_2_descomposicion_espectral_beta.png', dpi=300)
plt.show()
print(f'beta estimado para {grupo} sujeto {sujeto}: {beta:.4f}')
