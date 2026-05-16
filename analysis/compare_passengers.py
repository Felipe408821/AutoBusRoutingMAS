import os
import glob
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import StringIO
from itertools import combinations
from typing import Dict, Tuple, Optional, List

# Columnas de tiempo para análisis
COLUMNAS_TIEMPO = ['tiempo_espera', 'tiempo_viaje', 'tiempo_transbordo', 'tiempo_total']
# Columnas de métricas para análisis
COLUMNAS_METRICAS = ['tiempo_espera_promedio', 'tiempo_viaje_promedio', 'tiempo_total_promedio',
                    'tiempo_total_maximo', 'tiempo_total_minimo', 'tiempo_total_mediana',
                    'desviacion_tiempo_total', 'desviacion_tiempo_total_promedio']
RUTA_PASAJEROS = "analysis_results/passengers/"

# Configuración de estilos para gráficos
sns.set_theme(style="whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)


def analizar_csv_personalizado(ruta_archivo: str) -> pd.DataFrame:
    """Analiza un archivo CSV personalizado con resultados de pasajeros y lo convierte en un DataFrame."""
    try:
        with open(ruta_archivo, 'r') as archivo:
            lineas = [linea for linea in archivo if linea.strip().startswith("'],['")]

        if not lineas:
            print(f"Advertencia: No se encontraron datos de pasajeros en {ruta_archivo}")
            return pd.DataFrame()

        # Procesar líneas eficientemente
        lineas_limpias = []
        for linea in lineas:
            linea_limpia = (linea.replace("'],['", "")
                          .replace("'", "")
                          .replace(" ", "")
                          .replace("','", "")
                          .replace("\n", "").strip())
            lineas_limpias.append(linea_limpia)

        # Crear DataFrame desde las líneas limpias
        df = pd.read_csv(StringIO("\n".join(lineas_limpias)), header=None)
        df.drop(columns=[5], inplace=True, errors='ignore')

        if len(df.columns) < 4:
            print(f"Advertencia: Columnas insuficientes en {ruta_archivo}")
            return pd.DataFrame()

        df.columns = ['pasajero', 'tiempo_espera', 'tiempo_viaje', 'tiempo_transbordo', 'tiempo_total']

        # Convertir columnas numéricas eficientemente
        for col in COLUMNAS_TIEMPO:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        return df

    except Exception as e:
        print(f"Error procesando {ruta_archivo}: {str(e)}")
        return pd.DataFrame()


def calcular_metricas(df: pd.DataFrame, etiqueta: str) -> Dict:
    """Calcula métricas para un DataFrame individual."""
    if df.empty:
        return {
            'etiqueta': etiqueta,
            'total_pasajeros': 0,
            'pasajeros_llegados': 0,
            'porcentaje_llegados': 0,
            **{col: None for col in COLUMNAS_METRICAS}
        }

    llegados = df[df['tiempo_total'] > 0]
    if llegados.empty:
        metricas = {
            'etiqueta': etiqueta,
            'total_pasajeros': len(df),
            'pasajeros_llegados': 0,
            'porcentaje_llegados': 0,
            **{col: None for col in COLUMNAS_METRICAS}
        }
    else:
        metricas = {
            'etiqueta': etiqueta,
            'total_pasajeros': len(df),
            'pasajeros_llegados': len(llegados),
            'porcentaje_llegados': (len(llegados) / len(df)) * 100,
            'tiempo_espera_promedio': llegados['tiempo_espera'].mean(),
            'tiempo_viaje_promedio': llegados['tiempo_viaje'].mean(),
            'tiempo_transbordo_promedio': llegados['tiempo_transbordo'].mean(),
            'tiempo_total_promedio': llegados['tiempo_total'].mean(),
            'tiempo_total_maximo': llegados['tiempo_total'].max(),
            'tiempo_total_minimo': llegados['tiempo_total'].min(),
            'desviacion_tiempo_total': llegados['tiempo_total'].std(),
            'tiempo_total_mediana': llegados['tiempo_total'].median()
        }
    return metricas


def procesar_archivos_modelo(patron_archivos: str, nombre_modelo: str) -> Tuple[Optional[Dict], Optional[pd.DataFrame]]:
    """Procesa todos los archivos de un modelo y calcula métricas agregadas."""
    todos_archivos = glob.glob(patron_archivos)
    if not todos_archivos:
        print(f"Advertencia: No se encontraron archivos para el patrón {patron_archivos}")
        return None, None

    todas_metricas = [calcular_metricas(analizar_csv_personalizado(archivo), f"{nombre_modelo} - Ejecución") for archivo in todos_archivos]
    df_metricas = pd.DataFrame(todas_metricas)

    if df_metricas.empty:
        return None, None

    metricas_agregadas = {
        'etiqueta': nombre_modelo,
        'total_pasajeros': df_metricas['total_pasajeros'].mean(),
        'pasajeros_llegados': df_metricas['pasajeros_llegados'].mean(),
        'porcentaje_llegados': df_metricas['porcentaje_llegados'].mean(),
        'tiempo_espera_promedio': df_metricas['tiempo_espera_promedio'].mean(),
        'tiempo_viaje_promedio': df_metricas['tiempo_viaje_promedio'].mean(),
        'tiempo_transbordo_promedio': df_metricas['tiempo_transbordo_promedio'].mean(),
        'tiempo_total_promedio': df_metricas['tiempo_total_promedio'].mean(),
        'tiempo_total_maximo': df_metricas['tiempo_total_maximo'].max(),
        'tiempo_total_minimo': df_metricas['tiempo_total_minimo'].min(),
        'desviacion_tiempo_total': df_metricas['desviacion_tiempo_total'].mean(),
        'tiempo_total_mediana': df_metricas['tiempo_total_mediana'].mean(),
        'num_ejecuciones': len(todos_archivos),
        'desviacion_porcentaje_llegados': df_metricas['porcentaje_llegados'].std(),
        'desviacion_tiempo_total_promedio': df_metricas['tiempo_total_promedio'].std()
    }

    return metricas_agregadas, df_metricas


def comparar_multiples_modelos(patrones_modelos: Dict[str, str]) -> Tuple[Optional[pd.DataFrame], Optional[Dict]]:
    """Compara múltiples modelos dados como {nombre_modelo: patron_archivos}."""
    resultados = [(nombre_modelo, procesar_archivos_modelo(patron, nombre_modelo))
               for nombre_modelo, patron in patrones_modelos.items()]

    resultados_validos = [(nombre, agg, detalle) for nombre, (agg, detalle) in resultados if agg is not None]

    if not resultados_validos:
        print("Advertencia: No se encontraron datos válidos para ningún modelo")
        return None, None

    todas_metricas = [agg for _, agg, _ in resultados_validos]
    todos_detalles = {nombre: detalle for nombre, _, detalle in resultados_validos}

    return pd.DataFrame(todas_metricas).set_index('etiqueta'), todos_detalles


def generar_comparaciones_pareadas(df_comparacion: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """Genera comparaciones pareadas entre todos los modelos."""
    nombres_modelos = df_comparacion.index.tolist()
    return {
        f"{modelo2} vs {modelo1}": pd.DataFrame({
            'Diferencia': df_comparacion.loc[modelo2] - df_comparacion.loc[modelo1],
            '% Cambio': (df_comparacion.loc[modelo2] - df_comparacion.loc[modelo1]) /
                        df_comparacion.loc[modelo1].abs() * 100
        })
        for modelo1, modelo2 in combinations(nombres_modelos, 2)
    }


def _preparar_datos_graficos(df_comparacion: pd.DataFrame) -> pd.DataFrame:
    """Prepara datos para gráficos convirtiendo columnas de tiempo a minutos."""
    df_grafico = df_comparacion.copy()
    df_grafico[COLUMNAS_METRICAS] = df_grafico[COLUMNAS_METRICAS] / 60
    df_grafico['desviacion_tiempo_total_promedio_min'] = df_grafico['desviacion_tiempo_total_promedio'] / 60
    return df_grafico


def _guardar_grafico(fig: plt.Figure, nombre_archivo: str) -> None:
    """Función auxiliar para guardar gráficos consistentemente."""
    fig.savefig(f'{RUTA_PASAJEROS}{nombre_archivo}', dpi=300, bbox_inches='tight')
    plt.close(fig)


def graficar_metrica_individual(df_grafico: pd.DataFrame, metrica: str, etiqueta_y: str,
                       paleta: List[str], nombre_archivo: str,
                       barra_error: Optional[str] = None) -> None:
    """Función genérica para graficar una métrica individual."""
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.barplot(data=df_grafico.reset_index(), x='etiqueta', y=metrica,
                hue='etiqueta', palette=paleta, ax=ax, legend=False)

    if barra_error:
        ax.errorbar(x=range(len(df_grafico)), y=df_grafico[metrica],
                    yerr=df_grafico[barra_error], fmt='none', color='red', capsize=5)

    ax.set_ylabel(etiqueta_y)
    ax.set_xlabel("")
    ax.tick_params(axis='x', rotation=45)
    _guardar_grafico(fig, nombre_archivo)


def graficar_metricas_agrupadas(df_grafico: pd.DataFrame, metricas: List[str],
                         paleta: Dict[str, str], etiqueta_y: str,
                         etiquetas_leyenda: List[str], nombre_archivo: str) -> None:
    """Grafica métricas agrupadas con leyenda personalizada."""
    fig, ax = plt.subplots(figsize=(12, 6))
    datos_derretidos = df_grafico.reset_index()[['etiqueta'] + metricas].melt(id_vars='etiqueta')
    sns.barplot(data=datos_derretidos, x='etiqueta', y='value', hue='variable',
                palette=paleta, ax=ax)

    ax.set_ylabel(etiqueta_y)
    ax.set_xlabel("")
    ax.tick_params(axis='x', rotation=45)

    # Leyenda personalizada
    handles, _ = ax.get_legend_handles_labels()
    ax.legend(handles=handles, labels=etiquetas_leyenda, loc='upper left')
    _guardar_grafico(fig, nombre_archivo)

def graficar_metrica_individual_1(df_grafico: pd.DataFrame, metrica: str, etiqueta_y: "",
                                paleta: List[str], nombre_archivo: str,
                                barra_error: Optional[str] = None) -> None:
    """Genera una visualización estilizada con valores en azul y etiquetas de modelos rotadas."""
    df_plot = df_grafico.reset_index()

    # Extraer datos
    modelos = df_plot['etiqueta'].tolist()
    valores = [f"{v:.2f}" for v in df_plot[metrica]]

    # Color fijo para los valores
    color_valores = "#003366"  # Azul oscuro elegante

    # Crear figura con tamaño dinámico
    fig, ax = plt.subplots(figsize=(len(modelos)*2.2, 3))

    # Limpiar ejes
    ax.axis("off")

    # Dibujar cada valor y modelo
    for i, (modelo, valor) in enumerate(zip(modelos, valores)):
        ax.text(i, 0.6, valor, ha='center', va='bottom',
                fontsize=14, fontweight='bold', color=color_valores)
        ax.text(i, 0.4, modelo, ha='center', va='top',
                fontsize=11, rotation=45, color="#333333")

    # Etiqueta general como título a la izquierda
    if etiqueta_y:
        ax.text(-0.5, 1.1, etiqueta_y, fontsize=14, fontweight='bold', ha='left', color="#000000")

    # Ajuste de límites y espaciado
    ax.set_xlim(-0.5, len(modelos)-0.5)
    ax.set_ylim(0, 1.2)

    plt.tight_layout()
    plt.savefig(nombre_archivo, dpi=300, bbox_inches='tight')
    plt.close()

def graficar_y_guardar_imagenes0(df_comparacion: pd.DataFrame) -> None:
    """Crea gráficos comparativos para múltiples modelos con tiempos en minutos."""
    df_grafico = _preparar_datos_graficos(df_comparacion)
    paleta = sns.blend_palette(["#171796", "#e6e8ec"], n_colors=2)
    paleta1 = sns.blend_palette(["#FF7700", "#CC3333"], n_colors=2)

    # Gráfico de porcentaje de llegada
    graficar_metrica_individual(df_grafico, 'porcentaje_llegados', 'Tasa de éxito',
                       paleta, 'tasa_exito.png', 'desviacion_porcentaje_llegados')
    graficar_metrica_individual_1(df_grafico, 'porcentaje_llegados', '',
                       paleta, 'tasa_exito.png', 'desviacion_porcentaje_llegados')

    # Gráfico de tiempo total promedio
    graficar_metrica_individual(df_grafico, 'tiempo_total_promedio', 'Minutos',
                       paleta, 'tiempos_promedio.png', 'desviacion_tiempo_total_promedio')

    # Gráfico de tiempo de espera vs tiempo de viaje
    graficar_metricas_agrupadas(df_grafico, ['tiempo_espera_promedio', 'tiempo_viaje_promedio'],
                         paleta1, 'Minutos',
                         ['Tiempo Espera', 'Tiempo Viaje'], 'esperavsviaje.png')

    # Gráfico de conteo de pasajeros
    graficar_metricas_agrupadas(df_grafico, ['total_pasajeros', 'pasajeros_llegados'],
                         {'total_pasajeros': '#171796', 'pasajeros_llegados': '#53cf5b'},
                         'Pasajeros', ['Total', 'Llegados'], 'procesados.png')


def graficar_y_guardar_imagenes1(detalles_modelos: Dict[str, pd.DataFrame],
                      nombres_modelos: List[str]) -> None:
    """Crea gráficos de comparación detallados."""
    # Obtener datos de la primera ejecución para cada modelo
    dfs_primer_ejecucion = {}
    for nombre in nombres_modelos:
        primer_archivo = glob.glob(patrones_modelos[nombre])[0]
        df = analizar_csv_personalizado(primer_archivo)
        df[COLUMNAS_TIEMPO] = df[COLUMNAS_TIEMPO] / 60  # Convertir a minutos
        dfs_primer_ejecucion[nombre] = df

    paleta = sns.blend_palette(["#171796", "#e6e8ec"], n_colors=2)

    # Gráfico de caja de tiempos totales
    fig, ax = plt.subplots(figsize=(12, 6))
    datos_grafico = pd.concat([df['tiempo_total'].rename(nombre)
                       for nombre, df in dfs_primer_ejecucion.items()], axis=1)
    sns.boxplot(data=datos_grafico, palette=paleta, ax=ax)
    ax.set_ylabel("Minutos")
    ax.set_xlabel("")
    ax.tick_params(axis='x', rotation=45)
    _guardar_grafico(fig, 'tiempo_box_plot.png')

    # Gráfico de porcentaje de transbordo
    fig, ax = plt.subplots(figsize=(12, 6))
    datos_transbordo = pd.DataFrame({
        'Modelo': list(dfs_primer_ejecucion.keys()),
        'Porcentaje': [(df['tiempo_transbordo'] > 0).mean() * 100
                   for df in dfs_primer_ejecucion.values()]
    })
    sns.barplot(x='Modelo', y='Porcentaje', data=datos_transbordo,
            palette=paleta, ax=ax)
    ax.set_ylim(0, 100)
    ax.tick_params(axis='x', rotation=45)
    ax.set_xlabel("")
    _guardar_grafico(fig, 'transbordo.png')


if __name__ == "__main__":
    os.makedirs(RUTA_PASAJEROS, exist_ok=True)

    patrones_modelos = {
        "BAS_01": "experimental_tests/BAS_01/*_passengers_results.csv",
        "BDI_01": "experimental_tests/BDI_01/*_passengers_results.csv",
        "BAS_02": "experimental_tests/BAS_02/*_passengers_results.csv",
        "BDI_02": "experimental_tests/BDI_02/*_passengers_results.csv",
        "BAS_03": "experimental_tests/BAS_03/*_passengers_results.csv",
        "BDI_03": "experimental_tests/BDI_03/*_passengers_results.csv",
        "BAS_01_IC": "experimental_tests/BAS_01_IC/*_passengers_results.csv",
        "BDI_01_IC": "experimental_tests/BDI_01_IC/*_passengers_results.csv",
        "BDI_01_DY": "experimental_tests/BDI_01_DY/*_passengers_results.csv"
    }

    df_comparacion, detalles_modelos = comparar_multiples_modelos(patrones_modelos)

    if df_comparacion is not None:
        print("\n=== Métricas Agregadas para Todos los Modelos ===")
        print(df_comparacion[['num_ejecuciones', 'total_pasajeros', 'pasajeros_llegados',
                         'porcentaje_llegados', 'desviacion_porcentaje_llegados',
                         'tiempo_total_promedio', 'desviacion_tiempo_total_promedio']])

        comparaciones_pareadas = generar_comparaciones_pareadas(df_comparacion)
        for nombre_comparacion, df_diferencias in comparaciones_pareadas.items():
            print(f"\n=== Comparación: {nombre_comparacion} ===")
            print(df_diferencias)

        graficar_y_guardar_imagenes0(df_comparacion)
        graficar_y_guardar_imagenes1(detalles_modelos, list(patrones_modelos.keys()))

        df_comparacion.to_csv(RUTA_PASAJEROS + 'detalles.csv')
        print("\nResultados guardados en " + RUTA_PASAJEROS + "detalles.csv'")