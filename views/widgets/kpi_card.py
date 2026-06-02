import tkinter as tk
from tkinter import ttk

class KPICard(ttk.Frame):
    def __init__(self, parent, title, formula, **kw):
        super().__init__(parent, padding=(14, 12), style='Card.TFrame', **kw)

        # Título del KPI
        ttk.Label(
            self, text=title,
            style='CardTitle.TLabel'
        ).pack(anchor='w')

        # Valor dinámico
        self.value_var = tk.StringVar(value='--')
        ttk.Label(
            self, textvariable=self.value_var,
            style='CardValue.TLabel'
        ).pack(anchor='w', pady=(4, 0))

        # Nota de fórmula/descripción
        ttk.Label(
            self, text=formula,
            style='CardCaption.TLabel'
        ).pack(anchor='w', pady=(6, 0))

    def set_value(self, value):
        """Actualiza el valor mostrado en el KPI."""
        self.value_var.set(value)