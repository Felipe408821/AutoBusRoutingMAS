import os
import re
from collections import defaultdict, Counter
from glob import glob
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap

# Constantes para mejorar mantenibilidad
MODELOS_CONOCIDOS = ['BDI_01', 'BDI_02', 'BDI_03', 'BDI_01_IC', 'BDI_01_DY']

PATRON_ARCHIVOS = 'reporte_*_bus_dynamic_stops.txt'
DIRECTORIO_SALIDA = "analysis_results/dynamic_stops"

# Patrones de expresiones regulares precompilados para mejor performance
PATRON_PARADA = re.compile(r"PARADA DESTINO:\s*bus_stop\s*(\d+)\s*\(PARADA INICIO:\s*bus_stop\s*(\d+)\)")
PATRON_PASAJEROS = re.compile(r"-\s*Pasajeros:\s*(\d+)")
PATRON_HORA = re.compile(r"(\d{2}:\d{2}:\d{2})")
PATRON_PARADAS_DINAMICAS = re.compile(r"Rutas dinámicas creadas:\s*(\d+)")
PATRON_ASIGNACIONES = re.compile(r"Asignaciones totales:\s*(\d+)")

# Configuración de estilo global
plt.style.use('seaborn-v0_8')  # Estilo más moderno
sns.set_palette("viridis")  # Paleta por defecto más accesible

sns.set_style("whitegrid", {
    'axes.facecolor': 'white',
    'grid.color': 'black',
    'grid.linestyle': '--',
    'grid.alpha': 0.3,
    'axes.edgecolor': 'black',
    'axes.linewidth': 0.5,
})

# Colormap personalizado mejorado con 3 colores para mejor gradación
custom_cmap = LinearSegmentedColormap.from_list("custom", ["#f0f0f0", "#6a6aed", "#171796"])


def encontrar_archivos_reportes(carpetas):
    """Busca archivos de reportes en las carpetas especificadas de manera eficiente"""
    archivos = set()

    for carpeta in carpetas:
        if not os.path.exists(carpeta):
            print(f"Advertencia: Carpeta no encontrada - {carpeta}")
            continue

        patron = os.path.join(carpeta, '**', PATRON_ARCHIVOS)
        try:
            archivos_encontrados = glob(patron, recursive=True)
            if not archivos_encontrados:
                print(f"Advertencia: No se encontraron archivos en {carpeta}")
                continue

            archivos.update(f for f in archivos_encontrados if os.path.isfile(f))
        except Exception as e:
            print(f"Error al buscar archivos en {carpeta}: {str(e)}")

    print(f"\nArchivos encontrados ({len(archivos)}):")
    for archivo in sorted(archivos):
        print(f" - {os.path.normpath(archivo)}")

    return list(archivos)


def procesar_reporte(archivo):
    """Procesa un archivo de reporte de manera eficiente usando generadores"""
    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            contenido = f.read()
    except Exception as e:
        print(f"Error al leer {archivo}: {str(e)}")
        return None

    # Extraer datos principales del resumen
    datos_resumen = {
        'paradas_dinamicas': 0,
        'asignaciones_totales': 0
    }

    match_paradas = PATRON_PARADAS_DINAMICAS.search(contenido)
    if match_paradas:
        datos_resumen['paradas_dinamicas'] = int(match_paradas.group(1))

    match_asignaciones = PATRON_ASIGNACIONES.search(contenido)
    if match_asignaciones:
        datos_resumen['asignaciones_totales'] = int(match_asignaciones.group(1))

    # Procesar líneas
    frecuencias = Counter()
    pasajeros = Counter()
    current_route = None

    for linea in contenido.split('\n'):
        if not linea.strip():
            continue

        # Buscar declaración de paradas
        if "PARADA DESTINO:" in linea and "PARADA INICIO:" in linea:
            match = PATRON_PARADA.search(linea)
            if match:
                destino, origen = match.groups()
                current_route = (origen, destino)
            continue

        # Detectar asignación individual
        if linea.strip().startswith("Asignación"):
            if current_route:
                frecuencias[current_route] += 1  # <--- suma una asignación por línea
            continue

        # Buscar pasajeros solo si tenemos una ruta actual
        if current_route and "- Pasajeros:" in linea:
            match = PATRON_PASAJEROS.search(linea)
            if match:
                try:
                    pasajeros[current_route] += int(match.group(1))
                except ValueError:
                    continue

    return {
        'frecuencias': frecuencias,
        'pasajeros': pasajeros,
        **datos_resumen,
        'archivo': archivo
    }


