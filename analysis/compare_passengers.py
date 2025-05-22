import glob
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import StringIO
import numpy as np
from itertools import combinations

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
            'std_total_time': None,
            'median_total_time': None
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
        'std_total_time': arrived['tiempo_total'].std() if not arrived.empty else None,
        'median_total_time': arrived['tiempo_total'].median() if not arrived.empty else None
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
        'max_total_time': metrics_df['max_total_time'].max(),
        'min_total_time': metrics_df['min_total_time'].min(),
        'std_total_time': metrics_df['std_total_time'].mean(),
        'median_total_time': metrics_df['median_total_time'].mean(),
        'num_executions': len(all_files),
        'std_arrived_percentage': metrics_df['arrived_percentage'].std(),
        'std_avg_total_time': metrics_df['avg_total_time'].std()
    }

    return aggregated_metrics, metrics_df


def compare_multiple_models(model_patterns):
    """
    Compara múltiples modelos dados como un diccionario {nombre_modelo: patrón_archivo}
    Devuelve un DataFrame con las métricas agregadas de todos los modelos
    """
    all_metrics = []
    all_details = {}

    for model_name, pattern in model_patterns.items():
        agg_metrics, detail_metrics = process_model_files(pattern, model_name)
        if agg_metrics is not None:
            all_metrics.append(agg_metrics)
            all_details[model_name] = detail_metrics

    if not all_metrics:
        print("Advertencia: No se encontraron datos válidos para ningún modelo")
        return None, None

    comparison_df = pd.DataFrame(all_metrics).set_index('label')

    return comparison_df, all_details


def generate_pairwise_comparisons(comparison_df):
    """
    Genera comparaciones por pares entre todos los modelos
    """
    model_names = comparison_df.index.tolist()
    all_comparisons = {}

    for (model1, model2) in combinations(model_names, 2):
        diff_df = pd.DataFrame()
        diff_df['Diferencia'] = comparison_df.loc[model2] - comparison_df.loc[model1]
        diff_df['% Cambio'] = (comparison_df.loc[model2] - comparison_df.loc[model1]) / comparison_df.loc[
            model1].abs() * 100
        all_comparisons[f"{model2} vs {model1}"] = diff_df

    return all_comparisons


