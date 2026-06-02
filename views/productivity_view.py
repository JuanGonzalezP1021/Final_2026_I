import tkinter as tk
from tkinter import ttk, messagebox
from collections import defaultdict
from statistics import mean

from controllers.productivity_controller import ProductivityController
from controllers.agent_controller import AgentController
from domain.exceptions.custom_exceptions import CallCenterError
from views.widgets.kpi_card import KPICard
from views.widgets.forecast_chart import ForecastChart


class ProductivityView:
    # Campos del formulario (todos los duration + ids)
    FORM_FIELDS = (
        'agent_id', 'date',
        'aux_duration', 'break_1', 'break_2', 'break_3',
        'email_duration', 'lunch_duration', 'meeting_duration',
        'tech_issue_duration', 'personal_duration', 'task_duration',
        'training_duration', 'available_duration', 'busy_duration',
        'login_duration',
    )

    # Columnas mostradas en la tabla (incluye KPIs calculados)
    TABLE_COLUMNS = (
        'record_id', 'agent_id', 'date',
        'login_duration', 'busy_duration', 'available_duration',
        'aux_duration', 'occupancy', 'utilization', 'productivity_score',
    )

    def __init__(self, parent, status_var):
        self.ctrl = ProductivityController()
        self.agent_ctrl = AgentController()
        self.status = status_var
        self.frame = ttk.Frame(parent)
        self._kpi_row()
        self._form()
        self._table()
        self._forecast_section()
        self.refresh()

    # ---------- KPI cards ----------
    def _kpi_row(self):
        row = ttk.Frame(self.frame)
        row.pack(fill='x', padx=8, pady=6)
        self.kpi_occ = KPICard(row, 'Avg Occupancy',
                                'busy / login_duration')
        self.kpi_p10 = KPICard(row, 'P10 Occupancy',
                                'percentil 10 - bajos')
        self.kpi_p90 = KPICard(row, 'P90 Occupancy',
                                'percentil 90 - altos')
        self.kpi_total = KPICard(row, 'Records',
                                  'total registrados')
        for w in (self.kpi_occ, self.kpi_p10, self.kpi_p90, self.kpi_total):
            w.pack(side='left', expand=True, fill='x', padx=4)

    # ---------- Formulario CRUD ----------
    def _form(self):
        box = ttk.LabelFrame(self.frame, text='Productivity Record',
                              padding=8)
        box.pack(fill='x', padx=8, pady=4)
        self.entries = {}

        # Organizar los 16 campos en 2 filas de 8 columnas
        per_row = 8
        for i, f in enumerate(self.FORM_FIELDS):
            r = (i // per_row) * 2
            c = i % per_row
            ttk.Label(box, text=f.replace('_', ' ').title(),
                      font=('Segoe UI', 8)
                      ).grid(row=r, column=c, padx=3, pady=1, sticky='w')
            e = ttk.Entry(box, width=10)
            e.grid(row=r + 1, column=c, padx=3, pady=2)
            self.entries[f] = e

        btns = ttk.Frame(box)
        btns.grid(row=4, column=0, columnspan=per_row, pady=8)
        for txt, cmd in [('Create', self._create),
                         ('Update', self._update),
                         ('Delete', self._delete),
                         ('Clear', self._clear)]:
            ttk.Button(btns, text=txt, command=cmd
                       ).pack(side='left', padx=4)

    # ---------- Tabla ----------
    def _table(self):
        frame = ttk.Frame(self.frame)
        frame.pack(fill='both', expand=True, padx=8, pady=4)

        self.tree = ttk.Treeview(frame, columns=self.TABLE_COLUMNS,
                                  show='headings', height=8)
        for c in self.TABLE_COLUMNS:
            self.tree.heading(c, text=c.replace('_', ' ').title())
            width = 110 if c in ('record_id', 'agent_id', 'date') else 90
            self.tree.column(c, width=width, anchor='center')

        scroll = ttk.Scrollbar(frame, orient='vertical',
                                command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side='left', fill='both', expand=True)
        scroll.pack(side='right', fill='y')
        self.tree.bind('<<TreeviewSelect>>', self._on_select)

    # ---------- Sección de Forecast ----------
    def _forecast_section(self):
        fc_box = ttk.LabelFrame(self.frame,
                                 text='Occupancy Forecast by Team Manager',
                                 padding=6)
        fc_box.pack(fill='both', expand=False, padx=8, pady=4)

        controls = ttk.Frame(fc_box)
        controls.pack(fill='x', pady=2)
        ttk.Label(controls, text='Team Manager:').pack(side='left', padx=4)
        self.tl_var = tk.StringVar()
        self.tl_combo = ttk.Combobox(controls, textvariable=self.tl_var,
                                       width=12, state='readonly')
        self.tl_combo.pack(side='left', padx=4)

        ttk.Label(controls, text='Horizon (days):').pack(side='left', padx=4)
        self.horizon_var = tk.StringVar(value='7')
        ttk.Spinbox(controls, from_=3, to=30, width=5,
                     textvariable=self.horizon_var
                     ).pack(side='left', padx=4)

        ttk.Button(controls, text='Run Forecast',
                    command=self._run_forecast
                    ).pack(side='left', padx=8)

        self.chart = ForecastChart(fc_box)
        self.chart.pack(fill='both', expand=True)

    # ---------- Refresh ----------
    def refresh(self):
        # Tabla
        for r in self.tree.get_children():
            self.tree.delete(r)
        for p in self.ctrl.repo.find_all():
            self.tree.insert('', 'end',
                values=[p.get(f, '') for f in self.TABLE_COLUMNS])

        # KPI cards
        kpis = self.ctrl.kpis()
        self.kpi_occ.set_value(f"{kpis.get('avg_occupancy', 0):.0%}")
        dist = kpis.get('distribution', {})
        self.kpi_p10.set_value(f"{dist.get('p10', 0):.0%}")
        self.kpi_p90.set_value(f"{dist.get('p90', 0):.0%}")
        self.kpi_total.set_value(str(len(self.ctrl.repo.find_all())))

        # Lista de TLs para el combobox
        tls = sorted({a['team_manager']
                       for a in self.agent_ctrl.repo.find_all()})
        self.tl_combo['values'] = tls
        if tls and not self.tl_var.get():
            self.tl_var.set(tls[0])

    # ---------- CRUD handlers ----------
    def _read_form(self):
        """Lee el formulario y convierte los duration a int."""
        data = {}
        for k, e in self.entries.items():
            val = e.get().strip()
            if k in ('agent_id', 'date'):
                data[k] = val
            else:
                data[k] = int(val) if val else 0
        return data

    def _create(self):
        try:
            self.ctrl.create(self._read_form())
            self.status.set('Productivity record created')
            self.refresh()
            self._clear()
        except CallCenterError as ex:
            messagebox.showerror(ex.code, ex.message)
            self.status.set(f'Error: {ex.code}')
        except ValueError as ex:
            messagebox.showerror('Validation',
                                  f'Numero invalido: {ex}')

    def _update(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning('Update', 'Selecciona una fila primero')
            return
        record_id = self.tree.item(sel[0])['values'][0]
        try:
            self.ctrl.update(record_id, self._read_form())
            self.status.set('Record updated')
            self.refresh()
        except CallCenterError as ex:
            messagebox.showerror(ex.code, ex.message)

    def _delete(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning('Delete', 'Selecciona una fila primero')
            return
        record_id = self.tree.item(sel[0])['values'][0]
        if not messagebox.askyesno('Confirmar',
                f'Eliminar registro {record_id}?'):
            return
        try:
            self.ctrl.delete(record_id)
            self.status.set('Record deleted')
            self.refresh()
            self._clear()
        except CallCenterError as ex:
            messagebox.showerror(ex.code, ex.message)

    def _on_select(self, _):
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0])['values']
        col_map = dict(zip(self.TABLE_COLUMNS, vals))
        for f in self.FORM_FIELDS:
            self.entries[f].delete(0, 'end')
            if f in col_map:
                self.entries[f].insert(0, str(col_map[f]))

    def _clear(self):
        for e in self.entries.values():
            e.delete(0, 'end')

    # ---------- Forecast handler ----------
    def _run_forecast(self):
        tl = self.tl_var.get()
        if not tl:
            messagebox.showwarning('Forecast',
                                    'Selecciona un Team Manager')
            return
        try:
            horizon = int(self.horizon_var.get())
        except ValueError:
            horizon = 7

        try:
            result = self.ctrl.forecast_occupancy_for_tl(tl,
                                                          horizon=horizon)
            if 'error' in result:
                messagebox.showinfo('Forecast', result['error'])
                return

            # Reconstruir la serie historica para la grafica
            agent_to_tl = {a['agent_id']: a['team_manager']
                            for a in self.agent_ctrl.repo.find_all()}
            daily = defaultdict(list)
            for r in self.ctrl.repo.find_all():
                if agent_to_tl.get(r['agent_id']) == tl:
                    daily[r['date']].append(r['occupancy'])
            history = [mean(daily[d]) for d in sorted(daily)]

            preds = result['predictions']
            mae = result['mae']
            band = 1.96 * mae
            low = [p - band for p in preds]
            high = [p + band for p in preds]

            self.chart.render(history, preds, low, high,
                f"Occupancy forecast for {tl} ({result['method']})")
            self.status.set(
                f"Forecast: {result['method']}, MAE={mae:.3f}")
        except CallCenterError as ex:
            messagebox.showerror(ex.code, ex.message)