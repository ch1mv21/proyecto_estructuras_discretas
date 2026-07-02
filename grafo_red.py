#Evaluacion 03 Estructuras Discretas
#Autores: Jose Herrera - Manuel Soto - Tomas Diaz
#Academico: Eric Lillo
#Fecha:01/07/2026

import heapq
from router import Router
from enlace import Enlace


class GrafoRed:
    def __init__(self):
        self.lista_adyacencia = {}
        self.routers = {}

    # ─────────────────────────────────────────────
    #  GESTIÓN DE RED
    # ─────────────────────────────────────────────

    def agregar_enlace(self, enlace):
        if enlace.origen not in self.routers:
            self.routers[enlace.origen] = Router(enlace.origen)
            self.lista_adyacencia[enlace.origen] = []

        if enlace.destino not in self.routers:
            self.routers[enlace.destino] = Router(enlace.destino)
            self.lista_adyacencia[enlace.destino] = []

        self.lista_adyacencia[enlace.origen].append(enlace)
        self.lista_adyacencia[enlace.destino].append(enlace)

    def _buscar_enlace_por_id(self, id_enlace):
        """Devuelve el objeto Enlace con ese ID, o None si no existe."""
        vistos = set()
        for enlaces in self.lista_adyacencia.values():
            for e in enlaces:
                if e.id not in vistos:
                    vistos.add(e.id)
                    if str(e.id) == str(id_enlace):
                        return e
        return None

    def modificar_enlace(self, id_enlace, nueva_latencia=None, nuevo_costo=None, nuevo_ancho_banda=None):
        """
        Modifica los atributos de un enlace existente buscándolo por su ID.
        Solo actualiza los campos que se pasen como argumento (no-None).
        """
        enlace = self._buscar_enlace_por_id(id_enlace)
        if enlace is None:
            print(f"\n[Error] No existe ningún enlace con ID '{id_enlace}'.")
            return False

        cambios = []
        if nueva_latencia is not None:
            enlace.latencia = float(nueva_latencia)
            cambios.append(f"Latencia → {enlace.latencia} ms")
        if nuevo_costo is not None:
            enlace.costo = float(nuevo_costo)
            cambios.append(f"Costo → ${enlace.costo:,.0f} CLP")
        if nuevo_ancho_banda is not None:
            enlace.ancho_banda = float(nuevo_ancho_banda)
            cambios.append(f"Ancho de Banda → {enlace.ancho_banda} Mbps")

        if not cambios:
            print("\n[Aviso] No se especificó ningún campo para modificar.")
            return False

        print(f"\n[Éxito] Enlace [{id_enlace}] ({enlace.origen} <-> {enlace.destino}) actualizado:")
        for c in cambios:
            print(f"   • {c}")
        return True

    def eliminar_enlace(self, id_enlace):
        """
        Elimina el enlace con el ID indicado de todas las listas de adyacencia.
        Verifica que la red no quede desconectada tras la eliminación.
        """
        enlace = self._buscar_enlace_por_id(id_enlace)
        if enlace is None:
            print(f"\n[Error] No existe ningún enlace con ID '{id_enlace}'.")
            return False

        # Guardamos el estado activo original para poder revertir si es necesario
        estado_original = enlace.activo

        # Desactivamos temporalmente para simular la eliminación y verificar conectividad
        enlace.activo = False
        if not self._red_sigue_conectada():
            enlace.activo = estado_original
            print(f"\n[BLOQUEADO] No se puede eliminar el enlace [{id_enlace}].")
            print("Motivo: Su eliminación provocaría zonas aisladas en la red.")
            return False

        # Si la red sigue conectada, eliminamos físicamente el enlace de las listas
        for nodo in self.lista_adyacencia:
            self.lista_adyacencia[nodo] = [
                e for e in self.lista_adyacencia[nodo] if str(e.id) != str(id_enlace)
            ]

        print(f"\n[Éxito] Enlace [{id_enlace}] ({enlace.origen} <-> {enlace.destino}) eliminado correctamente.")
        return True

    def _red_sigue_conectada(self):
        """DFS para verificar que todos los nodos son alcanzables con enlaces activos."""
        nodos = list(self.routers.keys())
        if not nodos:
            return True

        visitados = set()
        pila = [nodos[0]]
        while pila:
            nodo_actual = pila.pop()
            if nodo_actual not in visitados:
                visitados.add(nodo_actual)
                for e in self.lista_adyacencia.get(nodo_actual, []):
                    if e.activo:
                        vecino = e.destino if e.origen == nodo_actual else e.origen
                        if vecino not in visitados:
                            pila.append(vecino)

        return len(visitados) == len(nodos)

    def eliminar_router(self, nombre_router):
        if nombre_router not in self.routers:
            print(f"\n[Error] El router '{nombre_router}' no existe en la red.")
            return False

        if self.es_punto_articulacion(nombre_router):
            print(f"\n[BLOQUEADO] No se puede eliminar '{nombre_router}'.")
            print("Motivo: Es un PUNTO DE ARTICULACIÓN. Su eliminación provocaría la desconexión de la red.")
            return False

        del self.routers[nombre_router]
        del self.lista_adyacencia[nombre_router]

        for nodo in self.lista_adyacencia:
            self.lista_adyacencia[nodo] = [
                e for e in self.lista_adyacencia[nodo]
                if e.origen != nombre_router and e.destino != nombre_router
            ]

        print(f"\n[Éxito] El router '{nombre_router}' y sus conexiones fueron eliminados correctamente.")
        return True

    # ─────────────────────────────────────────────
    #  REPRESENTACIÓN DEL GRAFO
    # ─────────────────────────────────────────────

    def mostrar_lista_adyacencia(self):
        if not self.routers:
            print("[Aviso] El grafo está vacío. Cargue un archivo primero.")
            return

        print("\n--- LISTA DE ADYACENCIA ---")
        for nodo, enlaces in self.lista_adyacencia.items():
            vecinos = []
            for e in enlaces:
                if e.activo:
                    vecino = e.destino if e.origen == nodo else e.origen
                    vecinos.append(f"{vecino}(id:{e.id})")
            print(f"Router {nodo} => Conectado con: [{', '.join(vecinos)}]")

    def mostrar_matriz_adyacencia(self):
        if not self.routers:
            print("[Aviso] El grafo está vacío. Cargue un archivo primero.")
            return

        nodos_ordenados = sorted(list(self.routers.keys()))
        n = len(nodos_ordenados)
        matriz = [[0] * n for _ in range(n)]
        mapeo_indices = {nodo: idx for idx, nodo in enumerate(nodos_ordenados)}

        for nodo, enlaces in self.lista_adyacencia.items():
            for e in enlaces:
                if e.activo:
                    u = mapeo_indices[e.origen]
                    v = mapeo_indices[e.destino]
                    matriz[u][v] = 1
                    matriz[v][u] = 1

        print("\n--- MATRIZ DE ADYACENCIA ---")
        print("   " + " ".join(nodos_ordenados))
        for idx, fila in enumerate(matriz):
            print(f"{nodos_ordenados[idx]}  " + " ".join(map(str, fila)))

    # ─────────────────────────────────────────────
    #  ANÁLISIS
    # ─────────────────────────────────────────────

    def analizar_conectividad(self):
        if not self.routers:
            print("\n[Aviso] El grafo está vacío. Cargue un archivo primero.")
            return

        nodo_inicial = list(self.routers.keys())[0]
        visitados = set()
        pila = [nodo_inicial]

        while pila:
            nodo_actual = pila.pop()
            if nodo_actual not in visitados:
                visitados.add(nodo_actual)
                for enlace in self.lista_adyacencia.get(nodo_actual, []):
                    if enlace.activo:
                        vecino = enlace.destino if enlace.origen == nodo_actual else enlace.origen
                        if vecino not in visitados:
                            pila.append(vecino)

        nodos_totales = set(self.routers.keys())
        nodos_aislados = nodos_totales - visitados

        print("\n" + "-" * 10 + " ANÁLISIS DE CONECTIVIDAD " + "-" * 10)
        if not nodos_aislados:
            print("[Resultado] La red está operando al 100%. No hay zonas aisladas.")
        else:
            print(f"[ALERTA CRÍTICA] Se detectó fragmentación en la red.")
            print(f"Los siguientes routers están aislados del router {nodo_inicial}:")
            print(f"-> Nodos inalcanzables: {', '.join(nodos_aislados)}")
        print("-" * 46)

    def analizar_ruta_optima(self, origen, destino):
        if origen not in self.routers or destino not in self.routers:
            print(f"\n[Error] El origen '{origen}' o destino '{destino}' no existen en la red.")
            return

        cola = [(0, 0, 0, origen, 0, 0, [origen])]
        mejor_metrica_visitado = {}

        while cola:
            lat_acum, neg_bw_prom, costo_acum, nodo_actual, suma_bw, saltos, camino = heapq.heappop(cola)

            if nodo_actual == destino:
                bw_promedio_real = -neg_bw_prom if saltos > 0 else 0
                self._imprimir_resumen_ruta(camino, lat_acum, bw_promedio_real, costo_acum)
                return camino

            metrica_actual = (lat_acum, neg_bw_prom, costo_acum)
            if nodo_actual in mejor_metrica_visitado and mejor_metrica_visitado[nodo_actual] <= metrica_actual:
                continue

            mejor_metrica_visitado[nodo_actual] = metrica_actual

            for enlace in self.lista_adyacencia.get(nodo_actual, []):
                if enlace.activo:
                    vecino = enlace.destino if enlace.origen == nodo_actual else enlace.origen

                    nueva_lat = lat_acum + enlace.latencia
                    nuevo_costo = costo_acum + enlace.costo
                    nueva_suma_bw = suma_bw + enlace.ancho_banda
                    nuevos_saltos = saltos + 1
                    nuevo_bw_prom = nueva_suma_bw / nuevos_saltos
                    nuevo_camino = camino + [vecino]

                    heapq.heappush(cola, (nueva_lat, -nuevo_bw_prom, nuevo_costo,
                                          vecino, nueva_suma_bw, nuevos_saltos, nuevo_camino))

        print(f"\n[Resultado] No existe una ruta activa o posible entre {origen} y {destino}.")
        return None 
    

    def _imprimir_resumen_ruta(self, camino, latencia, bw, costo):
        print("\n" + "=" * 15 + " RUTA ÓPTIMA ENCONTRADA " + "=" * 15)
        print(f"Ruta       : {' -> '.join(camino)}")
        print(f"Latencia   : {latencia:.2f} ms")
        print(f"Ancho Banda: {bw:.2f} Mbps (Promedio)")
        print(f"Costo Total: ${costo:,.0f} CLP")     # Formato con separador de miles
        print("=" * 54)

    def es_punto_articulacion(self, router_excluido):
        nodos_activos = [n for n in self.routers if n != router_excluido]
        if not nodos_activos:
            return False

        visitados = set()
        pila = [nodos_activos[0]]

        while pila:
            nodo_actual = pila.pop()
            if nodo_actual not in visitados:
                visitados.add(nodo_actual)
                for enlace in self.lista_adyacencia.get(nodo_actual, []):
                    if enlace.activo:
                        vecino = enlace.destino if enlace.origen == nodo_actual else enlace.origen
                        if vecino != router_excluido and vecino not in visitados:
                            pila.append(vecino)

        return len(visitados) < len(nodos_activos)