def determinar_modelo(ruta_archivo):
    """Determina el modelo a partir de la ruta del archivo"""
    directorio = os.path.dirname(ruta_archivo)
    nombre_directorio = os.path.basename(directorio)

    if nombre_directorio in MODELOS_CONOCIDOS:
        return nombre_directorio

    directorio_padre = os.path.basename(os.path.dirname(directorio))
    return directorio_padre if directorio_padre in MODELOS_CONOCIDOS else None


def generar_recomendaciones(frecuencias, pasajeros):
    """Genera recomendaciones basadas en los datos consolidados"""
    recomendaciones = []

    if not frecuencias or not pasajeros:
        return recomendaciones

    # 1. Ruta más frecuente
    ruta_frec, freq = frecuencias.most_common(1)[0]
    recomendaciones.append({
        'tipo': 'Más frecuente',
        'ruta': ruta_frec,
        'frecuencia': freq,
        'pasajeros': pasajeros.get(ruta_frec, 0),
        'descripcion': 'Ruta que aparece con más frecuencia en los reportes'
    })

    # 2. Ruta con más pasajeros
    ruta_pasaj, pasaj = pasajeros.most_common(1)[0]
    recomendaciones.append({
        'tipo': 'Más pasajeros',
        'ruta': ruta_pasaj,
        'frecuencia': frecuencias.get(ruta_pasaj, 0),
        'pasajeros': pasaj,
        'descripcion': 'Ruta con mayor volumen total de pasajeros'
    })

    # 3. Ruta balanceada
    rutas_score = [
        (ruta, (frec * 0.4 + pasaj * 0.6), frec, pasaj)
        for ruta in set(frecuencias) | set(pasajeros)
        for frec in [frecuencias.get(ruta, 0)]
        for pasaj in [pasajeros.get(ruta, 0)]
    ]

    if rutas_score:
        rutas_score.sort(key=lambda x: x[1], reverse=True)
        ruta, score, freq, pasaj = rutas_score[0]
        recomendaciones.append({
            'tipo': 'Mejor balanceada',
            'ruta': ruta,
            'frecuencia': freq,
            'pasajeros': pasaj,
            'score': score,
            'descripcion': 'Mejor combinación de frecuencia y volumen de pasajeros'
        })

    return recomendaciones


def mostrar_recomendaciones(recomendaciones):
    """Muestra las recomendaciones de forma clara y formateada"""
    if not recomendaciones:
        print("\nNo se pudieron generar recomendaciones")
        return

    header = " RECOMENDACIONES DE RUTAS ÓPTIMAS "
    print(f"\n{header.center(60, '=')}")

    for rec in recomendaciones:
        print(f"\n[{rec['tipo'].upper()}]")
        print(f"Ruta: bus_stop {rec['ruta'][0]} → bus_stop {rec['ruta'][1]}")
        print(f" - Frecuencia: {rec['frecuencia']} apariciones")
        print(f" - Pasajeros totales: {rec['pasajeros']}")
        if 'score' in rec:
            print(f" - Puntuación combinada: {rec['score']:.2f}")
        print(f" - Criterio: {rec.get('descripcion', '')}")
        print("-" * 60)


