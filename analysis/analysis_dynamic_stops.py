import os
import re
from collections import defaultdict, Counter
from glob import glob


def encontrar_archivos_reportes(carpetas):
    """Busca archivos de reportes en las carpetas especificadas"""
    archivos = []
    for carpeta in carpetas:
        # Verificar si la carpeta existe
        if not os.path.exists(carpeta):
            print(f"Advertencia: Carpeta no encontrada - {carpeta}")
            continue

        # Buscar archivos que coincidan con el patrón en la carpeta y subcarpetas
        patron = os.path.join(carpeta, '**', 'reporte_*_bus_dynamic_stops.txt')
        archivos_encontrados = glob(patron, recursive=True)

        if not archivos_encontrados:
            print(f"Advertencia: No se encontraron archivos en {carpeta}")
        else:
            archivos.extend(archivos_encontrados)

    # Eliminar duplicados y verificar que los archivos existen
    archivos = list(set([f for f in archivos if os.path.isfile(f)]))

    print(f"\nArchivos encontrados ({len(archivos)}):")
    for archivo in sorted(archivos):
        print(f" - {os.path.normpath(archivo)}")

    return archivos


def analizar_y_recomendar(carpetas):
    """Analiza los reportes y genera recomendaciones de rutas"""
    archivos = encontrar_archivos_reportes(carpetas)

    if not archivos:
        print("\nNo se encontraron archivos de reportes en las carpetas especificadas")
        return None

    # Consolidar datos de todos los archivos
    frecuencias_totales = Counter()
    pasajeros_totales = Counter()
    archivos_procesados = 0

    for archivo in archivos:
        datos = procesar_reporte(archivo)
        if datos:
            frecuencias_totales.update(datos['frecuencias'])
            pasajeros_totales.update(datos['pasajeros'])
            archivos_procesados += 1

    print(f"\nProcesados {archivos_procesados}/{len(archivos)} archivos correctamente")

    if not frecuencias_totales:
        print("\nNo se encontraron datos válidos en los reportes")
        return None

    # Generar recomendaciones
    recomendaciones = []

    # 1. Ruta más frecuente
    if frecuencias_totales:
        ruta_frec = frecuencias_totales.most_common(1)[0][0]
        recomendaciones.append({
            'tipo': 'Más frecuente',
            'ruta': ruta_frec,
            'frecuencia': frecuencias_totales[ruta_frec],
            'pasajeros': pasajeros_totales.get(ruta_frec, 0),
            'descripcion': 'Ruta que aparece con más frecuencia en los reportes'
        })

    # 2. Ruta con más pasajeros
    if pasajeros_totales:
        ruta_pasaj = pasajeros_totales.most_common(1)[0][0]
        recomendaciones.append({
            'tipo': 'Más pasajeros',
            'ruta': ruta_pasaj,
            'frecuencia': frecuencias_totales.get(ruta_pasaj, 0),
            'pasajeros': pasajeros_totales[ruta_pasaj],
            'descripcion': 'Ruta con mayor volumen total de pasajeros'
        })

    # 3. Ruta balanceada (combinación de frecuencia y pasajeros)
    if frecuencias_totales and pasajeros_totales:
        rutas_score = []
        for ruta in set(frecuencias_totales.keys()).union(set(pasajeros_totales.keys())):
            freq = frecuencias_totales.get(ruta, 0)
            pasaj = pasajeros_totales.get(ruta, 0)
            score = (freq * 0.4) + (pasaj * 0.6)  # Ponderación ajustable
            rutas_score.append((ruta, score, freq, pasaj))

        if rutas_score:
            rutas_score.sort(key=lambda x: x[1], reverse=True)
            mejor = rutas_score[0]
            recomendaciones.append({
                'tipo': 'Mejor balanceada',
                'ruta': mejor[0],
                'frecuencia': mejor[2],
                'pasajeros': mejor[3],
                'score': mejor[1],
                'descripcion': 'Mejor combinación de frecuencia y volumen de pasajeros'
            })

    return recomendaciones


def mostrar_recomendaciones(recomendaciones):
    """Muestra las recomendaciones de forma clara"""
    if not recomendaciones:
        print("\nNo se pudieron generar recomendaciones")
        return

    print("\n" + "=" * 60)
    print(" RECOMENDACIONES DE RUTAS ÓPTIMAS ".center(60, '='))
    print("=" * 60 + "\n")

    for rec in recomendaciones:
        print(f"[{rec['tipo'].upper()}]")
        print(f"Ruta: bus_stop {rec['ruta'][0]} → bus_stop {rec['ruta'][1]}")
        print(f" - Frecuencia: {rec['frecuencia']} apariciones en reportes")
        print(f" - Pasajeros totales: {rec['pasajeros']}")
        if 'score' in rec:
            print(f" - Puntuación combinada: {rec['score']:.2f}")
        print(f" - Criterio: {rec.get('descripcion', '')}")
        print("-" * 60)


