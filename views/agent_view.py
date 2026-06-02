import tkinter as tk
from tkinter import ttk, messagebox
from controllers.agent_controller import AgentController
from domain.exceptions.custom_exceptions import CallCenterError
from views.widgets.kpi_card import KPICard

class AgentView:
    FIELDS = ('agent_id', 'team_manager', 'active_date', 'days_range', 'tenurity')

    def __init__(self, parent, status_var):
        self.ctrl = AgentController()
        self.status = status_var
        self.frame = ttk.Frame(parent)
        
        self._kpi_row()
        self._form()
        self._table()
        self.refresh()

    def _kpi_row(self):
        row = ttk.Frame(self.frame)
        row.pack(fill='x', padx=8, pady=6)
        
        self.kpi_head = KPICard(row, 'Headcount', 'total agents')
        self.kpi_risk = KPICard(row, 'Attrition Risk', '% new hires')
        self.kpi_over = KPICard(row, 'TLs over capacity', 'count > 15 reports')
        
        for w in (self.kpi_head, self.kpi_risk, self.kpi_over):
            w.pack(side='left', expand=True, fill='x', padx=4)

    def _form(self):
        box = ttk.LabelFrame(self.frame, text='Agent', padding=8)
        box.pack(fill='x', padx=8, pady=4)
        
        self.entries = {}
        for i, f in enumerate(self.FIELDS):
            ttk.Label(box, text=f.replace('_', ' ').title()).grid(row=0, column=i, padx=4)
            e = ttk.Entry(box, width=14)
            e.grid(row=1, column=i, padx=4, pady=4)
            self.entries[f] = e
            
        btns = ttk.Frame(box)
        btns.grid(row=2, column=0, columnspan=5, pady=6)
        
        actions = [('Create', self._create), ('Update', self._update), 
                   ('Delete', self._delete), ('Clear', self._clear)]
        
        for txt, cmd in actions:
            ttk.Button(btns, text=txt, command=cmd).pack(side='left', padx=4)

    def _table(self):
        self.tree = ttk.Treeview(self.frame, columns=self.FIELDS, show='headings', height=14)
        
        for c in self.FIELDS:
            self.tree.heading(c, text=c.replace('_', ' ').title())
            self.tree.column(c, width=140)
            
        self.tree.pack(fill='both', expand=True, padx=8, pady=4)
        self.tree.bind('<<TreeviewSelect>>', self._on_select)

    def refresh(self):
        # Limpiar tabla
        for r in self.tree.get_children():
            self.tree.delete(r)
            
        # Cargar datos
        for a in self.ctrl.repo.find_all():
            self.tree.insert('', 'end', values=[a[f] for f in self.FIELDS])
            
        # Actualizar KPIs
        k = self.ctrl.kpis()
        self.kpi_head.set_value(str(k['headcount']))
        self.kpi_risk.set_value(f"{k['attrition_risk']:.0%}")
        self.kpi_over.set_value(str(len(k['tls_over_capacity'])))

    def _create(self):
        try:
            self.ctrl.create({k: e.get() for k, e in self.entries.items()})
            self.status.set('Agent created')
            self.refresh()
            self._clear()
        except CallCenterError as ex:
            messagebox.showerror(ex.code, ex.message)
            self.status.set(f'Error: {ex.code}')

    def _update(self):
        try:
            data = {k: e.get() for k, e in self.entries.items()}
            aid = data.pop('agent_id')
            self.ctrl.update(aid, data)
            self.status.set('Agent updated')
            self.refresh()
        except CallCenterError as ex:
            messagebox.showerror(ex.code, ex.message)

    def _delete(self):
        aid = self.entries['agent_id'].get()
        if not messagebox.askyesno('Confirm', f'Delete {aid}?'):
            return
        try:
            self.ctrl.delete(aid)
            self.status.set('Agent deleted')
            self.refresh()
            self._clear()
        except CallCenterError as ex:
            messagebox.showerror(ex.code, ex.message)

    def _on_select(self, _):
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0])['values']
        for i, f in enumerate(self.FIELDS):
            self.entries[f].delete(0, 'end')
            self.entries[f].insert(0, str(vals[i]))

    def _clear(self):
        for e in self.entries.values():
            e.delete(0, 'end')