import re
import os
from collections import defaultdict
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple, Optional, Any

CONFIG = {
    'ruta_resultados': 'analysis_results/buses',
    'paleta_colores': ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'],
    'estilo_graficos': 'whitegrid',
    'orden_lineas': ['651A', '651B', '652A', '652B', 'L1', 'L2', 'DYNA', 'DYNB'],
    'orden_modelos': ['BAS_01', 'BDI_01', 'BAS_02', 'BDI_02', 'BAS_03', 'BDI_03', 'BAS_01_IC', 'BDI_01_IC', 'BDI_01_DY']
}


def configurar_entorno():
    """Configura el entorno para los gráficos y verifica estructura de directorios."""
    sns.set_theme(style=CONFIG['estilo_graficos'])
    plt.rcParams['figure.facecolor'] = 'white'
    os.makedirs(CONFIG['ruta_resultados'], exist_ok=True)


def leer_archivo(ruta_archivo: str) -> str:
    """Lee el archivo y retorna la línea de datos relevante de manera eficiente."""
    try:
        with open(ruta_archivo, 'r', encoding='utf-8') as f:
            for linea in f:
                if linea.strip():
                    ultima_linea = linea
            return ultima_linea.strip() if ultima_linea else ""
    except Exception as e:
        print(f"Error leyendo archivo {ruta_archivo}: {e}")
        return ""


def parsear_datos(linea_datos: str) -> Dict[str, Dict[str, List[str]]]:
    """Parsea la línea de datos que contiene todas las paradas de manera más eficiente."""
    data = defaultdict(dict)
    if not linea_datos:
        return data

    # Compilar expresiones regulares una sola vez
    patron_parada = re.compile(r"\['(\d+)',map\(\[(.*?)\]\)\](?:,|$)")
    patron_linea = re.compile(r"'([^']+)'::\[([^\]]+)\]")

    for parada_match in patron_parada.finditer(linea_datos):
        parada = parada_match.group(1)
        contenido = parada_match.group(2)

        for linea_match in patron_linea.finditer(contenido):
            linea = linea_match.group(1)
            horas = [h.strip(" '") for h in linea_match.group(2).split(',') if
                     re.match(r"\d{2}:\d{2}:\d{2}", h.strip(" '"))]

            if horas:
                data[parada][linea] = horas
    return data


def hora_a_segundos(hora_str: str) -> int:
    """Convierte string de hora a segundos desde medianoche de manera vectorizada."""
    h, m, s = map(int, hora_str.split(':'))
    return h * 3600 + m * 60 + s


def calcular_intervalos(horas: List[str]) -> List[float]:
    """Calcula los intervalos entre horas consecutivas en minutos de manera optimizada."""
    if len(horas) < 2:
        return []

    segundos = np.array([hora_a_segundos(h) for h in horas])
    segundos.sort()
    return np.diff(segundos) / 60.0


def calcular_metricas_parada_linea(horas: List[str]) -> Optional[Dict[str, Any]]:
    """Calcula métricas de frecuencia para una parada-línea específica."""
    if len(horas) < 2:
        return None

    intervalos = calcular_intervalos(horas)
    media = np.mean(intervalos)
    desviacion = np.std(intervalos)

    return {
        'total_pasos': len(horas),
        'intervalos': intervalos,
        'media_intervalo': media,
        'max_intervalo': np.max(intervalos),
        'min_intervalo': np.min(intervalos),
        'desviacion_estandar': desviacion,
        'regularidad': "Irregular" if desviacion > media * 0.3 else "Buena",
        'hora_primer_paso': min(horas),
        'hora_ultimo_paso': max(horas),
        'es_critica': desviacion > media * 0.5
    }


def calcular_metricas(datos: Dict) -> Tuple[Dict, Dict[str, int], set]:
    """Calcula métricas de frecuencia para cada parada-línea de manera optimizada."""
    metrics = defaultdict(dict)
    pasos_por_parada = defaultdict(int)
    lineas_presentes = set()

    for parada, lineas in datos.items():
        for linea, horas in lineas.items():
            lineas_presentes.add(linea)
            pasos_por_parada[parada] += len(horas)

            if len(horas) >= 2:
                metricas = calcular_metricas_parada_linea(horas)
                if metricas:
                    metrics[parada][linea] = metricas

    return metrics, pasos_por_parada, lineas_presentes