def plot_aggregated_comparison(comparison_df, title="Comparación de Modelos"):
    """
    Crea gráficos comparativos para múltiples modelos con tiempos en minutos
    """
    # Convertir segundos a minutos en las columnas relevantes
    time_cols = ['avg_wait_time', 'avg_travel_time', 'avg_total_time',
                 'max_total_time', 'min_total_time', 'median_total_time',
                 'std_total_time', 'std_avg_total_time']

    # Crear copia para no modificar el DataFrame original
    plot_df = comparison_df.copy()
    plot_df[time_cols] = plot_df[time_cols] / 60

    num_models = len(plot_df)
    fig, axes = plt.subplots(3, 2, figsize=(18, 16))
    fig.suptitle(title, fontsize=16, y=1.02)

    # Gráfico 1: Porcentaje de llegada
    ax = axes[0, 0]
    sns.barplot(data=plot_df.reset_index(), x='label', y='arrived_percentage',
                hue='label', palette="pastel", ax=ax, legend=False)
    ax.errorbar(x=range(num_models), y=plot_df['arrived_percentage'],
                yerr=plot_df['std_arrived_percentage'], fmt='none', color='black', capsize=5)
    ax.set_title("Porcentaje de Pasajeros que Llegaron")
    ax.set_ylim(0, 100)
    ax.tick_params(axis='x', rotation=45)

    # Gráfico 2: Tiempo total promedio (ahora en minutos)
    ax = axes[0, 1]
    sns.barplot(data=plot_df.reset_index(), x='label', y='avg_total_time',
                hue='label', palette="pastel", ax=ax, legend=False)
    ax.errorbar(x=range(num_models), y=plot_df['avg_total_time'],
                yerr=plot_df['std_avg_total_time'], fmt='none', color='black', capsize=5)
    ax.set_title("Tiempo Total Promedio (minutos)")
    ax.tick_params(axis='x', rotation=45)

    # Gráfico 3: Tiempos de espera vs viaje (en minutos)
    ax = axes[1, 0]
    plot_df.reset_index()[['label', 'avg_wait_time', 'avg_travel_time']].melt(
        id_vars='label').pipe(
        (sns.barplot, 'data'), x='label', y='value', hue='variable', ax=ax)
    ax.set_title("Descomposición de Tiempos (Espera vs Viaje)")
    ax.set_ylabel("Minutos")
    ax.legend(title="Tipo de Tiempo")
    ax.tick_params(axis='x', rotation=45)

    # Gráfico 4: Variabilidad entre ejecuciones (convertir std a minutos)
    ax = axes[1, 1]
    plot_df['std_avg_total_time_min'] = plot_df['std_avg_total_time'] / 60
    plot_df['std_arrived_percentage'] = plot_df['std_arrived_percentage']
    plot_df.reset_index()[['label', 'std_arrived_percentage', 'std_avg_total_time_min']].melt(
        id_vars='label').pipe(
        (sns.barplot, 'data'), x='label', y='value', hue='variable', ax=ax)
    ax.set_title("Variabilidad entre Ejecuciones")
    ax.legend(title="Métrica")
    ax.set_ylabel("Valor")
    ax.tick_params(axis='x', rotation=45)

    # Gráfico 5: Tiempos extremos (en minutos)
    ax = axes[2, 0]
    plot_df.reset_index()[['label', 'min_total_time', 'median_total_time', 'max_total_time']].melt(
        id_vars='label').pipe(
        (sns.barplot, 'data'), x='label', y='value', hue='variable', ax=ax)
    ax.set_title("Tiempos Extremos y Mediana")
    ax.set_ylabel("Minutos")
    ax.legend(title="Métrica")
    ax.tick_params(axis='x', rotation=45)

    # Gráfico 6: Pasajeros procesados
    ax = axes[2, 1]
    plot_df.reset_index()[['label', 'total_passengers', 'arrived_passengers']].melt(
        id_vars='label').pipe(
        (sns.barplot, 'data'), x='label', y='value', hue='variable', ax=ax)
    ax.set_title("Pasajeros Totales vs Pasajeros que Llegaron")
    ax.legend(title="Tipo")
    ax.tick_params(axis='x', rotation=45)

    plt.tight_layout()
    plt.savefig('results/passengers/multi_model_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()

    return fig


def plot_detailed_comparison(model_details, model_names, title="Comparación Detallada"):
    """
    Crea gráficos detallados con tiempos en minutos
    """
    # Obtener datos de la primera ejecución para cada modelo
    first_exec_dfs = {}
    for name in model_names:
        pattern = model_patterns[name]
        first_file = glob.glob(pattern)[0]
        df = parse_custom_csv(first_file)
        # Convertir a minutos
        time_cols = ['tiempo_espera', 'tiempo_viaje', 'tiempo_transbordo', 'tiempo_total']
        df[time_cols] = df[time_cols] / 60
        first_exec_dfs[name] = df

    # Configurar figura
    fig = plt.figure(figsize=(20, 16))
    plt.suptitle(title, fontsize=16, y=1.02)

    # Gráfico 1: Distribución tiempos totales (minutos)
    ax1 = plt.subplot2grid((3, 3), (0, 0), colspan=1)
    for name, df in first_exec_dfs.items():
        sns.kdeplot(df['tiempo_total'], label=name, ax=ax1, fill=True, alpha=0.3)
    ax1.set_title("Distribución Tiempos Totales")
    ax1.set_xlabel("Minutos")
    ax1.legend()

    # Gráfico 2: Boxplot tiempos por modelo (minutos)
    ax2 = plt.subplot2grid((3, 3), (0, 1), colspan=1)
    plot_data = pd.concat([df['tiempo_total'].rename(name) for name, df in first_exec_dfs.items()], axis=1)
    sns.boxplot(data=plot_data, ax=ax2)
    ax2.set_title("Distribución Tiempos Totales")
    ax2.set_ylabel("Minutos")

    # Gráfico 3: Porcentaje con transbordo
    ax3 = plt.subplot2grid((3, 3), (0, 2), colspan=1)
    transbordo_data = pd.DataFrame({
        'Modelo': list(first_exec_dfs.keys()),
        'Porcentaje': [(df['tiempo_transbordo'] > 0).mean() * 100 for df in first_exec_dfs.values()]
    })
    sns.barplot(x='Modelo', y='Porcentaje', data=transbordo_data, ax=ax3)
    ax3.set_title("Pasajeros con Transbordo")
    ax3.set_ylim(0, 100)

    # Gráfico 4: Percentiles (minutos)
    ax4 = plt.subplot2grid((3, 3), (1, 0), colspan=1)
    percentiles = np.arange(0, 100, 5)
    for name, df in first_exec_dfs.items():
        ax4.plot(percentiles, np.percentile(df['tiempo_total'], percentiles), label=name, marker='o')
    ax4.set_title("Percentiles de Tiempo Total")
    ax4.set_xlabel("Percentil")
    ax4.set_ylabel("Minutos")
    ax4.grid(True)
    ax4.legend()

    # Gráfico 5: Relación espera vs viaje (minutos)
    ax5 = plt.subplot2grid((3, 3), (1, 1), colspan=1)
    for name, df in first_exec_dfs.items():
        ax5.scatter(df['tiempo_espera'], df['tiempo_viaje'], alpha=0.5, label=name)
    ax5.set_title("Relación Espera vs Viaje")
    ax5.set_xlabel("Tiempo Espera (minutos)")
    ax5.set_ylabel("Tiempo Viaje (minutos)")
    ax5.legend()

    # Gráfico 6: Distribución tiempos de espera (minutos)
    ax6 = plt.subplot2grid((3, 3), (1, 2), colspan=1)
    for name, df in first_exec_dfs.items():
        sns.kdeplot(df['tiempo_espera'], label=name, ax=ax6, fill=True, alpha=0.3)
    ax6.set_title("Distribución Tiempos de Espera")
    ax6.set_xlabel("Minutos")
    ax6.legend()

    # Gráfico 7: Evolución de métricas por ejecución (convertir a minutos)
    ax7 = plt.subplot2grid((3, 3), (2, 0), colspan=3)
    for name in model_names:
        if name in model_details:
            df = model_details[name].copy()
            df['avg_total_time'] = df['avg_total_time'] / 60
            df['std_total_time'] = df['std_total_time'] / 60
            ax7.plot(df.index, df['avg_total_time'], label=f"{name} (promedio)", marker='o')
            ax7.fill_between(df.index,
                             df['avg_total_time'] - df['std_total_time'],
                             df['avg_total_time'] + df['std_total_time'],
                             alpha=0.1)
    ax7.set_title("Evolución del Tiempo Total por Ejecución")
    ax7.set_xlabel("Nº Ejecución")
    ax7.set_ylabel("Tiempo Promedio (minutos)")
    ax7.legend()
    ax7.grid(True)

    plt.tight_layout()
    plt.savefig('results/passengers/multi_model_detailed.png', dpi=300, bbox_inches='tight')
    plt.close()

    return fig


if __name__ == "__main__":
    # Definir los modelos a comparar como un diccionario {nombre: patrón}
    model_patterns = {
        "BAS-01": "../experimental_tests/BAS-01/*_passengers_results.csv",
        #"BAS-02": "../experimental_tests/BAS-02/*_passengers_results.csv",
        "BAS-03": "../experimental_tests/BAS-03/*_passengers_results.csv",
        "BDI-01": "../experimental_tests/BDI-01/*_passengers_results.csv",
        #"BDI-02": "../experimental_tests/BDI-02/*_passengers_results.csv",
        #"BDI-03": "../experimental_tests/BDI-03/*_passengers_results.csv"
    }

    # Comparar todos los modelos
    comparison_df, model_details = compare_multiple_models(model_patterns)

    if comparison_df is not None:
        # Mostrar resultados en consola
        print("\n=== Métricas Agregadas para Todos los Modelos ===")
        print(comparison_df[['num_executions', 'total_passengers', 'arrived_passengers',
                             'arrived_percentage', 'std_arrived_percentage',
                             'avg_total_time', 'std_avg_total_time']])

        # Generar comparaciones por pares
        pairwise_comparisons = generate_pairwise_comparisons(comparison_df)
        for comparison_name, diff_df in pairwise_comparisons.items():
            print(f"\n=== Comparación: {comparison_name} ===")
            print(diff_df)

        # Generar gráficos
        plot_aggregated_comparison(comparison_df)
        plot_detailed_comparison(model_details, model_patterns.keys())

        # Guardar resultados en CSV
        comparison_df.to_csv('results/passengers/model_comparison.csv')
        print("\nResultados guardados en 'results/passengers/model_comparison.csv'")
