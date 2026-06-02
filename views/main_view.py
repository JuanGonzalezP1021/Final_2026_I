import tkinter as tk
from tkinter import ttk
from views.agent_view import AgentView
from views.contact_view import ContactView
from views.productivity_view import ProductivityView

class MainView:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('Call Center Management System')
        self.root.geometry('1100x700')
        self._build()

    def _build(self):
        style = ttk.Style(self.root)
        style.theme_use('clam')
        self.root.configure(bg='#eef2f5')

        style.configure('TFrame', background='#eef2f5')
        style.configure('TLabel', background='#eef2f5', foreground='#1f2937', font=('Segoe UI', 10))
        style.configure('TNotebook', background='#eef2f5', borderwidth=0)
        style.configure('TNotebook.Tab', font=('Segoe UI', 10, 'bold'), padding=[12, 8], background='#dbeafe', foreground='#1e3a8a')
        style.map('TNotebook.Tab', 
                  background=[('selected', '#1d4ed8')], 
                  foreground=[('selected', 'white')],
                  padding=[('selected', [12, 8])],
                  font=[('selected', ('Segoe UI', 10, 'bold'))])
        style.configure('TLabelframe', background='#f8fafc', bordercolor='#d1d5db', relief='solid', borderwidth=1)
        style.configure('TLabelframe.Label', font=('Segoe UI', 10, 'bold'), foreground='#0f172a', background='#f8fafc')
        style.configure('Card.TFrame', background='white', relief='flat', borderwidth=1)
        style.configure('CardTitle.TLabel', background='white', foreground='#1f2937', font=('Segoe UI', 9, 'bold'))
        style.configure('CardValue.TLabel', background='white', foreground='#1d4ed8', font=('Segoe UI', 22, 'bold'))
        style.configure('CardCaption.TLabel', background='white', foreground='#6b7280', font=('Segoe UI', 8))
        style.configure('TButton', font=('Segoe UI', 9, 'bold'), padding=6)
        style.configure('Accent.TButton', background='#2563eb', foreground='white')
        style.map('Accent.TButton', background=[('active', '#1d4ed8')])
        style.configure('TEntry', fieldbackground='white', background='white', bordercolor='#cbd5e1', lightcolor='#93c5fd', darkcolor='#cbd5e1')
        style.configure('TCombobox', fieldbackground='white', background='white')
        style.configure('Treeview', background='white', fieldbackground='white', foreground='#0f172a', rowheight=26, bordercolor='#d1d5db')
        style.configure('Treeview.Heading', font=('Segoe UI', 9, 'bold'), background='#e2e8f0', foreground='#0f172a', relief='flat')
        style.configure('Vertical.TScrollbar', gripcount=0, background='#cbd5e1', troughcolor='#f8fafc', bordercolor='#f8fafc')

        # Header
        header = tk.Frame(self.root, bg='#0d1b2a', height=48)
        header.pack(fill='x')
        
        tk.Label(
            header, text='Call Center System',
            font=('Segoe UI', 14, 'bold'),
            fg='white', bg='#0d1b2a'
        ).pack(side='left', padx=18, pady=10)
        
        self.status_var = tk.StringVar(value='Ready')
        tk.Label(
            header, textvariable=self.status_var,
            fg='#a8dadc', bg='#0d1b2a',
            font=('Segoe UI', 9)
        ).pack(side='right', padx=18)

        # Tabulation
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=12, pady=12)
        
        self.agent_tab = AgentView(notebook, self.status_var)
        self.contact_tab = ContactView(notebook, self.status_var)
        self.prod_tab = ProductivityView(notebook, self.status_var)
        
        notebook.add(self.agent_tab.frame, text='Agents')
        notebook.add(self.contact_tab.frame, text='Contacts')
        notebook.add(self.prod_tab.frame, text='Productivity')

    def run(self):
        self.root.mainloop()