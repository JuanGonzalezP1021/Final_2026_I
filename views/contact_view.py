import tkinter as tk
from tkinter import ttk, messagebox
from collections import defaultdict

from controllers.contact_controller import ContactController
from controllers.agent_controller import AgentController
from domain.exceptions.custom_exceptions import CallCenterError
from views.widgets.kpi_card import KPICard
from views.widgets.forecast_chart import ForecastChart
from analytics.kpis.contact_kpis import ContactKPICalculator


class ContactView:
    # Campos del formulario
    FORM_FIELDS = (
        'agent_id', 'date', 'lob', 'channel',
        'acw', 'inbound_tx', 'outbound_tx',
        'handle_time', 'hold_time',
        'outbound_handle_time', 'missed_contacts',
    )

    # Columnas mostradas en la tabla
    TABLE_COLUMNS = (
        'contact_id', 'agent_id', 'date', 'lob', 'channel',
        'inbound_tx', 'outbound_tx', 'handle_time',
        'missed_contacts', 'aht',
    )

    VALID_CHANNELS = ('Phone', 'Chat', 'Email')

    # Campos numericos (necesitan conversion a int)
    NUMERIC_FIELDS = ('acw', 'inbound_tx', 'outbound_tx',
                      'handle_time', 'hold_time',
                      'outbound_handle_time', 'missed_contacts')

    def __init__(self, parent, status_var):
        self.ctrl = ContactController()
        self.agent_ctrl = AgentController()
        self.status = status_var
        self.frame = ttk.Frame(parent)
        self.all_contacts = []
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
        self.kpi_aht_overall = KPICard(row, 'AHT Overall',
                                        '(handle + acw) / tx')
        self.kpi_aht_phone = KPICard(row, 'AHT Phone',
                                      'segundos por llamada')
        self.kpi_aht_chat = KPICard(row, 'AHT Chat',
                                     'segundos por chat')
        self.kpi_total = KPICard(row, 'Contacts',
                                  'total registrados')
        for w in (self.kpi_aht_overall, self.kpi_aht_phone,
                  self.kpi_aht_chat, self.kpi_total):
            w.pack(side='left', expand=True, fill='x', padx=4)

    def _search_row(self):
        search_box = ttk.LabelFrame(self.frame, text='Search & Filter', padding=8)
        search_box.pack(fill='x', padx=8, pady=4)
        
        ttk.Label(search_box, text='Agent ID:').grid(row=0, column=0, padx=4, sticky='w')
        self.search_agent_id = ttk.Entry(search_box, width=16)
        self.search_agent_id.grid(row=0, column=1, padx=4)
        
        ttk.Label(search_box, text='LOB:').grid(row=0, column=2, padx=4, sticky='w')
        self.search_lob = ttk.Entry(search_box, width=16)
        self.search_lob.grid(row=0, column=3, padx=4)
        
        ttk.Label(search_box, text='Channel:').grid(row=0, column=4, padx=4, sticky='w')
        self.search_channel = ttk.Entry(search_box, width=16)
        self.search_channel.grid(row=0, column=5, padx=4)
        
        ttk.Button(search_box, text='Search', command=self._apply_filters,
                   style='Accent.TButton').grid(row=0, column=6, padx=8)
        ttk.Button(search_box, text='Clear Filters',
                   command=self._clear_filters).grid(row=0, column=7, padx=4)

    def _apply_filters(self):
        agent_id_filter = self.search_agent_id.get().strip().lower()
        lob_filter = self.search_lob.get().strip().lower()
        channel_filter = self.search_channel.get().strip().lower()
        
        for r in self.tree.get_children():
            self.tree.delete(r)
        
        filtered_records = []
        for c in self.all_contacts:
            agent_id = str(c.get('agent_id', '')).lower()
            lob = str(c.get('lob', '')).lower()
            channel = str(c.get('channel', '')).lower()
            
            match_agent = (not agent_id_filter or agent_id_filter == agent_id)
            match_lob = (not lob_filter or lob_filter == lob)
            match_channel = (not channel_filter or channel_filter == channel)
            
            if match_agent and match_lob and match_channel:
                filtered_records.append(c)
                row = []
                for f in self.TABLE_COLUMNS:
                    if f == 'aht':
                        handled = (c.get('inbound_tx', 0) or 0) + (c.get('outbound_tx', 0) or 0)
                        aht = ((c.get('handle_time', 0) or 0) + (c.get('acw', 0) or 0)) / handled if handled else 0
                        row.append(f"{aht:.1f}")
                    else:
                        row.append(c.get(f, ''))
                self.tree.insert('', 'end', values=row)
        
        # Actualizar KPIs para los registros filtrados
        if filtered_records:
            kpi = ContactKPICalculator(filtered_records)
            aht_overall = kpi.aht()
            aht_ch = kpi.aht_by_channel()
            self.kpi_aht_overall.set_value(f"{aht_overall:.1f}s")
            self.kpi_aht_phone.set_value(f"{aht_ch.get('Phone', 0):.1f}s")
            self.kpi_aht_chat.set_value(f"{aht_ch.get('Chat', 0):.1f}s")
        else:
            self.kpi_aht_overall.set_value("0.0s")
            self.kpi_aht_phone.set_value("0.0s")
            self.kpi_aht_chat.set_value("0.0s")
        
        self.kpi_total.set_value(str(len(filtered_records)))
        self.status.set(f'Filtered: {len(filtered_records)} contacts')

    def _clear_filters(self):
        self.search_agent_id.delete(0, 'end')
        self.search_lob.delete(0, 'end')
        self.search_channel.delete(0, 'end')
        # Restore all KPIs
        kpi = self.ctrl.kpis()
        self.kpi_aht_overall.set_value(f"{kpi.get('aht_overall', 0):.1f}s")
        aht_ch = kpi.get('aht_by_channel', {})
        self.kpi_aht_phone.set_value(f"{aht_ch.get('Phone', 0):.1f}s")
        self.kpi_aht_chat.set_value(f"{aht_ch.get('Chat', 0):.1f}s")
        self.kpi_total.set_value(str(len(self.all_contacts)))
        self.refresh()

    # ---------- Formulario CRUD ----------
    def _form(self):
        box = ttk.LabelFrame(self.frame, text='Contact Record',
                              padding=8)
        box.pack(fill='x', padx=8, pady=4)
        self.entries = {}

        # Organizar los 11 campos en 2 filas
        per_row = 6
        for i, f in enumerate(self.FORM_FIELDS):
            r = (i // per_row) * 2
            c = i % per_row
            ttk.Label(box, text=f.replace('_', ' ').title(),
                      font=('Segoe UI', 8)
                      ).grid(row=r, column=c, padx=3, pady=1, sticky='w')

            # Channel es dropdown, los demas son Entry
            if f == 'channel':
                e = ttk.Combobox(box, values=self.VALID_CHANNELS,
                                  width=11, state='readonly')
            else:
                e = ttk.Entry(box, width=13)
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
            width = 130 if c in ('contact_id', 'lob') else 90
            self.tree.column(c, width=width, anchor='center')

        scroll = ttk.Scrollbar(frame, orient='vertical',
                                command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side='left', fill='both', expand=True)
        scroll.pack(side='right', fill='y')
        self.tree.bind('<<TreeviewSelect>>', self._on_select)

    # ---------- Seccion de Forecast ----------
    def _forecast_section(self):
        fc_box = ttk.LabelFrame(self.frame,
                                 text='Daily Volume Forecast by Channel',
                                 padding=6)
        fc_box.pack(fill='both', expand=False, padx=8, pady=4)

        controls = ttk.Frame(fc_box)
        controls.pack(fill='x', pady=2)
        ttk.Label(controls, text='Channel:').pack(side='left', padx=4)
        self.channel_var = tk.StringVar(value='Phone')
        ttk.Combobox(controls, textvariable=self.channel_var,
                      values=self.VALID_CHANNELS, width=10,
                      state='readonly'
                      ).pack(side='left', padx=4)

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
        # Cargar todos los contactos
        self.all_contacts = self.ctrl.repo.find_all()
        
        # Tabla
        for r in self.tree.get_children():
            self.tree.delete(r)
        
        # Mostrar contactos (con filtros si existen)
        agent_id_filter = self.search_agent_id.get().strip().lower()
        lob_filter = self.search_lob.get().strip().lower()
        channel_filter = self.search_channel.get().strip().lower()
        
        for c in self.all_contacts:
            agent_id = str(c.get('agent_id', '')).lower()
            lob = str(c.get('lob', '')).lower()
            channel = str(c.get('channel', '')).lower()
            
            match_agent = (not agent_id_filter or agent_id_filter == agent_id)
            match_lob = (not lob_filter or lob_filter == lob)
            match_channel = (not channel_filter or channel_filter == channel)
            
            if match_agent and match_lob and match_channel:
                row = []
                for f in self.TABLE_COLUMNS:
                    if f == 'aht':
                        handled = (c.get('inbound_tx', 0) or 0) + (c.get('outbound_tx', 0) or 0)
                        aht = ((c.get('handle_time', 0) or 0) + (c.get('acw', 0) or 0)) / handled if handled else 0
                        row.append(f"{aht:.1f}")
                    else:
                        row.append(c.get(f, ''))
                self.tree.insert('', 'end', values=row)

        # KPI cards
        kpis = self.ctrl.kpis()
        self.kpi_aht_overall.set_value(
            f"{kpis.get('aht_overall', 0):.1f}s")
        aht_ch = kpis.get('aht_by_channel', {})
        self.kpi_aht_phone.set_value(f"{aht_ch.get('Phone', 0):.1f}s")
        self.kpi_aht_chat.set_value(f"{aht_ch.get('Chat', 0):.1f}s")
        self.kpi_total.set_value(str(len(self.ctrl.repo.find_all())))

    # ---------- CRUD handlers ----------
    def _read_form(self):
        """Lee el formulario y convierte los campos numericos a int."""
        data = {}
        for k, e in self.entries.items():
            val = e.get().strip()
            if k in self.NUMERIC_FIELDS:
                data[k] = int(val) if val else 0
            else:
                data[k] = val
        return data

    def _create(self):
        try:
            self.ctrl.create(self._read_form())
            self.status.set('Contact created')
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
            messagebox.showwarning('Update',
                                    'Selecciona una fila primero')
            return
        contact_id = self.tree.item(sel[0])['values'][0]
        try:
            self.ctrl.update(contact_id, self._read_form())
            self.status.set('Contact updated')
            self.refresh()
        except CallCenterError as ex:
            messagebox.showerror(ex.code, ex.message)

    def _delete(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning('Delete',
                                    'Selecciona una fila primero')
            return
        contact_id = self.tree.item(sel[0])['values'][0]
        if not messagebox.askyesno('Confirmar',
                f'Eliminar contacto {contact_id}?'):
            return
        try:
            self.ctrl.delete(contact_id)
            self.status.set('Contact deleted')
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
            entry = self.entries[f]
            # Combobox y Entry tienen distinta forma de set
            if isinstance(entry, ttk.Combobox):
                entry.set(str(col_map.get(f, '')))
            else:
                entry.delete(0, 'end')
                if f in col_map:
                    entry.insert(0, str(col_map[f]))

    def _clear(self):
        for entry in self.entries.values():
            if isinstance(entry, ttk.Combobox):
                entry.set('')
            else:
                entry.delete(0, 'end')

    # ---------- Forecast handler ----------
    def _run_forecast(self):
        channel = self.channel_var.get()
        try:
            horizon = int(self.horizon_var.get())
        except ValueError:
            horizon = 7

        try:
            result = self.ctrl.forecast_volume(channel, horizon=horizon)

            history = result.get('history', [])
            preds = result.get('predictions', [])
            low = result.get('confidence_low', [])
            high = result.get('confidence_high', [])
            method = result.get('best_method', 'forecast')
            mae = result.get('mae', 0)

            if not history or len(history) < 5:
                messagebox.showinfo('Forecast',
                    'No hay suficiente historia para pronosticar')
                return

            self.chart.render(history, preds, low, high,
                f"Volume forecast for {channel} ({method})")
            self.status.set(f"Forecast: {method}, MAE={mae:.2f}")
        except CallCenterError as ex:
            messagebox.showerror(ex.code, ex.message)