def generar_informe_rutas(carpetas, nombre_archivo="informe_agregado.txt"):
    """Genera un informe detallado optimizado con estadísticas de asignaciones"""
    archivos = encontrar_archivos_reportes(carpetas)
    if not archivos:
        print("\nNo se encontraron archivos para generar el informe")
        return

    datos_archivos = [procesar_reporte(a) for a in archivos]
    datos_validos = [d for d in datos_archivos if d]

    # Consolidar datos
    frecuencias_totales = Counter()
    pasajeros_totales = Counter()

    rutas_unicas_por_modelo = defaultdict(set)

    pasajeros_por_modelo = Counter()

    estadisticas_por_modelo = defaultdict(lambda: {
        'rutas_generadas': 0,
        'rutas_totales': [],
        'asignaciones_totales': [],
        'archivos': 0,
        'pasajeros_totales': 0,
    })

    for datos in datos_validos:
        frecuencias_totales.update(datos['frecuencias'])
        pasajeros_totales.update(datos['pasajeros'])

        modelo = determinar_modelo(datos['archivo'])
        if modelo:
            rutas_unicas_por_modelo[modelo].update(datos['frecuencias'].keys())

            total_pasajeros = sum(datos['pasajeros'].values())
            pasajeros_por_modelo[modelo] += total_pasajeros

            estadisticas_por_modelo[modelo]['rutas_generadas'] = len(rutas_unicas_por_modelo[modelo])
            estadisticas_por_modelo[modelo]['rutas_totales'].append(datos['paradas_dinamicas'])

            estadisticas_por_modelo[modelo]['asignaciones_totales'].append(datos['asignaciones_totales'])
            estadisticas_por_modelo[modelo]['archivos'] += 1
            estadisticas_por_modelo[modelo]['pasajeros_totales'] = pasajeros_por_modelo[modelo]

    if not frecuencias_totales:
        print("\nNo hay datos válidos para generar el informe")
        return

    # Generar contenido del informe
    contenido = [
        "=" * 70,
        " INFORME DETALLADO DE RUTAS DE AUTOBÚS ".center(70),
        "=" * 70,
        f"Total de archivos procesados: {len(datos_validos)}/{len(archivos)}",
        f"Total de rutas diferentes: {len(frecuencias_totales)}",
    ]

    # Sección de estadísticas por modelo
    contenido.extend([
        "\n" + "=" * 70,
        " ESTADÍSTICAS POR MODELO ".center(70),
        "=" * 70
    ])

    for modelo in MODELOS_CONOCIDOS:
        stats = estadisticas_por_modelo.get(modelo)
        if stats and stats['archivos'] > 0:
            avg_paradas = sum(stats['rutas_totales'])
            avg_asignaciones = sum(stats['asignaciones_totales'])

            contenido.extend([
                f"\nModelo {modelo}:",
                f" - Muestras analizadas: {stats['archivos']}",
                f" - Rutas dinámicas únicas: {stats['rutas_generadas']:.2f}",
                f" - Rutas dinámicas totales: {avg_paradas:.2f}",
                f" - Asignaciones totales: {avg_asignaciones:.2f}",
                f" - Relación (Asignación/Ruta): {avg_asignaciones/stats['rutas_generadas']:.2f}",
                f" - Pasajeros beneficiados: {stats['pasajeros_totales']:.2f}",
            ])
        else:
            contenido.append(f"\nModelo {modelo}: No se encontraron datos")

    # Sección de detalle por ruta
    contenido.extend([
        "\n" + "=" * 70,
        " DETALLE POR RUTA ".center(70),
        "=" * 70
    ])

    for (origen, destino), freq in frecuencias_totales.most_common():
        pasaj = pasajeros_totales.get((origen, destino), 0)
        contenido.extend([
            f"\nRuta: bus_stop {origen} → bus_stop {destino}",
            f" - Frecuencia: {freq} apariciones",
            f" - Pasajeros totales: {pasaj}",
            f" - Promedio pasajeros/viaje: {pasaj / freq:.2f}" if freq else " - Promedio pasajeros/viaje: N/A",
            "-" * 50
        ])

    # Estadísticas generales
    total_viajes = sum(frecuencias_totales.values())
    total_pasajeros = sum(pasajeros_totales.values())

    contenido.extend([
        "\n" + "=" * 70,
        " ESTADÍSTICAS GENERALES ".center(70),
        "=" * 70,
        f"\nTotal asignaciones: {total_viajes}",
        f"Total de pasajeros beneficiados: {total_pasajeros}",
        f"Promedio de pasajeros por viaje: {total_pasajeros / total_viajes:.2f}" if total_viajes else "Promedio de pasajeros por viaje: N/A"
    ])

    # Guardar informe
    generar_graficos_a(estadisticas_por_modelo, frecuencias_totales, pasajeros_totales)

    try:
        os.makedirs(DIRECTORIO_SALIDA, exist_ok=True)
        ruta_completa = os.path.join(DIRECTORIO_SALIDA, nombre_archivo)
        with open(ruta_completa, 'w', encoding='utf-8') as f:
            f.write("\n".join(contenido))
        print(f"\nInforme generado exitosamente: {ruta_completa}")
    except Exception as e:
        print(f"\nError al generar el informe: {str(e)}")


