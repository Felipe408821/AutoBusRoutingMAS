import re
import os
from collections import defaultdict


def analizar_paradas_dinamicas(archivo):
    """
    Analiza un archivo individual para identificar paradas dinámicas.
    """
    patron_solicitud = re.compile(
        r"\[(\d+\.\d+),'bus_stop\((\d+)\)','cfp to cover bus_stop\((\d+)\)','Num of passengers (\d+)'"
    )
    patron_confirmacion = re.compile(
        r"\[(\d+\.\d+),'bus\((\d+)\)','(.+?)',' sends an inform_done message to bus_stop\((\d+)\)'"
    )

    solicitudes = []
    confirmaciones = []

    with open(archivo, 'r', encoding='utf-8') as f:
        for linea in f:
            match_solicitud = patron_solicitud.search(linea)
            if match_solicitud:
                solicitudes.append({
                    'timestamp': float(match_solicitud.group(1)),
                    'parada_origen': match_solicitud.group(2),
                    'parada_destino': match_solicitud.group(3),
                    'pasajeros': int(match_solicitud.group(4)),
                    'confirmada': False
                })

            match_confirmacion = patron_confirmacion.search(linea)
            if match_confirmacion:
                confirmaciones.append({
                    'timestamp': float(match_confirmacion.group(1)),
                    'bus_id': match_confirmacion.group(2),
                    'linea_bus': match_confirmacion.group(3),
                    'parada_origen': match_confirmacion.group(4)
                })

    resultados = defaultdict(list)
    for conf in confirmaciones:
        for sol in [s for s in solicitudes if not s['confirmada']]:
            if sol['parada_origen'] == conf['parada_origen'] and sol['timestamp'] < conf['timestamp']:
                resultados[sol['parada_destino']].append({
                    'tiempo': sol['timestamp'],
                    'pasajeros': sol['pasajeros'],
                    'bus_asignado': conf['bus_id'],
                    'linea_bus': conf['linea_bus'],
                    'tiempo_respuesta': conf['timestamp'] - sol['timestamp'],
                    'parada_solicitante': sol['parada_origen']
                })
                sol['confirmada'] = True
                break

    return dict(resultados)


def generar_reporte(resultados, nombre_archivo):
    """Genera un reporte para un archivo específico"""
    if not resultados:
        return f"REPORTE PARA {nombre_archivo}\nNo se encontraron paradas dinámicas confirmadas.\n"

    reporte = f"REPORTE DETALLADO DE PARADAS DINÁMICAS - {nombre_archivo}\n"
    reporte += "=" * 70 + "\n\n"

    for parada, asignaciones in sorted(resultados.items(), key=lambda x: x[1][0]['tiempo']):
        reporte += f"PARADA DESTINO: bus_stop {parada} (PARADA INICIO: bus_stop {asignaciones[0]['parada_solicitante']})\n"
        for i, asign in enumerate(asignaciones, 1):
            reporte += (f"  Asignación {i}:\n"
                        f"    - Hora: {asign['tiempo']:.1f}\n"
                        f"    - Pasajeros: {asign['pasajeros']}\n"
                        f"    - Bus: {asign['bus_asignado']} (Línea: {asign['linea_bus']})\n"
                        f"    - Tiempo respuesta: {asign['tiempo_respuesta']:.1f} min\n\n")

    total_asign = sum(len(v) for v in resultados.values())
    buses_utilizados = defaultdict(int)
    for asign in resultados.values():
        for a in asign:
            buses_utilizados[a['bus_asignado']] += 1

    reporte += "RESUMEN ESTADÍSTICO\n"
    reporte += f"- Paradas dinámicas creadas: {len(resultados)}\n"
    reporte += f"- Asignaciones totales: {total_asign}\n"

    if buses_utilizados:
        bus_top = max(buses_utilizados.items(), key=lambda x: x[1])
        linea_top = next(a['linea_bus'] for a in resultados.values() for a in a if a['bus_asignado'] == bus_top[0])
        reporte += f"- Bus más activo: {bus_top[0]} (Línea {linea_top}) con {bus_top[1]} asignaciones\n"

    reporte += "\n" + "=" * 70 + "\n"
    return reporte


