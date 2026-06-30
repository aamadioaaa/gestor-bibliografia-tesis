from pathlib import Path
import matplotlib.pyplot as plt
from common_cap3 import (
    load_subjects, average_mutual_information, false_nearest_neighbors,
    delay_embed, N_12_DAYS
)

BASE_DIR = Path('.').resolve()
OUT_DIR = BASE_DIR / 'figuras_cap3'
OUT_DIR.mkdir(exist_ok=True)
subjects = load_subjects(base_dir=BASE_DIR, n_points=N_12_DAYS)

sujeto_ndbt2 = 1
sujeto_dbt2 = 5
G_s = subjects['NDBT2'][sujeto_ndbt2]
G_e = subjects['DBT2'][sujeto_dbt2]

fig, axes = plt.subplots(2, 3, figsize=(15, 8.5))
for G, grupo, col in [(G_s, 'NDBT2', 0), (G_e, 'DBT2', 1)]:
    lags, ami = average_mutual_information(G, max_lag=32, n_bins=16)
    axes[0, 0].plot(lags, ami, marker='o', markersize=3, linewidth=1.2, label=grupo)
    axes[0, 1].plot(lags[1:], -1 * (ami[1:] - ami[:-1]), marker='o', markersize=3, linewidth=1.2, label=grupo)
    ms, fnn = false_nearest_neighbors(G, tau=4, max_m=8)
    axes[0, 2].plot(ms, fnn, marker='o', markersize=4, linewidth=1.2, label=grupo)

axes[0, 0].set_title('A. AMI normalizada')
axes[0, 0].set_xlabel(r'$\tau_{emb}$ (muestras)')
axes[0, 0].set_ylabel('AMI normalizada')
axes[0, 1].set_title('B. Pérdida discreta de información')
axes[0, 1].set_xlabel(r'$\tau_{emb}$ (muestras)')
axes[0, 1].set_ylabel(r'$-\Delta$ AMI')
axes[0, 2].set_title('C. Falsos vecinos cercanos')
axes[0, 2].set_xlabel(r'$m_{emb}$')
axes[0, 2].set_ylabel('FNN (%)')
axes[0, 2].axhline(5, linestyle='--', linewidth=1)
for ax in axes[0, :]:
    ax.grid(alpha=0.25)
    ax.legend()

# Proyección 2D con tau_emb=4 para cada grupo.
for ax, G, title in [(axes[1, 0], G_s, f'D. Fase NDBT2 sujeto {sujeto_ndbt2}'), (axes[1, 1], G_e, f'E. Fase DBT2 sujeto {sujeto_dbt2}')]:
    tau = 4
    x0 = G[:-tau]
    x1 = G[tau:]
    ax.scatter(x0, x1, s=10, alpha=0.55)
    lim_min = min(x0.min(), x1.min())
    lim_max = max(x0.max(), x1.max())
    ax.plot([lim_min, lim_max], [lim_min, lim_max], linestyle='--', linewidth=1)
    ax.set_xlabel(r'$G_t$ (mg/dL)')
    ax.set_ylabel(r'$G_{t+\tau}$ (mg/dL)')
    ax.set_title(title)
    ax.grid(alpha=0.25)

# Proyección 3D simple del sujeto DBT2.
axes[1, 2].axis('off')
fig.delaxes(axes[1, 2])
ax3 = fig.add_subplot(2, 3, 6, projection='3d')
Y = delay_embed(G_e, m=3, tau=4)
ax3.plot(Y[:, 0], Y[:, 1], Y[:, 2], linewidth=0.7, alpha=0.75)
ax3.set_xlabel(r'$G_t$')
ax3.set_ylabel(r'$G_{t+\tau}$')
ax3.set_zlabel(r'$G_{t+2\tau}$')
ax3.set_title('F. Proyección 3D del embedding')

plt.tight_layout()
plt.savefig(OUT_DIR / 'figura_3_5_embedding_AMI_FNN_fase.png', dpi=300)
plt.show()