def calcular_metricas_agregadas(metrics: Dict) -> Dict[str, Dict]:
    """Calcula estadísticas agregadas por línea de autobús de manera vectorizada."""
    agregados = defaultdict(list)

    for parada in metrics:
        for linea, data in metrics[parada].items():
            agregados[linea].append({
                'media': data['media_intervalo'],
                'desviacion': data['desviacion_estandar'],
                'regularidad': data['regularidad'],
                'es_critica': data['es_critica']
            })

    resultados = {}
    for linea, datos_linea in agregados.items():
        medias = [d['media'] for d in datos_linea]
        desviaciones = [d['desviacion'] for d in datos_linea]

        resultados[linea] = {
            'media_global': np.mean(medias),
            'desviacion_global': np.mean(desviaciones),
            'max_global': max(d['media'] for d in datos_linea),
            'min_global': min(d['media'] for d in datos_linea),
            'paradas_irregulares': sum(1 for d in datos_linea if d['regularidad'] == "Irregular"),
            'total_paradas': len(datos_linea),
            'porcentaje_irregular': sum(1 for d in datos_linea if d['regularidad'] == "Irregular") / len(
                datos_linea) * 100,
            'paradas_criticas': sum(1 for d in datos_linea if d['es_critica'])
        }

    return resultados


