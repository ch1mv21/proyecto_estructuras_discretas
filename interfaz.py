#Evaluacion 03 Estructuras Discretas
#Autores: Jose Herrera - Manuel Soto - Tomas Diaz
#Academico: Eric Lillo
#Fecha:01/07/2026

import tkinter as tk
from tkinter import ttk, filedialog
import threading
import sys
import networkx as nx
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from cargador_excel import CargadorExcel
from grafo_red import GrafoRed

# ─────────────────────────────────────────────
#  PALETA NOCTURNA
# ─────────────────────────────────────────────
BG_BASE     = "#0d1117"
BG_PANEL    = "#161b22"
BG_WIDGET   = "#1f2937"
BG_HOVER    = "#2d3748"
ACCENT      = "#58a6ff"
ACCENT2     = "#3fb950"
ACCENT_WARN = "#f85149"
ACCENT_YEL  = "#e3b341"
ACCENT_ORG  = "#d29922"
FG_PRIMARY  = "#e6edf3"
FG_MUTED    = "#8b949e"
BORDER      = "#30363d"

FONT       = "Helvetica"
F_TITLE    = (FONT, 15, "bold")
F_SUBTITLE = (FONT, 11, "bold")
F_BODY     = (FONT, 10)
F_MONO     = ("Courier", 10)
F_SMALL    = (FONT, 9)
F_BTN      = (FONT, 10, "bold")


# ─────────────────────────────────────────────
#  CAPTURA DE STDOUT → widget Text
# ─────────────────────────────────────────────
class StdoutRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, msg):
        self.text_widget.configure(state="normal")
        if any(k in msg for k in ("[Éxito]", "100%", "correctamente", "ÓPTIMA", "actualizado")):
            tag = "ok"
        elif any(k in msg for k in ("[Error]", "[BLOQUEADO]", "ALERTA", "aislados", "No existe")):
            tag = "err"
        elif any(k in msg for k in ("[Aviso]", "Aviso", "[Visualización]")):
            tag = "warn"
        elif any(k in msg for k in ("===", "---", "RUTA", "LISTA", "MATRIZ", "ANÁLISIS", "CONECTIVIDAD")):
            tag = "header"
        else:
            tag = "normal"
        self.text_widget.insert("end", msg, tag)
        self.text_widget.see("end")
        self.text_widget.configure(state="disabled")

    def flush(self):
        pass


