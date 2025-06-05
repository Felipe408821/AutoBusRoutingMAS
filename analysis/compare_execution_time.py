import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from glob import glob
from matplotlib.ticker import ScalarFormatter
from typing import List, Dict, Optional

# Configuración global
CONFIG = {
    'ruta_resultados': 'analysis_results/execution_time',
    'paleta_colores': 'dark:#171796',
    'estilo_graficos': 'whitegrid',
    'formato_numeros_grandes': lambda x: f"{x:.4e}" if x > 1e4 else f"{x:.4f}"
}


def configurar_entorno():
    """Configura el entorno para los gráficos y verifica estructura de directorios."""
    sns.set_theme(style=CONFIG['estilo_graficos'])
    plt.rcParams['figure.facecolor'] = 'white'
    os.makedirs(CONFIG['ruta_resultados'], exist_ok=True)


def procesar_archivo_tiempo(archivo: str) -> Optional[tuple]:
    """Procesa un archivo de tiempo de ejecución y devuelve (segundos, ciclos) o None si hay error."""
    try:
        with open(archivo, 'r') as f:
            lineas = f.readlines()
            if len(lineas) >= 2:
                datos_str = lineas[1].strip().strip('[]')
                segundos, ciclos = map(float, datos_str.split(','))
                return segundos, ciclos
    except Exception as e:
        print(f"Error procesando {os.path.basename(archivo)}: {e}")
    return None


def calcular_metricas_modelo(carpeta: str) -> Dict:
    """Calcula métricas de rendimiento para un modelo específico."""
    if not os.path.exists(carpeta):
        raise FileNotFoundError(f"Carpeta no encontrada: {carpeta}")

    archivos_tiempo = glob(os.path.join(carpeta, '*_execution_time.csv'))
    if not archivos_tiempo:
        raise ValueError(f"No se encontraron archivos de tiempo en {carpeta}")

    datos = [procesar_archivo_tiempo(archivo) for archivo in archivos_tiempo]
    datos_validos = [d for d in datos if d is not None]

    if not datos_validos:
        raise ValueError(f"No hay datos válidos en {carpeta}")

    tiempos, ciclos = zip(*datos_validos)
    ciclos_por_seg = np.divide(ciclos, tiempos, where=np.array(tiempos) > 0)

    return {
        'Modelo': os.path.basename(carpeta),
        'Tiempo Promedio (s)': np.mean(tiempos),
        'Tiempo Mínimo (s)': np.min(tiempos),
        'Tiempo Máximo (s)': np.max(tiempos),
        'Desviación Tiempo (s)': np.std(tiempos),
        'Ciclos Promedio': np.mean(ciclos),
        'Ciclos Mínimo': np.min(ciclos),
        'Ciclos Máximo': np.max(ciclos),
        'Desviación Ciclos': np.std(ciclos),
        'Ciclos/s Promedio': np.mean(ciclos_por_seg),
        'Ciclos/s Mínimo': np.min(ciclos_por_seg),
        'Ciclos/s Máximo': np.max(ciclos_por_seg),
        'Número de Ejecuciones': len(tiempos)
    }


def crear_grafico_comparativo(df: pd.DataFrame, col_y: str, titulo: str, archivo_salida: str):
    """Crea un gráfico de barras comparativo con barras de error."""
    plt.figure(figsize=(12, 6))
    ax = sns.barplot(
        x='Modelo',
        y=col_y,
        data=df,
        hue='Modelo',
        palette=CONFIG['paleta_colores'],
        legend=False,
        errorbar=None
    )

    # Configurar barras de error
    for i, modelo in enumerate(df['Modelo']):
        min_val = df.loc[df['Modelo'] == modelo, col_y.replace('Promedio', 'Mínimo')].values[0]
        max_val = df.loc[df['Modelo'] == modelo, col_y.replace('Promedio', 'Máximo')].values[0]
        avg_val = df.loc[df['Modelo'] == modelo, col_y].values[0]

        plt.errorbar(
            x=i,
            y=avg_val,
            yerr=[[avg_val - min_val], [max_val - avg_val]],
            fmt='none',
            color='red',
            capsize=5
        )

    # Configuración del gráfico
    plt.xlabel('')
    plt.ylabel(titulo.split('(')[0].strip(), fontsize=12)
    plt.title(titulo, fontsize=14)
    plt.xticks(rotation=45, ha='right')

    # Formateo de ejes para números grandes
    if any(df[col_y] > 1e4):
        ax.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
        plt.ticklabel_format(style='sci', axis='y', scilimits=(0, 0))

    # Anotar valores en las barras
    for p in ax.patches:
        ax.annotate(
            CONFIG['formato_numeros_grandes'](p.get_height()),
            (p.get_x() + p.get_width() / 2., p.get_height()),
            ha='center', va='center',
            xytext=(0, 10),
            textcoords='offset points',
            fontsize=10
        )

    plt.tight_layout()
    plt.savefig(os.path.join(CONFIG['ruta_resultados'], archivo_salida), dpi=300, bbox_inches='tight')
    plt.close()


