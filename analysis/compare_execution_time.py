import os
import numpy as np
from glob import glob
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


def calcular_tiempos_modelo(carpeta):
    """
    Calcula los tiempos de ejecución para un modelo específico.
    Devuelve un diccionario con estadísticas del modelo.
    """
    tiempos = []

    if not os.path.exists(carpeta):
        raise FileNotFoundError(f"La carpeta {carpeta} no existe")

    archivos_tiempo = glob(os.path.join(carpeta, '*_execution_time.csv'))

    if not archivos_tiempo:
        raise ValueError(f"No se encontraron archivos *_execution_time.csv en {carpeta}")

    for archivo in archivos_tiempo:
        try:
            with open(archivo, 'r') as f:
                lineas = f.readlines()
                if len(lineas) >= 2:
                    tiempo_str = lineas[1].strip()
                    tiempo = float(tiempo_str.strip('[]'))
                    tiempos.append(tiempo)
                else:
                    print(f"Advertencia: Archivo {os.path.basename(archivo)} no tiene formato esperado")
        except Exception as e:
            print(f"Error al procesar {os.path.basename(archivo)}: {e}")

    if not tiempos:
        raise ValueError(f"No se pudieron extraer tiempos válidos de {carpeta}")

    return {
        'Modelo': os.path.basename(carpeta),
        'Tiempo Promedio': np.mean(tiempos),
        'Tiempo Mínimo': np.min(tiempos),
        'Tiempo Máximo': np.max(tiempos),
        'Desviación Estándar': np.std(tiempos),
        'Número de Ejecuciones': len(tiempos)
    }


def generar_grafico(resultados):
    """
    Genera un gráfico de barras con los tiempos promedios de cada modelo.
    """
    # Crear DataFrame
    df = pd.DataFrame(resultados)
    df = df.sort_values('Tiempo Promedio')

    # Configurar el estilo del gráfico
    plt.figure(figsize=(12, 6))
    sns.set_style("whitegrid")

    # Crear gráfico de barras
    ax = sns.barplot(
        x='Modelo',
        y='Tiempo Promedio',
        data=df,
        legend=False,
        errorbar=None
    )

    # Añadir barras de error (rango min-max)
    for i, modelo in enumerate(df['Modelo']):
        min_val = df.loc[df['Modelo'] == modelo, 'Tiempo Mínimo'].values[0]
        max_val = df.loc[df['Modelo'] == modelo, 'Tiempo Máximo'].values[0]
        plt.errorbar(
            x=i,
            y=df.loc[df['Modelo'] == modelo, 'Tiempo Promedio'].values[0],
            yerr=[[df.loc[df['Modelo'] == modelo, 'Tiempo Promedio'].values[0] - min_val],
                  [max_val - df.loc[df['Modelo'] == modelo, 'Tiempo Promedio'].values[0]]],
            fmt='none',
            color='black',
            capsize=5
        )

    # Personalizar el gráfico
    plt.title('Comparación de Tiempos de Ejecución entre Modelos', fontsize=16, pad=20)
    plt.xlabel('Modelos', fontsize=12)
    plt.ylabel('Tiempo Promedio (segundos)', fontsize=12)
    plt.xticks(rotation=45, ha='right')

    # Añadir valores encima de las barras
    for p in ax.patches:
        ax.annotate(
            f"{p.get_height():.2f}s",
            (p.get_x() + p.get_width() / 2., p.get_height()),
            ha='center',
            va='center',
            xytext=(0, 10),
            textcoords='offset points',
            fontsize=10
        )

    # Ajustar layout
    plt.tight_layout()

    # Guardar el gráfico
    plt.savefig('results/compare_execution_time.png', dpi=300, bbox_inches='tight')
    print("\nGráfico guardado como 'compare_execution_time.png'")

    # Mostrar el gráfico
    plt.show()


def comparar_multiple_modelos(*carpetas_modelos):
    """
    Compara los tiempos de ejecución de múltiples modelos.
    """
    try:
        resultados = []

        for carpeta in carpetas_modelos:
            try:
                resultados.append(calcular_tiempos_modelo(carpeta))
            except Exception as e:
                print(f"Error procesando {carpeta}: {e}")
                continue

        if not resultados:
            raise ValueError("No se pudieron procesar ninguno de los modelos")

        # Crear DataFrame para análisis
        df = pd.DataFrame(resultados)
        df = df.sort_values('Tiempo Promedio')

        # Mostrar resultados en tabla
        print("\n" + "=" * 70)
        print("RESULTADOS COMPARATIVOS".center(70))
        print("=" * 70)
        print(df.to_string(index=False))

        # Generar y guardar gráfico
        generar_grafico(resultados)

        return df

    except Exception as e:
        print(f"\nError durante la comparación: {e}")
        return None


if __name__ == "__main__":
    modelos_a_comparar = [
        "../experimental_tests/BAS-01",
        "../experimental_tests/BAS-02",
        "../experimental_tests/BAS-03",
        "../experimental_tests/BDI-01",
        "../experimental_tests/BDI-02",
        "../experimental_tests/BDI-03"
    ]

    modelos_a_comparar = [m for m in modelos_a_comparar if os.path.exists(m)]

    if not modelos_a_comparar:
        print("Error: No se encontraron carpetas de modelos válidas para comparar")
    else:
        print(f"\nComparando {len(modelos_a_comparar)} modelos...")
        resultados_df = comparar_multiple_modelos(*modelos_a_comparar)