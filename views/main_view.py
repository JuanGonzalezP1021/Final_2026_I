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
        # Header
        header = tk.Frame(self.root, bg='#0d1b2a', height=44)
        header.pack(fill='x')
        
        tk.Label(
            header, text='Call Center System',
            font=('Segoe UI', 14, 'bold'),
            fg='white', bg='#0d1b2a'
        ).pack(side='left', padx=14, pady=10)
        
        self.status_var = tk.StringVar(value='Ready')
        tk.Label(
            header, textvariable=self.status_var,
            fg='#a8dadc', bg='#0d1b2a',
            font=('Segoe UI', 9)
        ).pack(side='right', padx=14)

        # Tabulation
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=8, pady=8)
        
        self.agent_tab = AgentView(notebook, self.status_var)
        self.contact_tab = ContactView(notebook, self.status_var)
        self.prod_tab = ProductivityView(notebook, self.status_var)
        
        notebook.add(self.agent_tab.frame, text=' Agents ')
        notebook.add(self.contact_tab.frame, text=' Contacts ')
        notebook.add(self.prod_tab.frame, text=' Productivity ')

    def run(self):
        self.root.mainloop()