def analizar_red(datos: Dict, metrics: Dict, pasos_por_parada: Dict, lineas_presentes: set) -> Dict:
    """Analiza la red completa para un modelo de manera optimizada."""
    resultados = {
        'general': {
            'total_paradas': len(datos),
            'total_lineas': len(lineas_presentes),
            'total_pasos_registrados': sum(pasos_por_parada.values()),
            'intervalo_promedio_red': np.mean([
                intervalo for parada in metrics for linea in metrics[parada]
                for intervalo in metrics[parada][linea]['intervalos']
            ]) if metrics else 0,
        },
        'problemas': {
            'paradas_criticas': [],
            'lineas_irregulares': defaultdict(int),
            'lineas_mas_frecuentes': [],
            'top_paradas_mas_pasos': sorted(
                pasos_por_parada.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }
    }

    # Identificar paradas críticas
    for parada in metrics:
        for linea, data in metrics[parada].items():
            if data['es_critica']:
                resultados['problemas']['paradas_criticas'].append({
                    'parada': parada,
                    'linea': linea,
                    'desviacion': data['desviacion_estandar'],
                    'media': data['media_intervalo']
                })

    # Calcular frecuencia por línea
    frecuencias = defaultdict(list)
    for parada in metrics:
        for linea, data in metrics[parada].items():
            frecuencias[linea].append(data['media_intervalo'])

    resultados['problemas']['lineas_mas_frecuentes'] = sorted(
        [(linea, np.mean(intervalos)) for linea, intervalos in frecuencias.items()],
        key=lambda x: x[1]
    )[:6]

    # Identificar líneas irregulares
    for linea in resultados['problemas']['lineas_mas_frecuentes']:
        total_paradas = sum(1 for p in metrics if linea[0] in metrics[p])
        irregulares = sum(
            1 for p in metrics if linea[0] in metrics[p] and metrics[p][linea[0]]['regularidad'] == "Irregular")

        if irregulares / total_paradas > 0.5:
            resultados['problemas']['lineas_irregulares'][
                linea[0]] = f"{irregulares}/{total_paradas} paradas irregulares"

    return resultados


def procesar_ejecucion(ruta_archivo: str) -> Optional[Dict]:
    """Procesa un archivo de ejecución completo."""
    try:
        linea_datos = leer_archivo(ruta_archivo)
        datos = parsear_datos(linea_datos)

        if not datos:
            print(f"Archivo sin datos válidos: {os.path.basename(ruta_archivo)}")
            return None

        metrics, pasos_por_parada, lineas_presentes = calcular_metricas(datos)
        resultados_agregados = calcular_metricas_agregadas(metrics)
        resultados_red = analizar_red(datos, metrics, pasos_por_parada, lineas_presentes)

        return {
            'agregados': resultados_agregados,
            'red': resultados_red,
            'nombre': os.path.splitext(os.path.basename(ruta_archivo))[0]
        }

    except Exception as e:
        print(f"Error procesando {os.path.basename(ruta_archivo)}: {e}")
        return None


def analizar_modelo(ruta_modelo: str) -> Optional[Dict]:
    """Analiza todas las ejecuciones de un modelo y genera reportes agregados."""
    nombre_modelo = os.path.basename(ruta_modelo.rstrip('/'))
    print(f"\nAnalizando modelo: {nombre_modelo}")

    archivos = [os.path.join(ruta_modelo, f) for f in os.listdir(ruta_modelo)
                if f.endswith('_service_frequency.csv')]

    if not archivos:
        print(f"No se encontraron archivos en {ruta_modelo}")
        return None

    resultados = [procesar_ejecucion(archivo) for archivo in archivos]
    resultados_validos = [r for r in resultados if r is not None]

    if not resultados_validos:
        print("No se pudieron procesar ejecuciones válidas")
        return None

    # Calcular promedios del modelo
    lineas_comunes = set().union(*[set(r['agregados'].keys()) for r in resultados_validos])

    promedios_modelo = {}
    for linea in lineas_comunes:
        datos_linea = [r['agregados'].get(linea, {}) for r in resultados_validos]
        medias = [d.get('media_global', 0) for d in datos_linea if 'media_global' in d]

        if medias:
            promedios_modelo[linea] = {
                'media_promedio': np.mean(medias),
                'media_desviacion': np.std(medias) if len(medias) > 1 else 0,
                'desviacion_promedio': np.mean([d.get('desviacion_global', 0) for d in datos_linea]),
                'irregularidad_promedio': np.mean([d.get('porcentaje_irregular', 0) for d in datos_linea]),
                'num_ejecuciones': len(medias),
                'min_media': min(medias),
                'max_media': max(medias),
                'paradas_criticas_promedio': np.mean([d.get('paradas_criticas', 0) for d in datos_linea])
            }

    # Calcular métricas de red promedio
    metricas_red = {
        'total_paradas': np.mean([r['red']['general']['total_paradas'] for r in resultados_validos]),
        'total_lineas': np.mean([r['red']['general']['total_lineas'] for r in resultados_validos]),
        'intervalo_promedio': np.mean([r['red']['general']['intervalo_promedio_red'] for r in resultados_validos]),
        'paradas_criticas_promedio': np.mean(
            [len(r['red']['problemas']['paradas_criticas']) for r in resultados_validos])
    }

    return {
        'nombre': nombre_modelo,
        'promedios': promedios_modelo,
        'metricas_red': metricas_red,
        'ejecuciones': len(resultados_validos)
    }


def generar_graficos_modelo(resultados: Dict):
    """Genera gráficos para un modelo individual."""
    nombre_modelo = resultados['nombre']
    datos_grafico = []

    for linea, datos in resultados['promedios'].items():
        datos_grafico.append({
            'Linea': linea,
            'Media_Intervalo': datos['media_promedio'],
            'Desviacion': datos['desviacion_promedio'],
            '%_Irregularidad': datos['irregularidad_promedio'],
            'Min_Media': datos['min_media'],
            'Max_Media': datos['max_media']
        })

    df = pd.DataFrame(datos_grafico).sort_values('Linea', key=lambda x: x.map(
        {v: i for i, v in enumerate(CONFIG['orden_lineas'])}))

    # Configurar gráficos
    sns.set_theme(style=CONFIG['estilo_graficos'])
    fig, axs = plt.subplots(2, 2, figsize=(15, 10))

    # Gráfico 1: Intervalos promedio por línea
    sns.barplot(x='Media_Intervalo', y='Linea', data=df, ax=axs[0, 0], color='b', alpha=0.6)
    axs[0, 0].errorbar(x=df['Media_Intervalo'], y=df['Linea'],
                       xerr=[df['Media_Intervalo'] - df['Min_Media'], df['Max_Media'] - df['Media_Intervalo']],
                       fmt='none', color='black', capsize=5)
    axs[0, 0].set_title('Intervalos Promedio por Línea')

    # Gráfico 2: Irregularidad por línea
    sns.barplot(x='%_Irregularidad', y='Linea', data=df.nlargest(10, '%_Irregularidad'),
                ax=axs[0, 1], palette='Reds_r')
    axs[0, 1].set_title('Top 10 Líneas más Irregulares')

    # Gráfico 3: Dispersión Media vs Desviación
    sns.scatterplot(x='Media_Intervalo', y='Desviacion', hue='Linea', data=df,
                    ax=axs[1, 0], s=100, palette='viridis')
    axs[1, 0].set_title('Relación Media-Desviación')

    # Gráfico 4: Métricas de red
    metricas = [
        ('Paradas', resultados['metricas_red']['total_paradas']),
        ('Líneas', resultados['metricas_red']['total_lineas']),
        ('Intervalo (min)', resultados['metricas_red']['intervalo_promedio']),
        ('Paradas críticas', resultados['metricas_red']['paradas_criticas_promedio'])
    ]
    nombres, valores = zip(*metricas)
    axs[1, 1].barh(nombres, [1] * 4, color='lightgray')
    for i, (nombre, valor) in enumerate(metricas):
        axs[1, 1].text(1.05, i, f"{nombre}: {valor:.1f}", va='center')
    axs[1, 1].set_title('Métricas de Red')
    axs[1, 1].axis('off')

    plt.suptitle(f"Análisis del Modelo {nombre_modelo}", y=1.02)
    plt.tight_layout()
    plt.savefig(f"{CONFIG['ruta_resultados']}/modelo_{nombre_modelo}.png", dpi=300, bbox_inches='tight')
    plt.close()


def generar_comparativa(resultados_modelos: Dict[str, Dict]):
    """Genera gráficos comparativos entre todos los modelos."""
    # Preparar datos
    datos_lineas = []
    metricas_modelos = []

    for nombre, datos in resultados_modelos.items():
        # Datos por línea
        for linea, metricas in datos['promedios'].items():
            datos_lineas.append({
                'Modelo': nombre,
                'Linea': linea,
                'Media_Intervalo': metricas['media_promedio'],
                '%_Irregularidad': metricas['irregularidad_promedio'],
                'Paradas_Criticas': metricas['paradas_criticas_promedio']
            })

        # Métricas agregadas
        metricas_modelos.append({
            'Modelo': nombre,
            'Paradas': datos['metricas_red']['total_paradas'],
            'Líneas': datos['metricas_red']['total_lineas'],
            'Intervalo_Promedio': datos['metricas_red']['intervalo_promedio'],
            'Paradas_Críticas': datos['metricas_red']['paradas_criticas_promedio'],
            'Consistencia': 100 - np.mean([m['irregularidad_promedio'] for m in datos['promedios'].values()])
        })

    df_lineas = pd.DataFrame(datos_lineas)
    df_metricas = pd.DataFrame(metricas_modelos).sort_values(
        'Modelo', key=lambda x: x.map({v: i for i, v in enumerate(CONFIG['orden_modelos'])})
    )

    # Gráfico 1: Heatmap de irregularidad
    plt.figure(figsize=(12, 8))
    heatmap_data = df_lineas.pivot_table(index='Linea', columns='Modelo', values='%_Irregularidad')
    heatmap_data = heatmap_data.reindex(index=CONFIG['orden_lineas'], columns=CONFIG['orden_modelos'])
    sns.heatmap(heatmap_data, cmap="YlOrRd", annot=True, fmt=".1f", cbar_kws={'label': '% Irregularidad'})
    plt.title('Irregularidad por Línea y Modelo')
    plt.tight_layout()
    plt.savefig(f"{CONFIG['ruta_resultados']}/heatmap_comparativo.png", dpi=300, bbox_inches='tight')
    plt.close()

    # Gráfico 2: Comparación de métricas clave
    plt.figure(figsize=(12, 6))
    df_melt = df_metricas.melt(id_vars='Modelo',
                               value_vars=['Intervalo_Promedio', 'Paradas_Críticas', 'Consistencia'],
                               var_name='Metrica', value_name='Valor')

    sns.barplot(x='Modelo', y='Valor', hue='Metrica', data=df_melt, palette=CONFIG['paleta_colores'][:3])
    plt.title('Comparación de Métricas Clave entre Modelos')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f"{CONFIG['ruta_resultados']}/metricas_comparativas.png", dpi=300, bbox_inches='tight')
    plt.close()


def main():
    """Función principal que coordina el análisis."""
    configurar_entorno()

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

    resultados = {}
    for ruta in modelos:
        if os.path.isdir(ruta):
            res = analizar_modelo(ruta)
            if res:
                resultados[res['nombre']] = res
                generar_graficos_modelo(res)
        else:
            print(f"Directorio no encontrado: {ruta}")

    if resultados:
        generar_comparativa(resultados)
        print("\nAnálisis completado. Resultados guardados en:", CONFIG['ruta_resultados'])


if __name__ == "__main__":
    main()