def generar_graficos(df: pd.DataFrame):
    """Genera todos los gráficos de comparación."""
    crear_grafico_comparativo(df, 'Tiempo Promedio (s)', 'Tiempo de Ejecución Promedio (s)', 'tiempos_ejecucion.png')
    crear_grafico_comparativo(df, 'Ciclos Promedio', 'Ciclos de Ejecución Promedio', 'ciclos_ejecucion.png')
    crear_grafico_comparativo(df, 'Ciclos/s Promedio', 'Eficiencia (Ciclos/segundo)', 'eficiencia_ejecucion.png')


def analizar_resultados(df: pd.DataFrame):
    """Realiza análisis comparativo de los resultados."""
    print("\n" + "=" * 100)
    print("RESULTADOS COMPARATIVOS DETALLADOS".center(100))
    print("=" * 100)
    print(df.to_string(index=False, float_format=CONFIG['formato_numeros_grandes']))

    print("\n" + "=" * 100)
    print("ANÁLISIS COMPARATIVO".center(100))
    print("=" * 100)

    mas_rapido = df.loc[df['Tiempo Promedio (s)'].idxmin()]
    print(f"\nModelo más rápido: {mas_rapido['Modelo']} ({mas_rapido['Tiempo Promedio (s)']:.4f} s)")

    menos_ciclos = df.loc[df['Ciclos Promedio'].idxmin()]
    print(f"Modelo con menos ciclos: {menos_ciclos['Modelo']} ({menos_ciclos['Ciclos Promedio']:.4e})")

    mas_eficiente = df.loc[df['Ciclos/s Promedio'].idxmax()]
    print(f"Modelo más eficiente: {mas_eficiente['Modelo']} ({mas_eficiente['Ciclos/s Promedio']:.4e} ciclos/s)")

    correlacion = df['Tiempo Promedio (s)'].corr(df['Ciclos Promedio'])
    print(f"\nCorrelación tiempo-ciclos: {correlacion:.2f}")

    if abs(correlacion) > 0.7:
        print("  - Fuerte relación lineal entre tiempo y ciclos")
    elif abs(correlacion) > 0.3:
        print("  - Relación moderada entre tiempo y ciclos")
    else:
        print("  - Relación débil entre tiempo y ciclos")


def comparar_modelos(carpetas_modelos: List[str]) -> Optional[pd.DataFrame]:
    """Compara múltiples modelos y devuelve DataFrame con resultados."""
    configurar_entorno()
    resultados = []

    for carpeta in carpetas_modelos:
        try:
            resultados.append(calcular_metricas_modelo(carpeta))
        except Exception as e:
            print(f"Error procesando {carpeta}: {e}")

    if not resultados:
        print("Error: No se pudieron procesar modelos")
        return None

    #df = pd.DataFrame(resultados).sort_values('Tiempo Promedio (s)')
    df = pd.DataFrame(resultados)
    generar_graficos(df)
    analizar_resultados(df)

    return df


if __name__ == "__main__":
    os.makedirs(CONFIG['ruta_resultados'], exist_ok=True)

    modelos = [
        "experimental_tests/BAS_01",
        "experimental_tests/BDI_01",
        "experimental_tests/BAS_02",
        "experimental_tests/BDI_02",
        "experimental_tests/BAS_03",
        "experimental_tests/BDI_03",
        "experimental_tests/BAS_01_IC",
        "experimental_tests/BDI_01_IC",
        "experimental_tests/BDI_01_DY"
    ]

    modelos_validos = [m for m in modelos if os.path.exists(m)]

    if modelos_validos:
        print(f"\nComparando {len(modelos_validos)} modelos...")
        resultados = comparar_modelos(modelos_validos)
    else:
        print("Error: No se encontraron carpetas de modelos válidas")