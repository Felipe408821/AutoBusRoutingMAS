import pandas as pd
from io import StringIO


def parse_custom_csv(file_path):
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()

        # Procesar las líneas para obtener datos limpios
        clean_lines = []
        for line in lines:
            if line.strip().startswith("'],['"):
                # Limpiar la línea
                clean_line = line.replace("'", "").replace("[", "").replace("]", "").replace("\n", "").strip()
                clean_lines.append(clean_line)

        # Crear DataFrame desde las líneas limpias
        if not clean_lines:
            print(f"Advertencia: No se encontraron datos de pasajeros en {file_path}")
            return pd.DataFrame()

        # Crear un CSV temporal en memoria
        csv_data = StringIO("\n".join(clean_lines))
        df = pd.read_csv(csv_data, header=None)

        # Asignar nombres de columnas (basado en el ejemplo que proporcionaste)
        if len(df.columns) >= 6:
            df.columns = ['n', 'Pasajero', 'tiempo_espera', 'tiempo_viaje', 'tiempo_transbordo', 'tiempo_total'] + list(
                df.columns[6:])
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


def analyze_passenger_data(file1, file2, label1="Dataset 1", label2="Dataset 2"):
    # Leer los archivos CSV
    df1 = parse_custom_csv(file1)
    df2 = parse_custom_csv(file2)

    # Verificar que tenemos las columnas necesarias
    required_columns = ['tiempo_espera', 'tiempo_viaje', 'tiempo_transbordo', 'tiempo_total']
    for df, label in [(df1, label1), (df2, label2)]:
        if not df.empty:
            missing_cols = [col for col in required_columns if col not in df.columns]
            if missing_cols:
                print(f"Advertencia: Faltan columnas en {label}: {', '.join(missing_cols)}")

    # Función para calcular métricas
    def calculate_metrics(df, label):
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
                'min_total_time': None
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
            'min_total_time': arrived['tiempo_total'].min() if not arrived.empty else None
        }
        return metrics

    # Calcular métricas
    metrics1 = calculate_metrics(df1, label1)
    metrics2 = calculate_metrics(df2, label2)

    # Crear DataFrame de comparación
    comparison_df = pd.DataFrame([metrics1, metrics2]).set_index('label')

    # Solo calcular diferencias si ambos datasets tienen datos
    if not df1.empty and not df2.empty:
        comparison_df.loc['Diferencia'] = comparison_df.iloc[1] - comparison_df.iloc[0]
        comparison_df.loc['% Cambio'] = (comparison_df.iloc[1] - comparison_df.iloc[0]) / comparison_df.iloc[0] * 100
    else:
        print("Advertencia: No se pueden calcular diferencias porque uno o ambos datasets están vacíos")

    # Mostrar resultados
    print("\n=== Comparación entre ambos datasets ===")
    print(comparison_df[['total_passengers', 'arrived_passengers', 'arrived_percentage']])

    print("\n=== Tiempos promedio (solo pasajeros que llegaron) ===")
    print(comparison_df[['avg_wait_time', 'avg_travel_time', 'avg_transfer_time', 'avg_total_time']])

    print("\n=== Tiempos totales extremos ===")
    print(comparison_df[['min_total_time', 'max_total_time']])

    return comparison_df


# Ejemplo de uso
if __name__ == "__main__":
    resultados = analyze_passenger_data(
        '../experimental_tests/BAS-01/passengers_results_viejo.csv',
        '../experimental_tests/BDI-01/passengers_results_basic.csv',
        'VIEJO',
        'NUEVO'
    )
    if resultados is not None:
        print("\nAnálisis completado exitosamente")