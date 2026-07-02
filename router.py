#Evaluacion 03 Estructuras Discretas
#Autores: Jose Herrera - Manuel Soto - Tomas Diaz
#Academico: Eric Lillo
#Fecha:01/07/2026

class Router:
    def __init__(self, nombre):
        self.nombre = nombre

    def __str__(self):
        return f"Router({self.nombre})"