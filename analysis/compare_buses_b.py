import re
from collections import defaultdict
import matplotlib.pyplot as plt
import os
import statistics
from datetime import datetime
import numpy as np


def leer_archivo(ruta_archivo):
    """Lee el archivo y retorna la línea de datos relevante"""
    with open(ruta_archivo, 'r', encoding='utf-8') as f:
        lineas = f.readlines()
        return lineas[-1].strip() if lineas else ""


def parse_custom_data(linea_datos):
    """Parsea la línea de datos que contiene todas las paradas"""
    data = defaultdict(dict)
    linea_datos = linea_datos.strip().strip("logs_service_frequency").strip()
    patron_parada = re.compile(r"\['(\d+)',map\(\[(.*?)\]\)\](?:,|$)")

    for match in patron_parada.finditer(linea_datos):
        parada = match.group(1)
        contenido = match.group(2)
        patron_linea = re.compile(r"'([^']+)'::\[([^\]]+)\]")

        for linea_match in patron_linea.finditer(contenido):
            linea = linea_match.group(1)
            horas_str = linea_match.group(2)
            horas = [h.strip().strip("'") for h in horas_str.split(',')]
            horas = [h for h in horas if re.match(r"\d{2}:\d{2}:\d{2}", h)]

            if horas:
                data[parada][linea] = horas

    return data


def hora_a_segundos(hora_str):
    """Convierte string de hora a segundos desde medianoche"""
    h, m, s = map(int, hora_str.split(':'))
    return h * 3600 + m * 60 + s


def calcular_intervalos(horas):
    """Calcula los intervalos entre horas consecutivas en minutos"""
    segundos = sorted(hora_a_segundos(h) for h in horas)
    return [(segundos[i] - segundos[i - 1]) / 60.0 for i in range(1, len(segundos))]


def calcular_metricas(datos):
    """Calcula métricas de frecuencia para cada parada-línea"""
    metrics = defaultdict(dict)
    paradas_irregulares = defaultdict(list)  # Nuevo: para registrar paradas irregulares

    for parada in datos:
        for linea in datos[parada]:
            horas = datos[parada][linea]
            if len(horas) >= 2:
                intervalos = calcular_intervalos(horas)
                media = sum(intervalos) / len(intervalos)
                varianza = sum((x - media) ** 2 for x in intervalos) / len(intervalos)
                desviacion = varianza ** 0.5
                es_irregular = desviacion > media * 0.3

                metrics[parada][linea] = {
                    'total_pasos': len(horas),
                    'intervalos': intervalos,
                    'media_intervalo': media,
                    'max_intervalo': max(intervalos),
                    'min_intervalo': min(intervalos),
                    'desviacion_estandar': desviacion,
                    'regularidad': "Irregular" if es_irregular else "Buena",
                    'hora_primer_paso': min(horas),
                    'hora_ultimo_paso': max(horas)
                }

                # Registrar paradas irregulares
                if es_irregular:
                    paradas_irregulares[linea].append({
                        'parada': parada,
                        'media_intervalo': media,
                        'desviacion': desviacion,
                        'ratio': desviacion / media
                    })

    return metrics, paradas_irregulares  # Ahora devuelve ambos


def generar_reporte_irregularidades(paradas_irregulares, nombre_modelo):
    """Genera un reporte detallado de paradas irregulares"""
    reporte = f"\n🔴 REPORTE DE PARADAS IRREGULARES - Modelo {nombre_modelo}\n"
    reporte += "=" * 60 + "\n"

    for linea, paradas in paradas_irregulares.items():
        reporte += f"\nLínea {linea} ({len(paradas)} paradas irregulares):\n"
        # Ordenar paradas por mayor irregularidad (ratio desviación/media)
        paradas_ordenadas = sorted(paradas, key=lambda x: x['ratio'], reverse=True)

        for p in paradas_ordenadas:
            reporte += (f"  - Parada {p['parada']}: Media={p['media_intervalo']:.1f} min, "
                        f"Desv={p['desviacion']:.1f} min (Ratio: {p['ratio']:.2f})\n")

    # Guardar reporte en archivo
    nombre_archivo = f"results/buses/details/irregularidades_{nombre_modelo}.txt"
    with open(nombre_archivo, 'w') as f:
        f.write(reporte)

    return reporte


