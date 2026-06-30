from pathlib import Path
import numpy as np
import pandas as pd
from common_cap3 import load_subjects, N_12_DAYS

BASE_DIR = Path('.').resolve()
subjects = load_subjects(base_dir=BASE_DIR, n_points=N_12_DAYS)

print('Sujetos NDBT2 cargados:', sorted(subjects['NDBT2']))
print('Sujetos DBT2 cargados:', sorted(subjects['DBT2']))

faltantes_dbt2 = sorted(set(range(1, 21)) - set(subjects['DBT2']))
faltantes_ndbt2 = sorted(set(range(1, 21)) - set(subjects['NDBT2']))
if faltantes_dbt2:
    print('Faltan archivos DBT2:', faltantes_dbt2)
if faltantes_ndbt2:
    print('Faltan archivos NDBT2:', faltantes_ndbt2)

resumen = []
for grupo, data in subjects.items():
    for sid, g in data.items():
        resumen.append({
            'grupo': grupo,
            'sujeto': sid,
            'n_muestras': len(g),
            'media_glucosa': np.mean(g),
            'min_glucosa': np.min(g),
            'max_glucosa': np.max(g),
        })
resumen = pd.DataFrame(resumen)
print(resumen.head())