# ─────────────────────────────────────────────
#  DIÁLOGO GENÉRICO DE EDICIÓN DE ENLACE
# ─────────────────────────────────────────────
class DialogoModificarEnlace(tk.Toplevel):
    """
    Ventana emergente que pide el ID del enlace y los nuevos valores
    (se dejan vacíos los campos que no se quieran cambiar).
    """
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.callback = callback
        self.title("Modificar Enlace")
        self.configure(bg=BG_BASE)
        self.resizable(False, False)
        self.grab_set()

        pad = {"padx": 14, "pady": 5}

        tk.Label(self, text="Modificar Enlace", font=F_SUBTITLE,
                 bg=BG_BASE, fg=ACCENT).grid(row=0, column=0, columnspan=2, **pad)

        campos = [
            ("ID del Enlace *", "ent_id"),
            ("Nueva Latencia (ms)", "ent_lat"),
            ("Nuevo Costo (CLP)",   "ent_cost"),
            ("Nuevo Ancho de Banda (Mbps)", "ent_bw"),
        ]
        self.entradas = {}
        for i, (lbl, key) in enumerate(campos, start=1):
            tk.Label(self, text=lbl, font=F_SMALL, bg=BG_BASE, fg=FG_MUTED
                     ).grid(row=i, column=0, sticky="e", **pad)
            e = tk.Entry(self, font=F_BODY, bg=BG_WIDGET, fg=FG_PRIMARY,
                         insertbackground=ACCENT, relief="flat", bd=4, width=18)
            e.grid(row=i, column=1, **pad)
            self.entradas[key] = e

        tk.Label(self, text="* Campo obligatorio. Dejar en blanco lo que no se quiera cambiar.",
                 font=(FONT, 8), bg=BG_BASE, fg=FG_MUTED
                 ).grid(row=len(campos)+1, column=0, columnspan=2, padx=14, pady=(0, 6))

        frame_btns = tk.Frame(self, bg=BG_BASE)
        frame_btns.grid(row=len(campos)+2, column=0, columnspan=2, pady=(4, 12))
        tk.Button(frame_btns, text="Cancelar", font=F_BTN,
                  bg=BG_WIDGET, fg=FG_MUTED, relief="flat", padx=12, pady=6,
                  command=self.destroy).pack(side="left", padx=6)
        tk.Button(frame_btns, text="Guardar cambios", font=F_BTN,
                  bg=ACCENT_ORG, fg=BG_BASE, relief="flat", padx=12, pady=6,
                  command=self._confirmar).pack(side="left", padx=6)

    def _confirmar(self):
        id_e   = self.entradas["ent_id"].get().strip()
        lat    = self.entradas["ent_lat"].get().strip()
        costo  = self.entradas["ent_cost"].get().strip()
        bw     = self.entradas["ent_bw"].get().strip()

        if not id_e:
            tk.messagebox.showwarning("Campo requerido", "El ID del enlace es obligatorio.",
                                      parent=self)
            return

        # Validaciones numéricas
        def to_float_or_none(val, campo):
            if not val:
                return None
            try:
                return float(val)
            except ValueError:
                tk.messagebox.showwarning("Valor inválido",
                    f"'{val}' no es un número válido para {campo}.", parent=self)
                raise

        try:
            lat_f   = to_float_or_none(lat,   "Latencia")
            costo_f = to_float_or_none(costo, "Costo")
            bw_f    = to_float_or_none(bw,    "Ancho de Banda")
        except ValueError:
            return

        self.destroy()
        self.callback(id_e, lat_f, costo_f, bw_f)


