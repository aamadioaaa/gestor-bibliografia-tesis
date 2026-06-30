"""
Funciones comunes para reproducir las figuras del Capítulo 3.
Datos esperados:
    - subject_S.zip: sujetos NDBT2 / sanos
    - subject_E.zip: sujetos DBT2 / enfermos
Cada CSV debe contener una columna llamada 'Glucosa'.
"""

from __future__ import annotations

import itertools
import os
import re
import zipfile
from pathlib import Path
from typing import Dict, Tuple, List

import numpy as np
import pandas as pd
from scipy.signal import savgol_filter, welch
from scipy.fft import dct, idct
from scipy.spatial import cKDTree
from scipy.stats import linregress, ttest_ind
from sklearn.metrics import mutual_info_score

DT_MIN = 15
DT_HOURS = DT_MIN / 60
FS_PER_DAY = int(24 * 60 / DT_MIN)  # 96 muestras/día
N_12_DAYS = 12 * FS_PER_DAY         # 1152 muestras


def _natural_subject_number(path: Path) -> int:
    match = re.search(r"subject_(\d+)_", path.name)
    return int(match.group(1)) if match else 10**9


def extract_zip_if_needed(zip_path: str | Path, out_dir: str | Path) -> Path:
    zip_path = Path(zip_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if not any(out_dir.glob("*.csv")):
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(out_dir)
    return out_dir


def load_subjects(
    s_zip: str | Path = "subject_S.zip",
    e_zip: str | Path = "subject_E.zip",
    base_dir: str | Path = ".",
    n_points: int | None = N_12_DAYS,
) -> Dict[str, Dict[int, np.ndarray]]:
    """Carga sujetos desde los ZIP y devuelve {'NDBT2': {id: G}, 'DBT2': {id: G}}."""
    base_dir = Path(base_dir)
    s_dir = extract_zip_if_needed(base_dir / s_zip, base_dir / "subject_S")
    e_dir = extract_zip_if_needed(base_dir / e_zip, base_dir / "subject_E")

    out = {"NDBT2": {}, "DBT2": {}}
    for group, folder, suffix in [("NDBT2", s_dir, "S"), ("DBT2", e_dir, "E")]:
        for csv_path in sorted(folder.glob(f"subject_*_{suffix}.csv"), key=_natural_subject_number):
            sid = _natural_subject_number(csv_path)
            df = pd.read_csv(csv_path)
            if "Glucosa" not in df.columns:
                raise ValueError(f"{csv_path.name} no tiene columna 'Glucosa'. Columnas: {df.columns.tolist()}")
            g = pd.to_numeric(df["Glucosa"], errors="coerce").dropna().to_numpy(dtype=float)
            if n_points is not None:
                g = g[:n_points]
            out[group][sid] = g
    return out


def time_axis(n: int, unit: str = "days") -> np.ndarray:
    minutes = np.arange(n) * DT_MIN
    if unit == "minutes":
        return minutes
    if unit == "hours":
        return minutes / 60
    if unit == "days":
        return minutes / (60 * 24)
    raise ValueError("unit debe ser 'minutes', 'hours' o 'days'.")


def day_slice(day: int, start_hour: float = 0, end_hour: float = 24) -> slice:
    start = day * FS_PER_DAY + int(round(start_hour / DT_HOURS))
    end = day * FS_PER_DAY + int(round(end_hour / DT_HOURS))
    return slice(start, end)


def savgol_trend(g: np.ndarray, window: int = 51, polyorder: int = 3) -> np.ndarray:
    g = np.asarray(g, dtype=float)
    window = min(window, len(g) if len(g) % 2 == 1 else len(g) - 1)
    if window < polyorder + 2:
        return pd.Series(g).rolling(5, center=True, min_periods=1).mean().to_numpy()
    if window % 2 == 0:
        window += 1
    return savgol_filter(g, window_length=window, polyorder=polyorder, mode="interp")


def colored_noise_beta(
    signal: np.ndarray,
    fs: float = FS_PER_DAY,
    nperseg: int = 256,
    fit_range: Tuple[float, float] = (0.5, 12.0),
) -> Tuple[float, np.ndarray, np.ndarray, Tuple[float, float, float]]:
    """Estima beta de P(f) ~ 1/f^beta por Welch y ajuste log-log.

    fs se expresa en muestras por día; por lo tanto f queda en ciclos/día.
    """
    x = np.asarray(signal, dtype=float)
    nperseg = min(nperseg, len(x))
    f, pxx = welch(x, fs=fs, nperseg=nperseg, noverlap=nperseg // 2, detrend="constant")
    mask = (f > 0) & np.isfinite(pxx) & (pxx > 0) & (f >= fit_range[0]) & (f <= fit_range[1])
    if mask.sum() < 3:
        return np.nan, f, pxx, (np.nan, np.nan, np.nan)
    slope, intercept, r, pvalue, stderr = linregress(np.log10(f[mask]), np.log10(pxx[mask]))
    beta = -slope
    return beta, f, pxx, (slope, intercept, r)


def dfa_alpha(
    x: np.ndarray,
    scales: np.ndarray | None = None,
    order: int = 1,
) -> Tuple[float, np.ndarray, np.ndarray, Tuple[float, float, float]]:
    """Detrended Fluctuation Analysis de orden polinómico dado."""
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    y = np.cumsum(x - np.mean(x))
    n = len(y)
    if scales is None:
        scales = np.unique(np.logspace(np.log10(8), np.log10(min(288, n // 4)), 24).astype(int))
    Fs = []
    valid_scales = []
    for s in scales:
        s = int(s)
        if s <= order + 2 or n // s < 4:
            continue
        nseg = n // s
        rms_vals = []
        for v in range(nseg):
            seg = y[v * s:(v + 1) * s]
            t = np.arange(s)
            coeff = np.polyfit(t, seg, order)
            trend = np.polyval(coeff, t)
            rms_vals.append(np.sqrt(np.mean((seg - trend) ** 2)))
        F = np.sqrt(np.mean(np.asarray(rms_vals) ** 2))
        if np.isfinite(F) and F > 0:
            Fs.append(F)
            valid_scales.append(s)
    valid_scales = np.asarray(valid_scales, dtype=float)
    Fs = np.asarray(Fs, dtype=float)
    if len(Fs) < 3:
        return np.nan, valid_scales, Fs, (np.nan, np.nan, np.nan)
    slope, intercept, r, pvalue, stderr = linregress(np.log10(valid_scales), np.log10(Fs))
    return slope, valid_scales, Fs, (slope, intercept, r)


def centered_velocity(g: np.ndarray, dt_min: float = DT_MIN) -> np.ndarray:
    g = np.asarray(g, dtype=float)
    v = np.empty_like(g, dtype=float)
    if len(g) < 3:
        return np.zeros_like(g, dtype=float)
    v[1:-1] = (g[2:] - g[:-2]) / (2 * dt_min)
    v[0] = (g[1] - g[0]) / dt_min
    v[-1] = (g[-1] - g[-2]) / dt_min
    return v


def conditioned_velocity(v: np.ndarray, kappa: float = 1.0) -> np.ndarray:
    v = np.asarray(v, dtype=float)
    sigma_v = np.nanstd(v)
    if sigma_v == 0 or not np.isfinite(sigma_v):
        return np.zeros_like(v)
    return sigma_v * np.tanh(kappa * v / sigma_v)


def local_energy(g: np.ndarray, window: int = 10) -> np.ndarray:
    s = pd.Series(np.asarray(g, dtype=float))
    return s.rolling(window=window, center=True, min_periods=2).var(ddof=0).bfill().ffill().to_numpy()


def dct_smooth_energy(e: np.ndarray, keep_fraction: float = 0.10) -> np.ndarray:
    e = np.asarray(e, dtype=float)
    coeff = dct(e, norm="ortho")
    keep = max(1, int(np.ceil(len(coeff) * keep_fraction)))
    filt = np.zeros_like(coeff)
    filt[:keep] = coeff[:keep]
    out = idct(filt, norm="ortho")
    return np.maximum(out, 0)


def metabolic_force(
    g: np.ndarray,
    window_energy: int = 10,
    keep_fraction: float = 0.10,
    kappa: float = 1.0,
    formula: str = "vc_times_Ehat",
) -> Dict[str, np.ndarray]:
    """Construye v(t), v_c(t), E(t), E_suav(t), E_hat(t) y S(t).

    formula='vc_times_Ehat' implementa S(t)=v_c(t)*E_hat(t), consistente con
    una ponderación por volatilidad acotada entre 0 y 1.
    Si el manuscrito final decide usar ganancia adaptativa, puede cambiarse a
    formula='vc_times_1_plus_Ehat', que implementa S(t)=v_c(t)*(1+E_hat(t)).
    """
    v = centered_velocity(g)
    vc = conditioned_velocity(v, kappa=kappa)
    e = local_energy(g, window=window_energy)
    e_s = dct_smooth_energy(e, keep_fraction=keep_fraction)
    denom = np.nanmax(e_s)
    e_hat = e_s / denom if denom and np.isfinite(denom) else np.zeros_like(e_s)
    if formula == "vc_times_Ehat":
        S = vc * e_hat
    elif formula == "vc_times_1_plus_Ehat":
        S = vc * (1 + e_hat)
    else:
        raise ValueError("formula debe ser 'vc_times_Ehat' o 'vc_times_1_plus_Ehat'.")
    return {"v": v, "vc": vc, "E": e, "E_smooth": e_s, "E_hat": e_hat, "S": S}


def morlet_band_energy(
    x: np.ndarray,
    period_hours: Tuple[float, float],
    n_periods: int = 24,
    w0: float = 6.0,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Energía tipo CWT-Morlet promediada en una banda de períodos.

    Implementación sin PyWavelets para facilitar uso en Jupyter estándar.
    Devuelve energía normalizada, matriz |coef|^2 y períodos en horas.
    """
    x = np.asarray(x, dtype=float)
    x0 = x - np.nanmean(x)
    periods_h = np.linspace(period_hours[0], period_hours[1], n_periods)
    powers = []
    for ph in periods_h:
        period_samples = ph / DT_HOURS
        scale = max(1.0, period_samples * w0 / (2 * np.pi))
        half = int(np.ceil(4 * scale))
        t = np.arange(-half, half + 1)
        wave = np.exp(1j * w0 * t / scale) * np.exp(-(t ** 2) / (2 * scale ** 2))
        wave -= wave.mean()
        norm = np.sqrt(np.sum(np.abs(wave) ** 2))
        if norm > 0:
            wave = wave / norm
        coef = np.convolve(x0, np.conj(wave[::-1]), mode="same")
        powers.append(np.abs(coef) ** 2)
    power = np.vstack(powers)
    band = np.nanmean(power, axis=0)
    if np.nanmax(band) > 0:
        band = band / np.nanmax(band)
    return band, power, periods_h


def positive_negative_areas(x: np.ndarray, dt_hours: float = DT_HOURS) -> Tuple[float, float, float]:
    x = np.asarray(x, dtype=float)
    pos = np.maximum(x, 0)
    neg = np.maximum(-x, 0)
    a_pos = np.nansum(pos) * dt_hours
    a_neg = np.nansum(neg) * dt_hours
    eps = 1e-12
    idx = (a_pos - a_neg) / (a_pos + a_neg + eps)
    return a_pos, a_neg, idx


def classify_event(delta_g: float, I_G: float, I_S: float, W: float, kind: str) -> str:
    if delta_g <= 0 or (I_G <= 0 and I_S <= 0):
        return "No compatible"
    if kind == "alba":
        if delta_g >= 50 and I_G > 0 and I_S > 0 and W >= 0.35:
            return "Fuerte"
        if delta_g >= 30 and (I_G > 0 or I_S > 0) and W >= 0.20:
            return "Moderada"
        return "Posible"
    if kind == "ingesta":
        if delta_g >= 120 and I_G > 0 and I_S > 0 and W >= 0.35:
            return "Fuerte"
        if delta_g >= 60 and I_S > 0 and W >= 0.20:
            return "Moderada"
        if delta_g >= 20 and (I_G > 0 or I_S > 0):
            return "Posible"
        return "No compatible"
    raise ValueError("kind debe ser 'alba' o 'ingesta'.")


def detect_dawn(g: np.ndarray, S: np.ndarray) -> pd.DataFrame:
    slow_energy, _, _ = morlet_band_energy(S, (3.0, 8.0))
    rows = []
    ndays = len(g) // FS_PER_DAY
    for day in range(ndays):
        sl = day_slice(day, 3, 8)
        gw = g[sl]
        sw = S[sl]
        ww = slow_energy[sl]
        if len(gw) == 0:
            continue
        delta_g = float(gw[-1] - gw[0])
        _, _, I_G = positive_negative_areas(gw - gw[0])
        _, _, I_S = positive_negative_areas(sw)
        W = float(np.nanmean(ww))
        rows.append({
            "dia": day + 1,
            "inicio_h": 3.0,
            "fin_h": 8.0,
            "DeltaG": delta_g,
            "I_G": I_G,
            "I_S": I_S,
            "W_lenta": W,
            "clasificacion": classify_event(delta_g, I_G, I_S, W, "alba"),
        })
    return pd.DataFrame(rows)


def detect_meal_like_events(
    g: np.ndarray,
    S: np.ndarray,
    window_samples: int = 10,
    min_delta_g: float = 20,
    min_score: float = 0.0,
) -> pd.DataFrame:
    fast_energy, _, _ = morlet_band_energy(S, (0.5, 2.0))
    candidates = []
    ndays = len(g) // FS_PER_DAY
    for day in range(ndays):
        day0 = day * FS_PER_DAY
        start_min = day0 + int(round(8 / DT_HOURS))
        start_max = day0 + int(round(21.5 / DT_HOURS))
        for start in range(start_min, min(start_max, day0 + FS_PER_DAY - window_samples) + 1):
            end = start + window_samples
            gw = g[start:end]
            sw = S[start:end]
            ww = fast_energy[start:end]
            delta_g = float(np.nanmax(gw - gw[0]))
            if delta_g < min_delta_g:
                continue
            _, _, I_G = positive_negative_areas(gw - gw[0])
            _, _, I_S = positive_negative_areas(sw)
            W = float(np.nanmean(ww))
            score = delta_g * max(I_G, 0) * max(I_S, 0) * (0.5 + W)
            if score <= min_score:
                continue
            label = classify_event(delta_g, I_G, I_S, W, "ingesta")
            if label == "No compatible":
                continue
            candidates.append({
                "dia": day + 1,
                "inicio_idx": start,
                "fin_idx": end,
                "inicio_h": (start - day0) * DT_HOURS,
                "fin_h": (end - day0) * DT_HOURS,
                "DeltaGmax": delta_g,
                "I_G": I_G,
                "I_S": I_S,
                "W_rapida": W,
                "score": score,
                "clasificacion": label,
            })
    # Selección greedy de ventanas no solapadas por día y por puntaje.
    selected = []
    for day in range(1, ndays + 1):
        day_cands = [c for c in candidates if c["dia"] == day]
        day_cands = sorted(day_cands, key=lambda r: r["score"], reverse=True)
        accepted = []
        for c in day_cands:
            overlaps = any(not (c["fin_idx"] <= a["inicio_idx"] or c["inicio_idx"] >= a["fin_idx"]) for a in accepted)
            if not overlaps:
                accepted.append(c)
        selected.extend(sorted(accepted, key=lambda r: r["inicio_idx"]))
    return pd.DataFrame(selected)


def ordinal_patterns(x: np.ndarray, D: int = 3, tau: int = 1) -> Tuple[np.ndarray, List[Tuple[int, ...]]]:
    x = np.asarray(x, dtype=float)
    perms = list(itertools.permutations(range(D)))
    perm_to_id = {p: i for i, p in enumerate(perms)}
    n = len(x) - (D - 1) * tau
    ids = []
    for t in range(max(0, n)):
        window = x[t:t + D * tau:tau]
        # mergesort es estable: conserva orden temporal ante empates.
        pattern = tuple(np.argsort(window, kind="mergesort"))
        ids.append(perm_to_id[pattern])
    return np.asarray(ids, dtype=int), perms


def permutation_distribution(x: np.ndarray, D: int = 3, tau: int = 1) -> np.ndarray:
    ids, perms = ordinal_patterns(x, D=D, tau=tau)
    counts = np.bincount(ids, minlength=len(perms)).astype(float)
    total = counts.sum()
    return counts / total if total > 0 else np.ones(len(perms)) / len(perms)


def shannon_entropy(p: np.ndarray) -> float:
    p = np.asarray(p, dtype=float)
    p = p[p > 0]
    return float(-np.sum(p * np.log(p)))


def h_complexity(p: np.ndarray) -> Tuple[float, float]:
    p = np.asarray(p, dtype=float)
    M = len(p)
    pe = np.ones(M) / M
    H = shannon_entropy(p) / np.log(M)
    js = shannon_entropy((p + pe) / 2) - 0.5 * shannon_entropy(p) - 0.5 * shannon_entropy(pe)
    delta = np.zeros(M); delta[0] = 1.0
    js_max = shannon_entropy((delta + pe) / 2) - 0.5 * shannon_entropy(delta) - 0.5 * shannon_entropy(pe)
    C = (js / js_max) * H if js_max > 0 else np.nan
    return H, C


def hx_c_bounds(M: int = 6, n_random: int = 25000, seed: int = 123) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Aproximación Monte Carlo de Cmin y Cmax para graficar la región accesible."""
    rng = np.random.default_rng(seed)
    Ps = rng.dirichlet(np.ones(M), size=n_random)
    HC = np.array([h_complexity(p) for p in Ps])
    H, C = HC[:, 0], HC[:, 1]
    bins = np.linspace(0, 1, 80)
    centers = 0.5 * (bins[:-1] + bins[1:])
    cmin = np.full(len(centers), np.nan)
    cmax = np.full(len(centers), np.nan)
    for i in range(len(centers)):
        m = (H >= bins[i]) & (H < bins[i + 1])
        if np.any(m):
            cmin[i] = np.nanmin(C[m])
            cmax[i] = np.nanmax(C[m])
    return centers, cmin, cmax


def optm_stationary_indicator(x: np.ndarray, D: int = 3, tau: int = 1) -> Tuple[float, np.ndarray, np.ndarray]:
    ids, perms = ordinal_patterns(x, D=D, tau=tau)
    M = len(perms)
    counts = np.zeros((M, M), dtype=float)
    for a, b in zip(ids[:-1], ids[1:]):
        counts[a, b] += 1
    row_sums = counts.sum(axis=1, keepdims=True)
    P = np.divide(counts, row_sums, out=np.ones_like(counts) / M, where=row_sums > 0)
    # vector estacionario: autovector izquierdo para autovalor 1
    w, v = np.linalg.eig(P.T)
    idx = np.argmin(np.abs(w - 1))
    stat = np.real(v[:, idx])
    stat = np.abs(stat)
    stat = stat / stat.sum() if stat.sum() > 0 else np.ones(M) / M
    return float(np.linalg.norm(stat)), P, stat


def classify_stat_ms(value: float, sane_max: float = 0.49, diabetic_min: float = 0.505) -> str:
    if value < sane_max:
        return "Sano"
    if value >= diabetic_min:
        return "Diabetes"
    return "Dudoso"


def delay_embed(x: np.ndarray, m: int = 4, tau: int = 4) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    n = len(x) - (m - 1) * tau
    if n <= 0:
        raise ValueError("Serie demasiado corta para ese m y tau.")
    return np.column_stack([x[i * tau:i * tau + n] for i in range(m)])


def lyapunov_rosenstein(
    x: np.ndarray,
    m: int = 4,
    tau: int = 4,
    min_tsep: int = FS_PER_DAY,
    max_k: int = 40,
    fit_k: Tuple[int, int] = (1, 12),
) -> Tuple[float, float, np.ndarray, np.ndarray]:
    """Estimador tipo Rosenstein. Devuelve lambda en h^-1 y tiempo Lyapunov en h."""
    X = delay_embed(x, m=m, tau=tau)
    N = len(X)
    tree = cKDTree(X)
    neigh = np.full(N, -1, dtype=int)
    for i in range(N):
        k = 2
        while True:
            dists, idxs = tree.query(X[i], k=min(k, N))
            idxs = np.atleast_1d(idxs)
            valid = idxs[np.abs(idxs - i) >= min_tsep]
            if len(valid) > 0:
                neigh[i] = valid[0]
                break
            k *= 2
            if k > N:
                break
    ks = np.arange(max_k + 1)
    log_div = []
    eps = 1e-12
    for kk in ks:
        vals = []
        for i, j in enumerate(neigh):
            if j < 0:
                continue
            if i + kk < N and j + kk < N:
                d = np.linalg.norm(X[i + kk] - X[j + kk])
                if d > eps and np.isfinite(d):
                    vals.append(np.log(d))
        log_div.append(np.nanmean(vals) if vals else np.nan)
    log_div = np.asarray(log_div, dtype=float)
    a, b = fit_k
    mask = (ks >= a) & (ks <= b) & np.isfinite(log_div)
    if mask.sum() < 3:
        return np.nan, np.nan, ks * DT_HOURS, log_div
    slope, intercept, r, pvalue, stderr = linregress(ks[mask] * DT_HOURS, log_div[mask])
    lam_h = slope
    T_L = 1 / lam_h if lam_h > 0 else np.inf
    return float(lam_h), float(T_L), ks * DT_HOURS, log_div


def quantile_binning(x: np.ndarray, n_bins: int = 16) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    qs = np.unique(np.quantile(x, np.linspace(0, 1, n_bins + 1)))
    if len(qs) <= 2:
        return np.zeros_like(x, dtype=int)
    return np.digitize(x, qs[1:-1], right=False)


def average_mutual_information(x: np.ndarray, max_lag: int = 32, n_bins: int = 16) -> Tuple[np.ndarray, np.ndarray]:
    xb = quantile_binning(x, n_bins=n_bins)
    amis = []
    lags = np.arange(1, max_lag + 1)
    for lag in lags:
        amis.append(mutual_info_score(xb[:-lag], xb[lag:]))
    amis = np.asarray(amis, dtype=float)
    if np.nanmax(amis) > 0:
        amis = amis / np.nanmax(amis)
    return lags, amis


def false_nearest_neighbors(
    x: np.ndarray,
    tau: int = 4,
    max_m: int = 8,
    rtol: float = 10.0,
    atol: float = 2.0,
) -> Tuple[np.ndarray, np.ndarray]:
    x = np.asarray(x, dtype=float)
    std_x = np.nanstd(x)
    ms, fnn = [], []
    for m in range(1, max_m + 1):
        Xm = delay_embed(x, m=m, tau=tau)
        Xm1 = delay_embed(x, m=m + 1, tau=tau)
        N = min(len(Xm), len(Xm1))
        Xm = Xm[:N]
        Xm1 = Xm1[:N]
        tree = cKDTree(Xm)
        dists, idxs = tree.query(Xm, k=2)
        nn = idxs[:, 1]
        dist_m = dists[:, 1]
        dist_m = np.maximum(dist_m, 1e-12)
        extra = np.abs(Xm1[:, -1] - Xm1[nn, -1])
        dist_m1 = np.linalg.norm(Xm1 - Xm1[nn], axis=1)
        false = (extra / dist_m > rtol) | (dist_m1 / std_x > atol)
        ms.append(m)
        fnn.append(100 * np.mean(false))
    return np.asarray(ms), np.asarray(fnn)
