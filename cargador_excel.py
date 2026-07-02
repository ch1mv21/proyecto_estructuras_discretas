#Evaluacion 03 Estructuras Discretas
#Autores: Jose Herrera - Manuel Soto - Tomas Diaz
#Academico: Eric Lillo
#Fecha:01/07/2026

import pandas as pd
from enlace import Enlace

class CargadorExcel:
    @staticmethod
    def cargar_red(ruta_archivo):
        enlaces = []
        try:
            # Detecta de manera simple si es un archivo CSV o Excel convencional
            if ruta_archivo.endswith('.csv'):
                df = pd.read_csv(ruta_archivo)
            else:
                df = pd.read_excel(ruta_archivo)
            
            # SOLUCIÓN AL ERROR: Normaliza columnas (Quita espacios extras y cambia ' ' por '_')
            df.columns = df.columns.str.strip().str.replace(' ', '_')
            
            # Validamos que existan los campos necesarios usando el nuevo formato unificado
            columnas_necesarias = ['ID', 'Origen', 'Destino', 'Latencia', 'Costo_CLP', 'Ancho_Banda']
            for col in columnas_necesarias:
                if col not in df.columns:
                    raise ValueError(f"Falta la columna requerida en el archivo: '{col}'")
            
            # Recorremos el DataFrame y creamos los objetos correspondientes
            for _, fila in df.iterrows():
                nuevo_enlace = Enlace(
                    id_enlace=fila['ID'],
                    origen=str(fila['Origen']).strip(),
                    destino=str(fila['Destino']).strip(),
                    latencia=fila['Latencia'],
                    costo=fila['Costo_CLP'],
                    ancho_banda=fila['Ancho_Banda']
                )
                enlaces.append(nuevo_enlace)
            
            print(f"\n[Éxito] Se procesaron correctamente {len(enlaces)} registros de enlaces.")
            
        except Exception as e:
            print(f"\n[Error] No se pudo procesar el archivo: {e}")
            
        return enlaces