import tkinter as tk
from tkinter import ttk, messagebox
from collections import defaultdict
from statistics import mean

from controllers.productivity_controller import ProductivityController
from controllers.agent_controller import AgentController
from domain.exceptions.custom_exceptions import CallCenterError
from views.widgets.kpi_card import KPICard
from views.widgets.forecast_chart import ForecastChart
from analytics.kpis.productivity_kpis import ProductivityKPI
from analytics.kpis.productivity_kpis import ProductivityKPI


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
        self.all_records = []
        self._kpi_row()
        self._search_row()
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
        self.kpi_util = KPICard(row, 'Avg Utilization',
                                 '(busy + available) / login_duration')
        self.kpi_p10 = KPICard(row, 'P10 Occupancy',
                                'percentil 10 - bajos')
        self.kpi_p90 = KPICard(row, 'P90 Occupancy',
                                'percentil 90 - altos')
        self.kpi_prod = KPICard(row, 'Avg Productivity',
                                 'score promedio')
        self.kpi_total = KPICard(row, 'Records',
                                  'total registrados')
        for w in (self.kpi_occ, self.kpi_util, self.kpi_p10,
                  self.kpi_p90, self.kpi_prod, self.kpi_total):
            w.pack(side='left', expand=True, fill='x', padx=4)
    def _search_row(self):
        search_box = ttk.LabelFrame(self.frame, text='Search & Filter', padding=8)
        search_box.pack(fill='x', padx=8, pady=4)
        
        ttk.Label(search_box, text='Agent ID:').grid(row=0, column=0, padx=4, sticky='w')
        self.search_agent_id = ttk.Entry(search_box, width=16)
        self.search_agent_id.grid(row=0, column=1, padx=4)
        
        ttk.Label(search_box, text='Date (YYYY-MM-DD):').grid(row=0, column=2, padx=4, sticky='w')
        self.search_date = ttk.Entry(search_box, width=16)
        self.search_date.grid(row=0, column=3, padx=4)
        
        ttk.Button(search_box, text='Search', command=self._apply_filters,
                   style='Accent.TButton').grid(row=0, column=4, padx=8)
        ttk.Button(search_box, text='Clear Filters',
                   command=self._clear_filters).grid(row=0, column=5, padx=4)

    def _apply_filters(self):
        agent_id_filter = self.search_agent_id.get().strip().lower()
        date_filter = self.search_date.get().strip().lower()
        
        for r in self.tree.get_children():
            self.tree.delete(r)
        
        filtered_records = []
        for p in self.all_records:
            agent_id = str(p.get('agent_id', '')).lower()
            date = str(p.get('date', '')).lower()
            
            match_agent = (not agent_id_filter or agent_id_filter == agent_id)
            match_date = (not date_filter or date_filter == date)
            
            if match_agent and match_date:
                filtered_records.append(p)
                row = self._format_record_for_table(p)
                self.tree.insert('', 'end',
                    values=[row.get(f, '') for f in self.TABLE_COLUMNS])
        
        # Actualizar KPIs para los registros filtrados
        if filtered_records:
            kpi = ProductivityKPI(filtered_records)
            self.kpi_occ.set_value(f"{kpi.avg_occupancy():.0%}")
            self.kpi_util.set_value(f"{kpi.avg_utilization():.0%}")
            dist = kpi.occupancy_distribution()
            self.kpi_p10.set_value(f"{dist.get('p10', 0):.0%}")
            self.kpi_p90.set_value(f"{dist.get('p90', 0):.0%}")
            self.kpi_prod.set_value(f"{kpi.avg_productivity_score():.1f}")
        else:
            self.kpi_occ.set_value("0%")
            self.kpi_util.set_value("0%")
            self.kpi_p10.set_value("0%")
            self.kpi_p90.set_value("0%")
            self.kpi_prod.set_value("0.0")
        
        self.kpi_total.set_value(str(len(filtered_records)))
        self.status.set(f'Filtered: {len(filtered_records)} records')

    def _clear_filters(self):
        self.search_agent_id.delete(0, 'end')
        self.search_date.delete(0, 'end')
        # Restore all KPIs
        kpis = self.ctrl.kpis()
        self.kpi_occ.set_value(f"{kpis.get('avg_occupancy', 0):.0%}")
        self.kpi_util.set_value(f"{kpis.get('avg_utilization', 0):.0%}")
        dist = kpis.get('distribution', {})
        self.kpi_p10.set_value(f"{dist.get('p10', 0):.0%}")
        self.kpi_p90.set_value(f"{dist.get('p90', 0):.0%}")
        self.kpi_prod.set_value(f"{kpis.get('avg_productivity_score', 0):.1f}")
        self.kpi_total.set_value(str(len(self.all_records)))
        self.refresh()
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
            ttk.Button(btns, text=txt, command=cmd,
                       style='Accent.TButton').pack(side='left', padx=4)

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

    def _format_record_for_table(self, record: dict) -> dict:
        enriched = dict(record)
        enriched['occupancy'] = round(ProductivityKPI([record])._occupancy(record), 3)
        enriched['utilization'] = round(ProductivityKPI([record])._utilization(record), 3)
        enriched['productivity_score'] = round(ProductivityKPI([record])._productivity_score(record), 1)
        return enriched

    # ---------- Sección de Forecast ----------
    def _forecast_section(self):
        fc_box = ttk.LabelFrame(self.frame,
                                 text='Occupancy Forecast by Team Manager',
                                 padding=8)
        fc_box.pack(fill='both', expand=True, padx=8, pady=4)
        fc_box.columnconfigure(0, weight=1)
        fc_box.rowconfigure(1, weight=1)

        controls = ttk.Frame(fc_box)
        controls.grid(row=0, column=0, sticky='ew', pady=(0, 8))
        controls.columnconfigure(1, weight=1)

        ttk.Label(controls, text='Team Manager:').grid(row=0, column=0,
                                                       padx=(0, 8), pady=2,
                                                       sticky='w')
        self.tl_var = tk.StringVar()
        self.tl_combo = ttk.Combobox(controls, textvariable=self.tl_var,
                                       width=20, state='readonly')
        self.tl_combo.grid(row=0, column=1, padx=(0, 16), pady=2,
                            sticky='ew')

        ttk.Label(controls, text='Horizon (days):').grid(row=0, column=2,
                                                         padx=(0, 8), pady=2,
                                                         sticky='w')
        self.horizon_var = tk.StringVar(value='7')
        ttk.Spinbox(controls, from_=3, to=30, width=6,
                     textvariable=self.horizon_var
                     ).grid(row=0, column=3, padx=(0, 12), pady=2)

        ttk.Button(controls, text='Run Forecast',
                    command=self._run_forecast
                    ).grid(row=0, column=4, padx=4, pady=2)

        self.chart = ForecastChart(fc_box)
        self.chart.grid(row=1, column=0, sticky='nsew')

    # ---------- Refresh ----------
    def refresh(self):
        # Cargar todos los registros
        self.all_records = self.ctrl.repo.find_all()
        
        # Tabla
        for r in self.tree.get_children():
            self.tree.delete(r)
        
        # Mostrar registros (con filtros si existen)
        agent_id_filter = self.search_agent_id.get().strip().lower()
        date_filter = self.search_date.get().strip().lower()
        
        for p in self.all_records:
            agent_id = str(p.get('agent_id', '')).lower()
            date = str(p.get('date', '')).lower()
            
            match_agent = (not agent_id_filter or agent_id_filter == agent_id)
            match_date = (not date_filter or date_filter == date)
            
            if match_agent and match_date:
                row = self._format_record_for_table(p)
                self.tree.insert('', 'end',
                    values=[row.get(f, '') for f in self.TABLE_COLUMNS])

        # KPI cards
        kpis = self.ctrl.kpis()
        self.kpi_occ.set_value(f"{kpis.get('avg_occupancy', 0):.0%}")
        self.kpi_util.set_value(f"{kpis.get('avg_utilization', 0):.0%}")
        dist = kpis.get('distribution', {})
        self.kpi_p10.set_value(f"{dist.get('p10', 0):.0%}")
        self.kpi_p90.set_value(f"{dist.get('p90', 0):.0%}")
        self.kpi_prod.set_value(f"{kpis.get('avg_productivity_score', 0):.1f}")
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
                if agent_to_tl.get(r.get('agent_id')) != tl:
                    continue
                occ = r.get('occupancy')
                if occ is None:
                    login = r.get('login_duration', 0) or 0
                    busy = r.get('busy_duration', 0) or 0
                    occ = busy / login if login else 0.0
                daily[r.get('date', '')].append(occ)
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