def procesar_reporte(archivo):
    """Procesa un archivo de reporte y extrae la información relevante incluyendo horas"""
    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            contenido = f.read()
    except Exception as e:
        print(f"Error al leer {archivo}: {str(e)}")
        return None

    # Expresiones regulares mejoradas
    patron_parada = re.compile(
        r"PARADA DESTINO:\s*bus_stop\s*(\d+)\s*\(PARADA INICIO:\s*bus_stop\s*(\d+)\)"
    )
    patron_pasajeros = re.compile(
        r"-\s*Pasajeros:\s*(\d+)"
    )
    patron_hora = re.compile(
        r"(\d{2}:\d{2}:\d{2})"  # Formato HH:MM:SS
    )

    frecuencias = Counter()
    pasajeros = Counter()
    horas_asignacion = defaultdict(list)  # Diccionario para almacenar horas por ruta
    current_route = None
    current_hora = None

    for linea in contenido.split('\n'):
        # Buscar hora en la línea
        hora_match = patron_hora.search(linea)
        if hora_match:
            current_hora = hora_match.group(1)

        # Buscar declaración de paradas
        if "PARADA DESTINO:" in linea and "PARADA INICIO:" in linea:
            match = patron_parada.search(linea)
            if match:
                destino, origen = match.groups()
                current_route = (origen, destino)
                frecuencias[current_route] += 1
                if current_hora:  # Solo si hemos encontrado una hora
                    horas_asignacion[current_route].append(current_hora)

        # Buscar línea de pasajeros cuando tenemos una ruta actual
        elif current_route and "- Pasajeros:" in linea:
            match = patron_pasajeros.search(linea)
            if match:
                try:
                    num = int(match.group(1))
                    pasajeros[current_route] += num
                except ValueError:
                    continue

    return {
        'frecuencias': frecuencias,
        'pasajeros': pasajeros,
        'horas_asignacion': horas_asignacion,
        'archivo': archivo
    }