def calcular_metricas_agregadas(metrics):
    """Calcula estadísticas agregadas por línea de autobús"""
    agregados = defaultdict(list)

    for parada in metrics:
        for linea, data in metrics[parada].items():
            agregados[linea].append({
                'media': data['media_intervalo'],
                'desviacion': data['desviacion_estandar'],
                'max_intervalo': data['max_intervalo'],
                'min_intervalo': data['min_intervalo'],
                'regularidad': data['regularidad'],
                'num_paradas': 1
            })

    resultados = {}
    for linea, datos_linea in agregados.items():
        medias = [d['media'] for d in datos_linea]
        desviaciones = [d['desviacion'] for d in datos_linea]

        resultados[linea] = {
            'media_global': statistics.mean(medias),
            'desviacion_global': statistics.mean(desviaciones),
            'max_global': max(d['max_intervalo'] for d in datos_linea),
            'min_global': min(d['min_intervalo'] for d in datos_linea),
            'paradas_irregulares': sum(1 for d in datos_linea if d['regularidad'] == "Irregular"),
            'total_paradas': len(datos_linea),
            'porcentaje_irregular': sum(1 for d in datos_linea if d['regularidad'] == "Irregular") / len(
                datos_linea) * 100
        }

    return resultados


def procesar_ejecucion(archivo):
    """Procesa un solo archivo de ejecución y devuelve sus métricas"""
    try:
        linea_datos = leer_archivo(archivo)
        datos = parse_custom_data(linea_datos)

        if not datos:
            print(f"  ⚠️ Archivo sin datos válidos: {os.path.basename(archivo)}")
            return None

        metrics, irregularidades = calcular_metricas(datos)  # Ahora recibe ambos valores

        # Generar reporte para esta ejecución
        nombre_ejecucion = os.path.splitext(os.path.basename(archivo))[0]
        reporte = generar_reporte_irregularidades(irregularidades, nombre_ejecucion)
        print(reporte)  # Opcional: mostrar en consola

        return calcular_metricas_agregadas(metrics)

    except Exception as e:
        print(f"  ❌ Error procesando {os.path.basename(archivo)}: {str(e)}")
        return None


def analizar_modelo(ruta_modelo):
    """Analiza todas las ejecuciones de un modelo y calcula promedios"""
    nombre_modelo = os.path.basename(ruta_modelo.rstrip('/'))
    print(f"\n🔍 Analizando modelo: {nombre_modelo}")

    # Buscar todos los archivos de ejecución
    archivos_ejecucion = []
    for archivo in os.listdir(ruta_modelo):
        if archivo.endswith('_service_frequency.csv'):
            archivos_ejecucion.append(os.path.join(ruta_modelo, archivo))

    if not archivos_ejecucion:
        print(f"⚠️ No se encontraron archivos de ejecución en {ruta_modelo}")
        return None

    print(f"  📂 Encontradas {len(archivos_ejecucion)} ejecuciones")

    # Procesar cada ejecución
    resultados_ejecuciones = []
    for archivo in archivos_ejecucion:
        print(f"  📊 Procesando ejecución: {os.path.basename(archivo)}")
        resultados = procesar_ejecucion(archivo)
        if resultados:
            resultados_ejecuciones.append(resultados)

    if not resultados_ejecuciones:
        print("  ⚠️ No se pudieron procesar ejecuciones válidas")
        return None

    # Calcular promedios del modelo a partir de todas sus ejecuciones
    lineas_comunes = set()
    for ejecucion in resultados_ejecuciones:
        lineas_comunes.update(ejecucion.keys())

    promedios_modelo = {}
    for linea in lineas_comunes:
        # Recopilar datos de todas las ejecuciones para esta línea
        medias = []
        desviaciones = []
        porcentajes_irreg = []

        for ejecucion in resultados_ejecuciones:
            if linea in ejecucion:
                medias.append(ejecucion[linea]['media_global'])
                desviaciones.append(ejecucion[linea]['desviacion_global'])
                porcentajes_irreg.append(ejecucion[linea]['porcentaje_irregular'])

        # Calcular promedios y desviaciones estándar entre ejecuciones
        promedios_modelo[linea] = {
            'media_promedio': statistics.mean(medias) if medias else 0,
            'media_desviacion': statistics.stdev(medias) if len(medias) > 1 else 0,
            'desviacion_promedio': statistics.mean(desviaciones) if desviaciones else 0,
            'irregularidad_promedio': statistics.mean(porcentajes_irreg) if porcentajes_irreg else 0,
            'num_ejecuciones': len(medias),
            'min_media': min(medias) if medias else 0,
            'max_media': max(medias) if medias else 0
        }

    print(f"  ✅ Procesadas {len(resultados_ejecuciones)} ejecuciones válidas")
    return {
        'nombre': nombre_modelo,
        'promedios': promedios_modelo,
        'ejecuciones': len(resultados_ejecuciones)
    }


