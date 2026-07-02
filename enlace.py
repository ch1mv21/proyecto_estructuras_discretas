#Evaluacion 03 Estructuras Discretas
#Autores: Jose Herrera - Manuel Soto - Tomas Diaz
#Academico: Eric Lillo
#Fecha:01/07/2026

class Enlace:
    def __init__(self, id_enlace, origen, destino, latencia, costo, ancho_banda):
        self.id = id_enlace
        self.origen = origen
        self.destino = destino
        self.latencia = float(latencia)
        self.costo = float(costo)          # CORREGIDO: antes usaba float(latencia) por error
        self.ancho_banda = float(ancho_banda)
        self.activo = True

    def __str__(self):
        estado = "Activo" if self.activo else "Inactivo"
        return (f"[{self.id}] {self.origen} <-> {self.destino} "
                f"(Lat: {self.latencia}ms, BW: {self.ancho_banda}Mbps, "
                f"Costo: ${self.costo:,.0f} CLP) - {estado}")