def procesar_archivo(archivo, carpeta_entrada, carpeta_salida):
    """Procesa un archivo individual y genera su reporte"""
    try:
        ruta_completa = os.path.join(carpeta_entrada, archivo)
        nombre_base = os.path.splitext(archivo)[0]

        # Procesar archivo
        resultados = analizar_paradas_dinamicas(ruta_completa)
        reporte = generar_reporte(resultados, nombre_base)

        # Guardar reporte individual
        nombre_reporte = f"reporte_{nombre_base}.txt"
        ruta_reporte = os.path.join(carpeta_salida, nombre_reporte)

        with open(ruta_reporte, 'w', encoding='utf-8') as f:
            f.write(reporte)

        print(f"Generado reporte: {ruta_reporte}")
        return True

    except Exception as e:
        print(f"Error al procesar {archivo}: {str(e)}")
        return False


def procesar_carpeta(carpeta_entrada, carpeta_salida):
    """Procesa todos los archivos CSV en una carpeta y genera reportes"""
    # Buscar archivos CSV que coincidan con el patrón de nombre
    archivos = [f for f in os.listdir(carpeta_entrada)
                if f.endswith('_bus_dynamic_stops.csv') and os.path.isfile(os.path.join(carpeta_entrada, f))]

    if not archivos:
        print(f"No se encontraron archivos de paradas dinámicas en {carpeta_entrada}")
        return 0

    print(f"\nProcesando {len(archivos)} archivos en {carpeta_entrada}...\n")
    exitos = 0

    for archivo in archivos:
        if procesar_archivo(archivo, carpeta_entrada, carpeta_salida):
            exitos += 1

    return exitos


def procesar_multiples_carpetas(carpetas, carpeta_salida_base="analysis_results/dynamic_stops"):
    """
    Procesa múltiples carpetas y guarda los resultados en subcarpetas organizadas.

    Args:
        carpetas (list): Lista de rutas de carpetas a procesar
        carpeta_salida_base (str): Carpeta base donde se guardarán los resultados
    """
    # Crear directorio base de resultados si no existe
    os.makedirs(carpeta_salida_base, exist_ok=True)

    total_archivos = 0
    total_exitos = 0

    for carpeta in carpetas:
        if not os.path.isdir(carpeta):
            print(f"Advertencia: {carpeta} no es un directorio válido. Se omitirá.")
            continue

        # Crear subcarpeta de resultados con el nombre de la carpeta de entrada
        nombre_carpeta = os.path.basename(os.path.normpath(carpeta))
        carpeta_salida = os.path.join(carpeta_salida_base, nombre_carpeta)
        os.makedirs(carpeta_salida, exist_ok=True)

        print(f"\n{'=' * 50}")
        print(f"PROCESANDO CARPETA: {carpeta}")
        print(f"{'=' * 50}")

        exitos = procesar_carpeta(carpeta, carpeta_salida)
        total_exitos += exitos
        total_archivos += len([f for f in os.listdir(carpeta)
                               if f.endswith('_bus_dynamic_stops.csv') and os.path.isfile(os.path.join(carpeta, f))])

    print(f"\n{'=' * 50}")
    print(f"PROCESAMIENTO COMPLETADO")
    print(f"{'=' * 50}")
    print(f"Total de carpetas procesadas: {len(carpetas)}")
    print(f"Total de archivos encontrados: {total_archivos}")
    print(f"Total de archivos procesados exitosamente: {total_exitos}")
    print(f"\nTodos los reportes se han guardado en la carpeta: {os.path.abspath(carpeta_salida_base)}")


if __name__ == "__main__":
    carpetas_a_procesar = [
        'experimental_tests/BDI_01',
        'experimental_tests/BDI_01_IC',
        'experimental_tests/BDI_02',
        'experimental_tests/BDI_03',
        'experimental_tests/BDI_01_DY',
        'experimental_tests/BDI_01_RE'
    ]

    procesar_multiples_carpetas(carpetas_a_procesar)
