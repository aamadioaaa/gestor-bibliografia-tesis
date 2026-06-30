# Códigos por sección — Capítulo 3

Este paquete contiene los códigos de Jupyter/Python para reproducir las figuras del Capítulo 3 actual: análisis espectral, DFA, velocidad, energía local, indicador S(t), wavelet para alba/ingestas, Lyapunov, plano H×C, OPTM y reconstrucción de espacio de fase.

No se incluye código de Ackerman, Bergman ni Lotka–Volterra.

## Archivos principales

- `codigos_capitulo3_figuras.ipynb`: notebook completo para Jupyter.
- `scripts/`: códigos separados por sección.
- `subject_S.zip`: datos NDBT2/sanos usados por los scripts.
- `subject_E.zip`: datos DBT2/enfermos usados por los scripts.

## Cómo ejecutar

Desde la carpeta del paquete:

```bash
jupyter notebook codigos_capitulo3_figuras.ipynb
```

O por consola:

```bash
python scripts/00_configuracion_y_carga_datos.py
python scripts/3_4_HxC.py
```

Las figuras se guardan automáticamente en `figuras_cap3/`.

## Datos faltantes o a confirmar

1. En `subject_E.zip` falta `subject_11_E.csv`; por eso hay 19 sujetos DBT2 y 20 NDBT2.
2. En el DOCX la ecuación visible de `S(t)` aparece vacía; se implementó `S(t)=v_c(t)·Ê(t)`. Si la versión final usa `S(t)=v_c(t)(1+Ê(t))`, cambiar el argumento `formula` en `metabolic_force()`.
3. El texto menciona el ajuste espectral 0.01–0.4; el código lo transforma a 0.96–38.4 ciclos/día porque el muestreo es de 96 muestras/día.
4. Los umbrales exactos de clasificación fuerte/moderada/posible para ingestas y alba pueden ajustarse en `classify_event()` y `detect_meal_like_events()`.
