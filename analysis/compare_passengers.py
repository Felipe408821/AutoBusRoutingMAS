import glob
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import StringIO
import numpy as np

# Configurar estilo de gráficos
sns.set_theme(style="whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)

def parse_custom_csv(file_path):
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()

        # Procesar las líneas para obtener datos limpios
        clean_lines = []
        for line in lines:
            if line.strip().startswith("'],['"):
                # Limpiar la línea
                clean_line = (line.replace("'],['", "")
                              .replace("'", "")
                              .replace(" ", "")
                              .replace("','", "")
                              .replace("'", "")
                              .replace("\n", "").strip())
                clean_lines.append(clean_line)

        # Crear DataFrame desde las líneas limpias
        if not clean_lines:
            print(f"Advertencia: No se encontraron datos de pasajeros en {file_path}")
            return pd.DataFrame()

        # Crear un CSV temporal en memoria
        csv_data = StringIO("\n".join(clean_lines))
        df = pd.read_csv(csv_data, header=None)
        del df[5]

        # Asignar nombres de columnas
        if len(df.columns) >= 4:
            df.columns = ['pasajero', 'tiempo_espera', 'tiempo_viaje', 'tiempo_transbordo', 'tiempo_total']
        else:
            print(f"Advertencia: Número insuficiente de columnas en {file_path}")
            return pd.DataFrame()

        # Convertir columnas numéricas
        numeric_cols = ['tiempo_espera', 'tiempo_viaje', 'tiempo_transbordo', 'tiempo_total']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        return df

    except Exception as e:
        print(f"Error al procesar {file_path}: {str(e)}")
        return pd.DataFrame()


def calculate_metrics(df, label):
    """Calcula métricas para un DataFrame individual"""
    if df.empty:
        return {
            'label': label,
            'total_passengers': 0,
            'arrived_passengers': 0,
            'arrived_percentage': 0,
            'avg_wait_time': None,
            'avg_travel_time': None,
            'avg_transfer_time': None,
            'avg_total_time': None,
            'max_total_time': None,
            'min_total_time': None,
            'std_total_time': None  # Nueva métrica: desviación estándar
        }

    # Filtrar pasajeros que llegaron a destino
    arrived = df[df['tiempo_total'] > 0]

    metrics = {
        'label': label,
        'total_passengers': len(df),
        'arrived_passengers': len(arrived),
        'arrived_percentage': (len(arrived) / len(df)) * 100 if len(df) > 0 else 0,
        'avg_wait_time': arrived['tiempo_espera'].mean() if not arrived.empty else None,
        'avg_travel_time': arrived['tiempo_viaje'].mean() if not arrived.empty else None,
        'avg_transfer_time': arrived['tiempo_transbordo'].mean() if not arrived.empty else None,
        'avg_total_time': arrived['tiempo_total'].mean() if not arrived.empty else None,
        'max_total_time': arrived['tiempo_total'].max() if not arrived.empty else None,
        'min_total_time': arrived['tiempo_total'].min() if not arrived.empty else None,
        'std_total_time': arrived['tiempo_total'].std() if not arrived.empty else None
    }
    return metrics


def process_model_files(file_pattern, model_name):
    """Procesa todos los archivos de un modelo y calcula métricas agregadas"""
    all_files = glob.glob(file_pattern)
    if not all_files:
        print(f"Advertencia: No se encontraron archivos para el patrón {file_pattern}")
        return None

    # Lista para almacenar métricas de cada ejecución
    all_metrics = []

    # Procesar cada archivo individualmente
    for file in all_files:
        df = parse_custom_csv(file)
        metrics = calculate_metrics(df, f"{model_name} - Ejecución")
        all_metrics.append(metrics)

    # Crear DataFrame con todas las métricas
    metrics_df = pd.DataFrame(all_metrics)

    # Calcular métricas agregadas (promedio de todas las ejecuciones)
    aggregated_metrics = {
        'label': model_name,
        'total_passengers': metrics_df['total_passengers'].mean(),
        'arrived_passengers': metrics_df['arrived_passengers'].mean(),
        'arrived_percentage': metrics_df['arrived_percentage'].mean(),
        'avg_wait_time': metrics_df['avg_wait_time'].mean(),
        'avg_travel_time': metrics_df['avg_travel_time'].mean(),
        'avg_transfer_time': metrics_df['avg_transfer_time'].mean(),
        'avg_total_time': metrics_df['avg_total_time'].mean(),
        'max_total_time': metrics_df['max_total_time'].max(),  # Tomamos el máximo de todos los máximos
        'min_total_time': metrics_df['min_total_time'].min(),  # Tomamos el mínimo de todos los mínimos
        'std_total_time': metrics_df['std_total_time'].mean(),  # Promedio de las desviaciones
        'num_executions': len(all_files),  # Número de ejecuciones procesadas
        'std_arrived_percentage': metrics_df['arrived_percentage'].std(),  # Variabilidad entre ejecuciones
        'std_avg_total_time': metrics_df['avg_total_time'].std()  # Variabilidad del tiempo promedio
    }

    return aggregated_metrics, metrics_df


def compare_models(model1_pattern, model2_pattern, model1_name="Modelo 1", model2_name="Modelo 2"):
    """Compara dos modelos procesando múltiples ejecuciones de cada uno"""
    # Procesar archivos del primer modelo
    model1_agg, model1_all = process_model_files(model1_pattern, model1_name)
    model2_agg, model2_all = process_model_files(model2_pattern, model2_name)

    # Crear DataFrame de comparación
    comparison_df = pd.DataFrame([model1_agg, model2_agg]).set_index('label')

    # Calcular diferencias estadísticas
    comparison_df.loc['Diferencia'] = comparison_df.iloc[1] - comparison_df.iloc[0]
    comparison_df.loc['% Cambio'] = (comparison_df.iloc[1] - comparison_df.iloc[0]) / comparison_df.iloc[0].abs() * 100

    # Mostrar resultados detallados
    print("\n=== Comparación entre modelos ===")
    print(comparison_df[['num_executions', 'total_passengers', 'arrived_passengers',
                         'arrived_percentage', 'std_arrived_percentage']])

    print("\n=== Tiempos promedio ===")
    print(comparison_df[['avg_wait_time', 'avg_travel_time', 'avg_transfer_time',
                         'avg_total_time', 'std_avg_total_time']])

    print("\n=== Tiempos extremos ===")
    print(comparison_df[['min_total_time', 'max_total_time']])

    print("\n=== Variabilidad entre ejecuciones ===")
    print(comparison_df[['std_arrived_percentage', 'std_avg_total_time']])

    return {
        'comparison': comparison_df,
        'model1_details': model1_all,
        'model2_details': model2_all
    }


def compare_models_with_plots(model1_pattern, model2_pattern, model1_name="Baseline", model2_name="BDI"):
    """Compara dos modelos con TODOS los gráficos en una sola figura"""
    # 1. Procesar datos
    results = compare_models(model1_pattern, model2_pattern, model1_name, model2_name)
    model1_df = results['model1_details']
    model2_df = results['model2_details']
    comparison_df = results['comparison'].iloc[:2]

    # Datos brutos para gráficos detallados (usamos la primera ejecución de cada modelo)
    df_basico = parse_custom_csv(glob.glob(model1_pattern)[0])
    df_bdi = parse_custom_csv(glob.glob(model2_pattern)[0])

    # 2. Configurar figura maestra
    fig = plt.figure(figsize=(20, 24))
    plt.suptitle(f"Comparación Completa: {model1_name} vs {model2_name}", fontsize=16, y=1.02)

    # --- GRÁFICOS SUPERIORES (Métricas agregadas) ---
    # Gráfico 1: Boxplot de tiempos entre ejecuciones
    ax1 = plt.subplot2grid((4, 3), (0, 0), colspan=1)
    combined_data = pd.concat([model1_df.assign(Modelo=model1_name), model2_df.assign(Modelo=model2_name)])
    sns.boxplot(data=combined_data, x='Modelo', y='avg_total_time', hue='Modelo', palette="Set2", ax=ax1, legend=False)
    ax1.set_title("Distribución de Tiempos Totales\n(Entre Ejecuciones)")
    ax1.set_ylabel("Tiempo Promedio (s)")

    # Gráfico 2: Porcentaje de llegada
    ax2 = plt.subplot2grid((4, 3), (0, 1), colspan=1)
    sns.barplot(data=comparison_df.reset_index(), x='label', y='arrived_percentage', hue='label',
                palette="pastel", ax=ax2, legend=False)
    ax2.errorbar(x=range(len(comparison_df)), y=comparison_df['arrived_percentage'],
                 yerr=comparison_df['std_arrived_percentage'], fmt='none', color='black', capsize=5)
    ax2.set_title("Porcentaje de Pasajeros que Llegan")
    ax2.set_ylim(0, 100)

    # Gráfico 3: Evolución por ejecución
    ax3 = plt.subplot2grid((4, 3), (0, 2), colspan=1)
    sns.lineplot(data=model1_df, x=model1_df.index, y='avg_total_time', label=model1_name, marker='o', ax=ax3)
    sns.lineplot(data=model2_df, x=model2_df.index, y='avg_total_time', label=model2_name, marker='s', ax=ax3)
    ax3.set_title("Tiempo Promedio por Ejecución")
    ax3.set_xlabel("Nº Ejecución")

    # --- GRÁFICOS INFERIORES (Análisis detallado) ---
    # Gráfico 4: Distribución tiempos de espera (CORREGIDO)
    ax4 = plt.subplot2grid((4, 3), (1, 0), colspan=1)
    sns.boxplot(
        data=pd.concat([
            df_basico['tiempo_espera'].rename(model1_name),
            df_bdi['tiempo_espera'].rename(model2_name)
        ]),
        ax=ax4
    )
    ax4.set_title("Distribución Tiempos de Espera")
    ax4.set_ylabel("Segundos")

    # Gráfico 5: KDE de tiempos totales
    ax5 = plt.subplot2grid((4, 3), (1, 1), colspan=1)
    sns.kdeplot(df_basico['tiempo_total'], label=model1_name, ax=ax5, fill=True, alpha=0.3)
    sns.kdeplot(df_bdi['tiempo_total'], label=model2_name, ax=ax5, fill=True, alpha=0.3)
    ax5.set_title("Distribución Tiempos Totales")
    ax5.set_xlabel("Segundos")

    # Gráfico 6: Porcentaje con transbordo
    ax6 = plt.subplot2grid((4, 3), (1, 2), colspan=1)
    transbordo_data = pd.DataFrame({
        'Modelo': [model1_name, model2_name],
        'Porcentaje': [
            (df_basico['tiempo_transbordo'] > 0).mean() * 100,
            (df_bdi['tiempo_transbordo'] > 0).mean() * 100
        ]
    })
    sns.barplot(x='Modelo', y='Porcentaje', data=transbordo_data, ax=ax6)
    ax6.set_title("Pasajeros con Transbordo")
    ax6.set_ylim(0, 100)

    # Gráfico 7: Scatter espera vs viaje
    ax7 = plt.subplot2grid((4, 3), (2, 0), colspan=1)
    ax7.scatter(df_basico['tiempo_espera'], df_basico['tiempo_viaje'], alpha=0.5, label=model1_name)
    ax7.scatter(df_bdi['tiempo_espera'], df_bdi['tiempo_viaje'], alpha=0.5, label=model2_name)
    ax7.set_title("Relación Espera vs Viaje")
    ax7.set_xlabel("Tiempo Espera (s)")
    ax7.set_ylabel("Tiempo Viaje (s)")
    ax7.legend()

    # Gráfico 8: Percentiles
    ax8 = plt.subplot2grid((4, 3), (2, 1), colspan=1)
    percentiles = np.arange(0, 100, 5)
    ax8.plot(percentiles, np.percentile(df_basico['tiempo_total'], percentiles), label=model1_name, marker='o')
    ax8.plot(percentiles, np.percentile(df_bdi['tiempo_total'], percentiles), label=model2_name, marker='o')
    ax8.set_title("Percentiles de Tiempo Total")
    ax8.set_xlabel("Percentil")
    ax8.set_ylabel("Tiempo (s)")
    ax8.grid(True)

    # Gráfico 9: Diferencias de medias
    ax9 = plt.subplot2grid((4, 3), (2, 2), colspan=1)
    metricas = ['tiempo_espera', 'tiempo_viaje', 'tiempo_total']
    diferencias = {
        'Métrica': metricas,
        'Diferencia': [df_bdi[metrica].mean() - df_basico[metrica].mean() for metrica in metricas]
    }
    sns.barplot(x='Diferencia', y='Métrica', data=pd.DataFrame(diferencias), ax=ax9)
    ax9.set_title("Diferencia de Medias (BDI - Baseline)")
    ax9.axvline(0, color='gray', linestyle='--')

    # Ajustar layout y guardar
    plt.tight_layout()
    plt.savefig('results/compare_passengers.png', dpi=300, bbox_inches='tight')
    plt.close()

    return results


if __name__ == "__main__":
    # Patrones de archivos para cada modelo
    baseline_pattern = "../experimental_tests/BAS-01/passengers_*.csv"
    bdi_pattern = "../experimental_tests/BDI-01/passengers_*.csv"

    # Comparar modelos
    results = compare_models_with_plots(
        baseline_pattern,
        bdi_pattern,
        model1_name="Baseline Model",
        model2_name="BDI Model"
    )