def generar_informe_rutas(carpetas, nombre_archivo="informe_agregado.txt"):
    """Genera un archivo de texto con un informe detallado de todas las rutas encontradas incluyendo horas"""
    archivos = encontrar_archivos_reportes(carpetas)

    if not archivos:
        print("\nNo se encontraron archivos de reportes para generar el informe")
        return

    # Procesar todos los archivos y consolidar datos
    frecuencias_totales = Counter()
    pasajeros_totales = Counter()
    horas_totales = defaultdict(list)  # Para consolidar horas de todas las rutas

    for archivo in archivos:
        datos = procesar_reporte(archivo)
        if datos:
            frecuencias_totales.update(datos['frecuencias'])
            pasajeros_totales.update(datos['pasajeros'])
            # Consolidar horas
            for ruta, horas in datos['horas_asignacion'].items():
                horas_totales[ruta].extend(horas)

    if not frecuencias_totales:
        print("\nNo hay datos de rutas para generar el informe")
        return

    # Ordenar rutas por frecuencia (descendente)
    rutas_ordenadas = sorted(frecuencias_totales.items(), key=lambda x: x[1], reverse=True)

    # Generar el contenido del informe
    contenido_informe = []
    contenido_informe.append("=" * 70)
    contenido_informe.append(" INFORME DETALLADO DE RUTAS DE AUTOBÚS ".center(70, ' '))
    contenido_informe.append("=" * 70)
    contenido_informe.append(f"\nFecha de generación: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    contenido_informe.append(f"Total de archivos procesados: {len(archivos)}")
    contenido_informe.append(f"Total de rutas diferentes encontradas: {len(frecuencias_totales)}")
    contenido_informe.append("\n" + "=" * 70)
    contenido_informe.append(" DETALLE POR RUTA ".center(70, ' '))
    contenido_informe.append("=" * 70 + "\n")

    for ruta, frecuencia in rutas_ordenadas:
        origen, destino = ruta
        pasajeros = pasajeros_totales.get(ruta, 0)
        horas = horas_totales.get(ruta, [])

        contenido_informe.append(f"Ruta: bus_stop {origen} → bus_stop {destino}")
        contenido_informe.append(f" - Frecuencia: {frecuencia} apariciones en reportes")
        contenido_informe.append(f" - Pasajeros totales: {pasajeros}")
        contenido_informe.append(
            f" - Promedio de pasajeros por viaje: {pasajeros / frecuencia:.2f}" if frecuencia > 0 else " - Promedio de pasajeros por viaje: N/A")

        # Información de horas
        if horas:
            # Contar ocurrencias por hora
            conteo_horas = Counter(horas)
            horas_ordenadas = sorted(conteo_horas.items(), key=lambda x: x[1], reverse=True)

            contenido_informe.append("\n   Horas de asignación (más frecuentes primero):")
            for hora, count in horas_ordenadas[:5]:  # Mostrar top 5 horas
                contenido_informe.append(f"    - {hora}: {count} asignaciones")

            # Calcular rango horario
            try:
                horas_datetime = [datetime.datetime.strptime(h, "%H:%M:%S") for h in horas]
                min_hora = min(horas_datetime).strftime("%H:%M:%S")
                max_hora = max(horas_datetime).strftime("%H:%M:%S")
                contenido_informe.append(f"\n   Rango horario: De {min_hora} a {max_hora}")
            except:
                pass
        else:
            contenido_informe.append("\n   No se registraron horas de asignación")

        contenido_informe.append("-" * 50)

    # Estadísticas resumen
    total_pasajeros = sum(pasajeros_totales.values())
    total_viajes = sum(frecuencias_totales.values())

    contenido_informe.append("\n" + "=" * 70)
    contenido_informe.append(" ESTADÍSTICAS GENERALES ".center(70, ' '))
    contenido_informe.append("=" * 70)
    contenido_informe.append(f"\nTotal de viajes registrados: {total_viajes}")
    contenido_informe.append(f"Total de pasajeros transportados: {total_pasajeros}")
    contenido_informe.append(
        f"Promedio de pasajeros por viaje: {total_pasajeros / total_viajes:.2f}" if total_viajes > 0 else "Promedio de pasajeros por viaje: N/A")

    # Top rutas
    top_frecuencia = frecuencias_totales.most_common(3)
    top_pasajeros = pasajeros_totales.most_common(3)

    contenido_informe.append("\nTop 3 rutas más frecuentes:")
    for i, (ruta, freq) in enumerate(top_frecuencia, 1):
        contenido_informe.append(f"{i}. bus_stop {ruta[0]} → bus_stop {ruta[1]} - {freq} viajes")

    contenido_informe.append("\nTop 3 rutas con más pasajeros:")
    for i, (ruta, pasaj) in enumerate(top_pasajeros, 1):
        contenido_informe.append(f"{i}. bus_stop {ruta[0]} → bus_stop {ruta[1]} - {pasaj} pasajeros")

    # Análisis de horas pico
    contenido_informe.append("\n" + "=" * 70)
    contenido_informe.append(" ANÁLISIS DE HORAS ".center(70, ' '))
    contenido_informe.append("=" * 70)

    # Consolidar todas las horas
    todas_horas = []
    for horas in horas_totales.values():
        todas_horas.extend(horas)

    if todas_horas:
        # Contar frecuencia por hora
        conteo_total_horas = Counter(todas_horas)
        top_horas = conteo_total_horas.most_common(5)

        contenido_informe.append("\nTop 5 horas con más asignaciones:")
        for i, (hora, count) in enumerate(top_horas, 1):
            contenido_informe.append(f"{i}. {hora}: {count} asignaciones")

        # Distribución por franjas horarias
        franjas = {
            "Madrugada (00:00-05:59)": 0,
            "Mañana (06:00-11:59)": 0,
            "Tarde (12:00-17:59)": 0,
            "Noche (18:00-23:59)": 0
        }

        for hora in todas_horas:
            try:
                h = int(hora.split(':')[0])
                if h < 6:
                    franjas["Madrugada (00:00-05:59)"] += 1
                elif h < 12:
                    franjas["Mañana (06:00-11:59)"] += 1
                elif h < 18:
                    franjas["Tarde (12:00-17:59)"] += 1
                else:
                    franjas["Noche (18:00-23:59)"] += 1
            except:
                pass

        contenido_informe.append("\nDistribución por franjas horarias:")
        for franja, count in franjas.items():
            porcentaje = (count / len(todas_horas)) * 100 if todas_horas else 0
            contenido_informe.append(f" - {franja}: {count} asignaciones ({porcentaje:.1f}%)")
    else:
        contenido_informe.append("\nNo se registraron horas de asignación en los reportes")

    try:
        with open("analysis_results/dynamic_stops/"+ nombre_archivo, 'w', encoding='utf-8') as f:
            f.write("\n".join(contenido_informe))
        print(f"\nInforme generado exitosamente: {nombre_archivo}")
    except Exception as e:
        print(f"\nError al generar el informe: {str(e)}")


# Modificación en el main para incluir la generación del informe
if __name__ == "__main__":
    import datetime  # Necesario para la fecha en el informe

    # Configuración de carpetas a analizar
    carpetas_a_probar = [
        'analysis_results/dynamic_stops',
    ]

    # Filtrar solo las carpetas que existen
    carpetas_a_analizar = [c for c in carpetas_a_probar if os.path.isdir(c)]

    if not carpetas_a_analizar:
        print("\nError: No se pudo encontrar la carpeta 'analysis_results/dynamic_stops'")
    else:
        print("\nCarpetas encontradas:")
        for c in carpetas_a_analizar:
            print(f" - {os.path.abspath(c)}")

        subcarpetas = []
        for carpeta in carpetas_a_analizar:
            for sub in ['BDI_01', 'BDI_01_IC', 'BDI_01_DY', 'BDI_02', 'BDI_03']:
                sub_path = os.path.join(carpeta, sub)
                if os.path.isdir(sub_path):
                    subcarpetas.append(sub_path)

        if subcarpetas:
            carpetas_a_analizar.extend(subcarpetas)

        # Procesar y mostrar resultados
        recomendaciones = analizar_y_recomendar(carpetas_a_analizar)
        mostrar_recomendaciones(recomendaciones)

        # Generar el informe detallado
        generar_informe_rutas(carpetas_a_analizar)