def plot_comparativa_modelos(resultados_modelos):
    """Genera gráficos comparativos entre todos los modelos analizados"""
    if not resultados_modelos:
        return

    ORDEN_PERSONALIZADO = ['651A', '651B', '652A', '652B', 'L1', 'L2', 'DYNA', 'DYNB']

    lineas_comunes = set()
    for modelo in resultados_modelos.values():
        lineas_comunes.update(modelo['promedios'].keys())

    lineas_comunes = [linea for linea in ORDEN_PERSONALIZADO if linea in lineas_comunes]

    modelos = [m['nombre'] for m in resultados_modelos.values()]
    num_modelos = len(modelos)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs('analysis_results/buses', exist_ok=True)

    colores_personalizados = {
        '651A': '#171796',
        '651B': '#4b4bd3',
        '652A': '#2E8B57',
        '652B': '#98FB98',
        'L1': '#990000',
        'L2': '#FF0000',
        'DYNA': '#F033FF',
        'DYNB': '#ff7aff',
    }

    # Gráfico 1: Comparativa de frecuencia media con barras de error
    plt.figure(figsize=(max(12, num_modelos * 2), 8))

    # Preparar datos
    datos_grafico = {linea: {'medias': [], 'minimos': [], 'maximos': []}
                     for linea in lineas_comunes}

    for modelo in resultados_modelos.values():
        for linea in lineas_comunes:
            if linea in modelo['promedios']:
                datos_grafico[linea]['medias'].append(modelo['promedios'][linea]['media_promedio'])
                datos_grafico[linea]['minimos'].append(modelo['promedios'][linea]['min_media'])
                datos_grafico[linea]['maximos'].append(modelo['promedios'][linea]['max_media'])
            else:
                datos_grafico[linea]['medias'].append(0)
                datos_grafico[linea]['minimos'].append(0)
                datos_grafico[linea]['maximos'].append(0)

    # Posiciones de las barras
    x = np.arange(num_modelos)
    ancho = 0.8 / len(lineas_comunes)

    for i, linea in enumerate(lineas_comunes):
        color = colores_personalizados[linea]

        plt.bar(x + i * ancho, datos_grafico[linea]['medias'], width=ancho,
                color=color, label=linea,
                yerr=[[m - mn for m, mn in zip(datos_grafico[linea]['medias'], datos_grafico[linea]['minimos'])],
                      [mx - m for m, mx in zip(datos_grafico[linea]['medias'], datos_grafico[linea]['maximos'])]],
                capsize=5)

    plt.ylabel('Minutos')
    plt.xticks(x + ancho * (len(lineas_comunes) - 1) / 2, modelos, rotation=45, ha='right')
    plt.legend(loc='upper left')
    plt.grid(True, axis='y')
    plt.tight_layout()
    plt.savefig(f'results/buses/comparativa_frecuencia.png', dpi=300, bbox_inches='tight')
    plt.close()

    # Gráfico 2: Comparativa de irregularidad
    plt.figure(figsize=(max(12, num_modelos * 2), 8))

    for i, linea in enumerate(lineas_comunes):
        irregularidades = []
        for modelo in resultados_modelos.values():
            if linea in modelo['promedios']:
                irregularidades.append(modelo['promedios'][linea]['irregularidad_promedio'])
            else:
                irregularidades.append(0)

        plt.plot(modelos, irregularidades, 'o-', label=linea)

    plt.title(f'Comparativa de Irregularidad Promedio')
    plt.xlabel('Modelo')
    plt.ylabel('% Paradas Irregulares')
    plt.xticks(rotation=45, ha='right')
    plt.legend(loc='upper right')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f'results/buses/comparativa_irregularidad.png', dpi=300, bbox_inches='tight')
    plt.close()

    # Gráfico 3: Resumen de métricas por modelo
    colores = ['#171796', '#e6e8ec']

    fig, ax = plt.subplots(figsize=(12, 6))  # Esto devuelve una figura y un solo eje

    for i, modelo in enumerate(resultados_modelos.values()):
        medias = [v['media_promedio'] for v in modelo['promedios'].values()]
        color = colores[i % len(colores)]
        ax.bar(modelo['nombre'],
               statistics.mean(medias),
               yerr=statistics.stdev(medias) if len(medias) > 1 else 0,
               capsize=5,
               color=color,
               error_kw={'ecolor': 'red', 'capsize': 5}
               )

    ax.set_ylabel('Minutos')
    ax.tick_params(axis='x', rotation=45)

    plt.tight_layout()
    plt.savefig('results/buses/comparativa_general.png', dpi=300, bbox_inches='tight')
    plt.close()