def main():
    """Función principal"""
    carpetas_base = [c for c in ['analysis_results/dynamic_stops'] if os.path.isdir(c)]
    if not carpetas_base:
        print("\nError: No se encontró la carpeta base")
        return

    # Encontrar subcarpetas de modelos
    carpetas_analizar = []
    for carpeta in carpetas_base:
        carpetas_analizar.extend(
            os.path.join(carpeta, sub)
            for sub in MODELOS_CONOCIDOS
                if os.path.isdir(os.path.join(carpeta, sub)))

    # Procesamiento principal
    frecuencias, pasajeros = consolidar_datos(carpetas_analizar)
    recomendaciones = generar_recomendaciones(frecuencias, pasajeros)
    mostrar_recomendaciones(recomendaciones)
    generar_informe_rutas(carpetas_analizar)


def consolidar_datos(carpetas):
    """Consolida datos de múltiples archivos para análisis"""
    archivos = encontrar_archivos_reportes(carpetas)
    if not archivos:
        return Counter(), Counter()

    frecuencias = Counter()
    pasajeros = Counter()

    for archivo in archivos:
        datos = procesar_reporte(archivo)
        if datos:
            frecuencias.update(datos['frecuencias'])
            pasajeros.update(datos['pasajeros'])

    return frecuencias, pasajeros


def escalar_colores(valores, gamma=0.5):
    """Escala los valores con corrección gamma para controlar el contraste"""
    norm = valores / valores.max()
    intensidad = np.power(norm, gamma)  # Gamma <1 para mayor contraste en valores bajos
    return [custom_cmap(v) for v in intensidad]


def grafico_rutas(df, col_valor, titulo, archivo_salida):
    """Función genérica para crear gráficos de rutas"""
    plt.figure(figsize=(12, 7))

    # Ordenar por valor descendente
    df = df.sort_values(col_valor, ascending=True)

    # Crear gráfico con bordes definidos
    ax = sns.barplot(
        data=df,
        y='Ruta',
        x=col_valor,
        palette=escalar_colores(df[col_valor]),
        edgecolor = None,  # Eliminamos los bordes
        linewidth = 0  # Sin línea de contorno
    )

    # Títulos y etiquetas con estilo claro
    plt.title(titulo, fontsize=14, pad=20, fontweight='bold', color='black')
    plt.xlabel('Número de ' + col_valor, fontsize=12, labelpad=10, color='black')
    plt.ylabel('Ruta', fontsize=12, labelpad=10, color='black')

    # Configuración de ejes y ticks
    ax.tick_params(axis='both', which='major', labelsize=10, colors='black')
    ax.set_facecolor('white')  # Fondo blanco para el área del gráfico

    # Añadir valores en las barras (en negro para mejor contraste)
    for i, valor in enumerate(df[col_valor]):
        ax.text(valor + 0.02 * df[col_valor].max(), i,
                f'{valor:,.0f}',
                va='center',
                fontsize=10,
                color='black')

    # Cuadrícula horizontal negra
    ax.grid(axis='x', color='black', linestyle='-', alpha=0.3)
    ax.grid(axis='y', visible=False)  # Ocultar grid vertical

    # Ajustar límites para evitar espacio en blanco
    ax.set_xlim(left=0, right=df[col_valor].max() * 1.15)

    # Guardar con fondo blanco
    plt.tight_layout()
    plt.savefig(
        os.path.join(DIRECTORIO_SALIDA, archivo_salida),
        dpi=300,
        bbox_inches='tight',
        facecolor='white'  # Fondo blanco al guardar
    )
    plt.close()


def grafico_modelos(df, col_y, titulo, archivo_salida, hue=None, palette=None):
    """Función genérica para gráficos por modelo"""
    plt.figure(figsize=(10, 6))

    # Ordenar por el valor principal descendente
    if hue is None:
        df = df.sort_values(col_y, ascending=False)

    # Crear gráfico de barras sin bordes
    ax = sns.barplot(
        data=df,
        x='Modelo',
        y=col_y,
        hue=hue,
        palette=palette if palette else escalar_colores(df[col_y]),
        edgecolor=None,
        linewidth=0
    )

    # Títulos y etiquetas
    plt.title(titulo, fontsize=14, pad=20, fontweight='bold', color='black')
    plt.xlabel('Modelo', fontsize=12, labelpad=10, color='black')
    plt.ylabel(col_y, fontsize=12, labelpad=10, color='black')

    # Configuración de ejes
    ax.tick_params(axis='x', rotation=45, labelsize=10, colors='black')
    ax.tick_params(axis='y', labelsize=10, colors='black')
    ax.set_facecolor('white')

    # Añadir valores formateados en las barras (funciona para gráficos simples y agrupados)
    for p in ax.patches:
        valor = p.get_height()
        if not np.isnan(valor):  # Ignorar valores NaN
            ax.text(p.get_x() + p.get_width() / 2.,
                    p.get_height() + 0.02 * df[col_y].max(),
                    formatear_numero(valor),
                    ha='center',
                    va='center',
                    fontsize=9,
                    color='black')

    # Cuadrícula y estilo
    ax.grid(axis='y', color='black', linestyle='-', alpha=0.3)
    ax.grid(axis='x', visible=False)
    sns.despine(left=True, bottom=True)

    # Ajustar leyenda si hay hue
    if hue is not None:
        plt.legend(title=hue, facecolor='white', edgecolor='none')

    # Formatear eje Y con formato europeo
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: formatear_numero(x)))

    plt.tight_layout()
    plt.savefig(
        os.path.join(DIRECTORIO_SALIDA, archivo_salida),
        dpi=300,
        bbox_inches='tight',
        facecolor='white'
    )
    plt.close()