# ─────────────────────────────────────────────
#  APLICACIÓN PRINCIPAL
# ─────────────────────────────────────────────
class MonitorRedApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Monitor de Red ISP")
        self.geometry("1080x700")
        self.minsize(900, 580)
        self.configure(bg=BG_BASE)
        self.red = GrafoRed()
        self._build_ui()
        self._redirect_stdout()

    # ── CONSTRUCCIÓN UI ─────────────────────
    def _build_ui(self):
        header = tk.Frame(self, bg=BG_PANEL, height=54)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="◈  Monitor de Red ISP",
            font=F_TITLE, bg=BG_PANEL, fg=ACCENT
        ).pack(side="left", padx=20, pady=12)
        self.lbl_status = tk.Label(header, text="Sin archivo cargado",
            font=F_SMALL, bg=BG_PANEL, fg=FG_MUTED)
        self.lbl_status.pack(side="right", padx=20)

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        body = tk.Frame(self, bg=BG_BASE)
        body.pack(fill="both", expand=True)

        sidebar = tk.Frame(body, bg=BG_PANEL, width=240)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        self._build_sidebar(sidebar)

        tk.Frame(body, bg=BORDER, width=1).pack(side="left", fill="y")

        content = tk.Frame(body, bg=BG_BASE)
        content.pack(side="left", fill="both", expand=True)

        self._apply_styles()

        self.notebook = ttk.Notebook(content, style="Dark.TNotebook")
        self.notebook.pack(fill="both", expand=True)

        self.tab_consola = tk.Frame(self.notebook, bg=BG_BASE)
        self.notebook.add(self.tab_consola, text="")
        self._build_consola(self.tab_consola)

        self.tab_lista = tk.Frame(self.notebook, bg=BG_BASE)
        self.notebook.add(self.tab_lista, text="")
        self._build_tabla_lista(self.tab_lista)

        self.tab_matriz = tk.Frame(self.notebook, bg=BG_BASE)
        self.notebook.add(self.tab_matriz, text="")
        self._build_tabla_matriz(self.tab_matriz)

        self.tab_grafo = tk.Frame(self.notebook, bg=BG_BASE)
        self.notebook.add(self.tab_grafo, text="")
        self._build_grafo_tab(self.tab_grafo)

    def _apply_styles(self):
        style = ttk.Style(self)
        style.theme_use("default")
        style.configure("Dark.TNotebook", background=BG_BASE, borderwidth=0)
        style.configure("Dark.TNotebook.Tab",
            background=BG_WIDGET, foreground=FG_MUTED,
            font=F_SMALL, padding=[12, 5])
        style.map("Dark.TNotebook.Tab",
            background=[("selected", BG_BASE)],
            foreground=[("selected", ACCENT)])
        style.configure("Dark.Treeview",
            background=BG_WIDGET, fieldbackground=BG_WIDGET,
            foreground=FG_PRIMARY, font=F_BODY, rowheight=24, borderwidth=0)
        style.configure("Dark.Treeview.Heading",
            background=BG_PANEL, foreground=ACCENT,
            font=(FONT, 10, "bold"), relief="flat")
        style.map("Dark.Treeview",
            background=[("selected", BG_HOVER)],
            foreground=[("selected", FG_PRIMARY)])

    def _build_sidebar(self, parent):
        # ── SECCIÓN: ACCIONES GENERALES ──
        tk.Label(parent, text="ACCIONES",
            font=F_SMALL, bg=BG_PANEL, fg=FG_MUTED
        ).pack(anchor="w", padx=16, pady=(18, 6))

        self._btn(parent, "📂  Cargar Archivo",     self.accion_cargar, ACCENT)
        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=12, pady=8)
        self._btn(parent, "🔗  Lista Adyacencia",      self.accion_lista)
        self._btn(parent, "⊞  Matriz Adyacencia",     self.accion_matriz)
        self._btn(parent, "🕸️  Ver Grafo Visual",      self.accion_grafo)
        self._btn(parent, "🔍  Analizar Conectividad", self.accion_conectividad)
        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=12, pady=8)

        # ── SECCIÓN: RUTA ÓPTIMA ──
        tk.Label(parent, text="RUTA ÓPTIMA",
            font=F_SMALL, bg=BG_PANEL, fg=FG_MUTED
        ).pack(anchor="w", padx=16, pady=(4, 4))
        self._lbl_entry(parent, "Origen:")
        self.ent_origen = self._entry(parent)
        self._lbl_entry(parent, "Destino:")
        self.ent_destino = self._entry(parent)
        self._btn(parent, "▶  Calcular Ruta", self.accion_ruta, ACCENT2)
        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=12, pady=8)

        # ── SECCIÓN: GESTIÓN DE ENLACES ──
        tk.Label(parent, text="GESTIÓN DE ENLACES",
            font=F_SMALL, bg=BG_PANEL, fg=FG_MUTED
        ).pack(anchor="w", padx=16, pady=(4, 4))

        self._btn(parent, "✏️  Modificar Enlace", self.accion_modificar_enlace, ACCENT_ORG)

        self._lbl_entry(parent, "ID Enlace a Eliminar:")
        self.ent_enlace = self._entry(parent)
        self._btn(parent, "✂️  Eliminar Enlace", self.accion_eliminar_enlace, ACCENT_WARN)
        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=12, pady=8)

        # ── SECCIÓN: ELIMINAR ROUTER ──
        tk.Label(parent, text="ELIMINAR ROUTER",
            font=F_SMALL, bg=BG_PANEL, fg=FG_MUTED
        ).pack(anchor="w", padx=16, pady=(4, 4))
        self._lbl_entry(parent, "Nombre Router:")
        self.ent_router = self._entry(parent)
        self._btn(parent, "🗑  Eliminar Router", self.accion_eliminar, ACCENT_WARN)

        tk.Frame(parent, bg=BG_PANEL).pack(fill="both", expand=True)
        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=12)
        self._btn(parent, "✕  Salir", self.destroy, FG_MUTED)
        tk.Frame(parent, bg=BG_PANEL, height=10).pack()

    def _btn(self, parent, text, cmd, color=None):
        color = color or FG_PRIMARY
        f = tk.Frame(parent, bg=BG_PANEL)
        f.pack(fill="x", padx=12, pady=2)
        btn = tk.Button(f, text=text, command=cmd,
            font=F_BTN, bg=BG_WIDGET, fg=color,
            activebackground=BG_HOVER, activeforeground=color,
            bd=0, padx=10, pady=7, anchor="w",
            cursor="hand2", relief="flat")
        btn.pack(fill="x")
        btn.bind("<Enter>", lambda e: btn.config(bg=BG_HOVER))
        btn.bind("<Leave>", lambda e: btn.config(bg=BG_WIDGET))
        return btn

    def _lbl_entry(self, parent, text):
        tk.Label(parent, text=text, font=F_SMALL,
            bg=BG_PANEL, fg=FG_MUTED
        ).pack(anchor="w", padx=16, pady=(4, 0))

    def _entry(self, parent):
        e = tk.Entry(parent, font=F_BODY,
            bg=BG_WIDGET, fg=FG_PRIMARY,
            insertbackground=ACCENT, relief="flat", bd=0)
        e.pack(fill="x", padx=12, pady=(2, 0), ipady=5)
        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=12)
        return e

    def _build_consola(self, parent):
        tk.Label(parent, text="Salida del Sistema",
            font=F_SUBTITLE, bg=BG_BASE, fg=FG_PRIMARY
        ).pack(anchor="w", padx=16, pady=(12, 4))

        frame_txt = tk.Frame(parent, bg=BG_WIDGET)
        frame_txt.pack(fill="both", expand=True, padx=12, pady=(0, 4))

        self.consola = tk.Text(frame_txt, font=F_MONO,
            bg=BG_WIDGET, fg=FG_PRIMARY,
            insertbackground=ACCENT, relief="flat", bd=8,
            state="disabled", wrap="word", selectbackground=BG_HOVER)
        sb = tk.Scrollbar(frame_txt, command=self.consola.yview, bg=BG_WIDGET)
        self.consola.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.consola.pack(fill="both", expand=True)

        self.consola.tag_config("ok",     foreground=ACCENT2)
        self.consola.tag_config("err",    foreground=ACCENT_WARN)
        self.consola.tag_config("warn",   foreground=ACCENT_YEL)
        self.consola.tag_config("header", foreground=ACCENT, font=(FONT, 10, "bold"))
        self.consola.tag_config("normal", foreground=FG_PRIMARY)

        footer = tk.Frame(parent, bg=BG_BASE)
        footer.pack(fill="x", padx=16, pady=(4, 8))
        tk.Label(footer,
            text="Jose Herrera  ·  Manuel Soto  ·  Tomas Diaz",
            font=(FONT, 8), bg=BG_BASE, fg=FG_MUTED
        ).pack(side="right")

    def _build_tabla_lista(self, parent):
        tk.Label(parent, text="Lista de Adyacencia",
            font=F_SUBTITLE, bg=BG_BASE, fg=FG_PRIMARY
        ).pack(anchor="w", padx=16, pady=(12, 4))

        frame = tk.Frame(parent, bg=BG_BASE)
        frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        cols = ("Router", "Conectado con")
        self.tree_lista = ttk.Treeview(frame, columns=cols,
            show="headings", style="Dark.Treeview")
        for c in cols:
            self.tree_lista.heading(c, text=c)
        self.tree_lista.column("Router", width=120, anchor="center")
        self.tree_lista.column("Conectado con", anchor="w")

        sb = tk.Scrollbar(frame, command=self.tree_lista.yview, bg=BG_WIDGET)
        self.tree_lista.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.tree_lista.pack(fill="both", expand=True)

    def _build_tabla_matriz(self, parent):
        tk.Label(parent, text="Matriz de Adyacencia",
            font=F_SUBTITLE, bg=BG_BASE, fg=FG_PRIMARY
        ).pack(anchor="w", padx=16, pady=(12, 4))

        outer = tk.Frame(parent, bg=BG_BASE)
        outer.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        hbar = tk.Scrollbar(outer, orient="horizontal", bg=BG_WIDGET)
        vbar = tk.Scrollbar(outer, orient="vertical",   bg=BG_WIDGET)
        self.canvas_matriz = tk.Canvas(outer, bg=BG_WIDGET,
            xscrollcommand=hbar.set, yscrollcommand=vbar.set,
            highlightthickness=0)
        hbar.config(command=self.canvas_matriz.xview)
        vbar.config(command=self.canvas_matriz.yview)
        hbar.pack(side="bottom", fill="x")
        vbar.pack(side="right",  fill="y")
        self.canvas_matriz.pack(fill="both", expand=True)

        self.frame_matriz = tk.Frame(self.canvas_matriz, bg=BG_WIDGET)
        self.canvas_matriz.create_window((0, 0), window=self.frame_matriz, anchor="nw")
        self.frame_matriz.bind("<Configure>",
            lambda e: self.canvas_matriz.configure(
                scrollregion=self.canvas_matriz.bbox("all")))

    def _build_grafo_tab(self, parent):
        tk.Label(parent, text="Visualización del Grafo",
            font=F_SUBTITLE, bg=BG_BASE, fg=FG_PRIMARY
        ).pack(anchor="w", padx=16, pady=(12, 4))

        self.frame_grafo = tk.Frame(parent, bg=BG_BASE)
        self.frame_grafo.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        tk.Label(self.frame_grafo,
            text="Carga un archivo y usa\n'Ver Grafo Visual' para renderizar el mapa.",
            font=F_BODY, bg=BG_BASE, fg=FG_MUTED
        ).pack(expand=True)

    # ── STDOUT ──────────────────────────────
    def _redirect_stdout(self):
        sys.stdout = StdoutRedirector(self.consola)

    def _limpiar_consola(self):
        self.consola.configure(state="normal")
        self.consola.delete("1.0", "end")
        self.consola.configure(state="disabled")

    def _log(self, msg, tag="normal"):
        self.consola.configure(state="normal")
        self.consola.insert("end", msg + "\n", tag)
        self.consola.see("end")
        self.consola.configure(state="disabled")

    def _actualizar_vistas(self):
        """Recarga lista, matriz y (si ya estaba dibujado) el grafo visual."""
        self._poblar_lista()
        self._poblar_matriz()
        # Si el frame del grafo ya tiene un canvas (matplotlib), lo re-dibujamos
        for w in self.frame_grafo.winfo_children():
            if isinstance(w, tk.Widget):
                self._dibujar_grafo_embebido()
                break

    # ── ACCIONES ────────────────────────────
    def accion_cargar(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar archivo de topología",
            filetypes=[("Excel / CSV", "*.xlsx *.xls *.csv"), ("Todos", "*.*")])
        if not ruta:
            return
        self.notebook.select(self.tab_consola)
        self._log(f"\n📂  Cargando: {ruta}", "warn")

        def _tarea():
            enlaces = CargadorExcel.cargar_red(ruta)
            if enlaces:
                self.red = GrafoRed()
                for enlace in enlaces:
                    self.red.agregar_enlace(enlace)
                n_r = len(self.red.routers)
                self.after(0, lambda: self.lbl_status.config(
                    text=f"{n_r} routers · {len(enlaces)} enlaces", fg=ACCENT2))
                self.after(0, self._poblar_lista)
                self.after(0, self._poblar_matriz)

        threading.Thread(target=_tarea, daemon=True).start()

    def accion_lista(self):
        if not self.red.routers:
            self._log("\n[Aviso] Cargue un archivo primero.", "warn"); return
        self._poblar_lista()
        self.notebook.select(self.tab_lista)

    def accion_matriz(self):
        if not self.red.routers:
            self._log("\n[Aviso] Cargue un archivo primero.", "warn"); return
        self._poblar_matriz()
        self.notebook.select(self.tab_matriz)

    def accion_grafo(self):
        if not self.red.routers:
            self._log("\n[Aviso] Cargue un archivo primero.", "warn"); return
        self.notebook.select(self.tab_grafo)
        self._dibujar_grafo_embebido()

    def accion_conectividad(self):
        if not self.red.routers:
            self._log("\n[Aviso] Cargue un archivo primero.", "warn"); return
        self.notebook.select(self.tab_consola)
        self._log("\n" + "─"*46, "header")
        self.red.analizar_conectividad()

    def accion_ruta(self):
        if not self.red.routers:
            self._log("\n[Aviso] Cargue un archivo primero.", "warn"); return
        origen  = self.ent_origen.get().strip().upper()
        destino = self.ent_destino.get().strip().upper()
        if not origen or not destino:
            self._log("\n[Aviso] Ingresa Origen y Destino.", "warn"); return
        
        self.notebook.select(self.tab_consola)
        self._log(f"\n▶  Calculando ruta: {origen} → {destino}", "warn")
        camino_optimo = self.red.analizar_ruta_optima(origen, destino)
         
        if camino_optimo:
            self.notebook.select(self.tab_grafo)
            self._dibujar_grafo_embebido(ruta_resaltada=camino_optimo)



    def accion_modificar_enlace(self):
        if not self.red.routers:
            self._log("\n[Aviso] Cargue un archivo primero.", "warn"); return
        self.notebook.select(self.tab_consola)

        def _aplicar(id_e, lat, costo, bw):
            exito = self.red.modificar_enlace(id_e, lat, costo, bw)
            if exito:
                self._actualizar_vistas()

        DialogoModificarEnlace(self, _aplicar)

    def accion_eliminar_enlace(self):
        if not self.red.routers:
            self._log("\n[Aviso] Cargue un archivo primero.", "warn"); return
        id_e = self.ent_enlace.get().strip()
        if not id_e:
            self._log("\n[Aviso] Ingresa el ID del enlace a eliminar.", "warn"); return
        self.notebook.select(self.tab_consola)
        self._log(f"\n✂️  Intentando eliminar enlace ID: {id_e}", "warn")
        exito = self.red.eliminar_enlace(id_e)
        if exito:
            self.ent_enlace.delete(0, "end")
            self._actualizar_vistas()

    def accion_eliminar(self):
        if not self.red.routers:
            self._log("\n[Aviso] Cargue un archivo primero.", "warn"); return
        nombre = self.ent_router.get().strip().upper()
        if not nombre:
            self._log("\n[Aviso] Ingresa el nombre del router.", "warn"); return
        self.notebook.select(self.tab_consola)
        self._log(f"\n🗑  Intentando eliminar: {nombre}", "warn")
        exito = self.red.eliminar_router(nombre)
        if exito:
            self.ent_router.delete(0, "end")
            self._actualizar_vistas()

    # ── POBLAR VISTAS ───────────────────────
    def _poblar_lista(self):
        for row in self.tree_lista.get_children():
            self.tree_lista.delete(row)
        for nodo, enlaces in sorted(self.red.lista_adyacencia.items()):
            vecinos = []
            for e in enlaces:
                if e.activo:
                    v = e.destino if e.origen == nodo else e.origen
                    vecinos.append(f"{v}(id:{e.id})")
            self.tree_lista.insert("", "end",
                values=(f"Router {nodo}", ", ".join(vecinos) if vecinos else "—"))

    def _poblar_matriz(self):
        for w in self.frame_matriz.winfo_children():
            w.destroy()
        nodos = sorted(self.red.routers.keys())
        n = len(nodos)
        if n == 0:
            return
        mapeo = {nd: i for i, nd in enumerate(nodos)}
        mat = [[0]*n for _ in range(n)]
        for nodo, enlaces in self.red.lista_adyacencia.items():
            for e in enlaces:
                if e.activo:
                    u, v = mapeo[e.origen], mapeo[e.destino]
                    mat[u][v] = mat[v][u] = 1
        pad = 2
        tk.Label(self.frame_matriz, text="", bg=BG_WIDGET, width=5
            ).grid(row=0, column=0)
        for j, nd in enumerate(nodos):
            tk.Label(self.frame_matriz, text=nd,
                font=(FONT, 8, "bold"), bg=BG_PANEL, fg=ACCENT,
                width=4, relief="flat"
            ).grid(row=0, column=j+1, padx=pad, pady=pad)
        for i, nd_row in enumerate(nodos):
            tk.Label(self.frame_matriz, text=nd_row,
                font=(FONT, 8, "bold"), bg=BG_PANEL, fg=ACCENT,
                width=5, anchor="e", relief="flat"
            ).grid(row=i+1, column=0, padx=pad, pady=pad)
            for j in range(n):
                val = mat[i][j]
                tk.Label(self.frame_matriz, text=str(val),
                    font=(FONT, 9),
                    bg=ACCENT2 if val else BG_WIDGET,
                    fg=BG_BASE if val else FG_MUTED,
                    width=3, relief="flat"
                ).grid(row=i+1, column=j+1, padx=pad, pady=pad)
        self.canvas_matriz.configure(
            scrollregion=self.canvas_matriz.bbox("all"))

    def _dibujar_grafo_embebido(self, ruta_resaltada=None):
        for w in self.frame_grafo.winfo_children():
            w.destroy()
            
        G = nx.Graph()
        for nodo in self.red.routers:
            G.add_node(nodo)
            
        for nodo, enlaces in self.red.lista_adyacencia.items():
            for e in enlaces:
                if e.activo:
                    G.add_edge(e.origen, e.destino, weight=e.latencia)
                    
        fig, ax = plt.subplots(figsize=(10, 6))
        fig.patch.set_facecolor(BG_BASE)
        ax.set_facecolor(BG_BASE)
        
        pos = nx.spring_layout(G, k=0.45, iterations=60, seed=42)
        
        # 1. Dibujamos los nodos
        nx.draw_networkx_nodes(G, pos, ax=ax, node_color=ACCENT, node_size=350, alpha=0.9)
        nx.draw_networkx_labels(G, pos, ax=ax, font_size=7, font_color=BG_BASE, font_weight="bold")
        
        # 2. Dibujamos todas las aristas base en gris
        nx.draw_networkx_edges(G, pos, ax=ax, edge_color=BORDER, width=1.2, alpha=0.8)
        
        # 3. Si hay una ruta resaltada, dibujamos esas aristas de color verde encima
        if ruta_resaltada and len(ruta_resaltada) > 1:
            aristas_ruta = [(ruta_resaltada[i], ruta_resaltada[i+1]) for i in range(len(ruta_resaltada)-1)]
            nx.draw_networkx_edges(G, pos, ax=ax, edgelist=aristas_ruta, edge_color=ACCENT2, width=3.5, alpha=1.0)
            ax.set_title(f"Ruta Óptima: {' → '.join(ruta_resaltada)}", color=ACCENT2, fontsize=12, fontfamily=FONT, pad=10)
        else:
            ax.set_title("Mapa de Infraestructura — Red ISP", color=FG_PRIMARY, fontsize=12, fontfamily=FONT, pad=10)
            
        ax.axis("off")
        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=self.frame_grafo)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        plt.close(fig)
        self._log("\n[Visualización] Grafo renderizado en la pestaña 'Grafo Visual'.", "ok")