def main():
    """Función principal"""
    os.makedirs('analysis_results', exist_ok=True)
    os.makedirs('analysis_results/buses', exist_ok=True)

    modelos_a_comparar = [
        "../experimental_tests/BAS_01",
        "../experimental_tests/BDI_01",
        "../experimental_tests/BAS_02",
        "../experimental_tests/BDI_02",
        "../experimental_tests/BAS_03",
        "../experimental_tests/BDI_03",
        "../experimental_tests/BAS_01_IC",
        "../experimental_tests/BDI_01_IC",
        "../experimental_tests/BDI_01_DY"
    ]

    resultados_modelos = {}
    for ruta_modelo in modelos_a_comparar:
        if os.path.isdir(ruta_modelo):
            resultado = analizar_modelo(ruta_modelo)
            if resultado:
                resultados_modelos[resultado['nombre']] = resultado
        else:
            print(f"⚠️ El directorio del modelo no existe: {ruta_modelo}")

    if resultados_modelos:
        print("\n📌 Generando buses entre modelos...")
        plot_comparativa_modelos(resultados_modelos)

        # Mostrar resumen en consola
        print("\n📋 Resumen comparativo:")
        for nombre, datos in resultados_modelos.items():
            print(f"\nModelo: {nombre} ({datos['ejecuciones']} ejecuciones)")
            for linea, metricas in datos['promedios'].items():
                print(f"  Línea {linea}:")
                print(f"    • Frecuencia: {metricas['media_promedio']:.2f} ± {metricas['media_desviacion']:.2f} min")
                print(f"    • Irregularidad: {metricas['irregularidad_promedio']:.1f}%")

        print("\n✅ Análisis completado. Gráficos guardados en 'results/buses'")
    else:
        print("❌ No se pudo generar comparativa: no hay datos válidos de modelos")


if __name__ == "__main__":
    main()