def formatear_numero(valor):
    """Alternativa si locale no funciona"""
    if valor < 10:
        return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    else:
        return f"{valor:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")


def generar_graficos_a(estadisticas_por_modelo, frecuencias_totales, pasajeros_totales):
    # Crear DataFrame desde estadisticas_por_modelo
    df_modelos = []

    for modelo, stats in estadisticas_por_modelo.items():
        if stats['archivos'] == 0:
            continue

        total_rutas = stats['rutas_generadas']
        total_paradas = sum(stats['rutas_totales'])
        total_asignaciones = sum(stats['asignaciones_totales'])
        pasajeros = stats['pasajeros_totales']

        df_modelos.append({
            'Modelo': modelo,
            'Rutas Dinámicas Únicas': total_rutas,
            'Rutas Dinámicas Totales': total_paradas,
            'Asignaciones Totales': total_asignaciones,
            'Pasajeros Beneficiados': pasajeros,
            'Relación Asignación/Ruta': total_asignaciones / total_rutas if total_rutas else 0
        })

    df_modelos = pd.DataFrame(df_modelos)

    # Crear carpeta si no existe
    os.makedirs(DIRECTORIO_SALIDA, exist_ok=True)

    # --- 1. Gráfico combinado: Rutas únicas y totales por modelo ---
    df_melt = df_modelos.melt(id_vars='Modelo',
                              value_vars=['Rutas Dinámicas Únicas', 'Rutas Dinámicas Totales'],
                              var_name='Tipo de Ruta',
                              value_name='Cantidad')

    grafico_modelos(df_melt, 'Cantidad', '',
                    'rutas_dinamicas_modelo.png', hue='Tipo de Ruta', palette=["#171796", "#6a6aed"])

    # --- 2. Asignaciones totales ---
    grafico_modelos(df_modelos, 'Asignaciones Totales', '',
                    'asignaciones_totales_modelo.png')

    # --- 3. Relación Asignación/Ruta ---
    grafico_modelos(df_modelos, 'Relación Asignación/Ruta', '',
                    'relacion_asignacion_ruta_modelo.png')

    # --- 4. Pasajeros beneficiados ---
    grafico_modelos(df_modelos, 'Pasajeros Beneficiados', '',
                    'pasajeros_beneficiados_modelo.png')

    # --- TOP 10 RUTAS CON MÁS ASIGNACIONES ---
    top_asignaciones = frecuencias_totales.most_common(10)
    df_top_asignaciones = pd.DataFrame([
        {'Ruta': f'{origen} → {destino}', 'Asignaciones': asignaciones}
        for (origen, destino), asignaciones in top_asignaciones
    ])

    grafico_rutas(df_top_asignaciones, 'Asignaciones',
                  '',
                  'top10_asignaciones_rutas.png')

    # --- TOP 10 RUTAS CON MÁS PASAJEROS ---
    top_pasajeros = sorted(pasajeros_totales.items(), key=lambda x: x[1], reverse=True)[:10]
    df_top_pasajeros = pd.DataFrame([
        {'Ruta': f'{origen} → {destino}', 'Pasajeros': pasajeros}
        for (origen, destino), pasajeros in top_pasajeros
    ])

    grafico_rutas(df_top_pasajeros, 'Pasajeros',
                  '',
                  'top10_pasajeros_rutas.png')


if __name__ == "__main__":
    main()