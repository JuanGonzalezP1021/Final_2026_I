import tkinter as tk

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg
)


class ForecastChart(tk.Frame):

    def __init__(self, parent):
        super().__init__(parent)

        self.fig = Figure(
            figsize=(6, 3),
            dpi=100
        )

        self.ax = self.fig.add_subplot(111)

        self.canvas = FigureCanvasTkAgg(
            self.fig,
            master=self
        )

        self.canvas.get_tk_widget().pack(
            fill='both',
            expand=True
        )

    def render(
        self,
        history,
        predictions,
        low,
        high,
        title
    ):
        self.ax.clear()

        h = len(history)

        x_hist = list(range(h))
        x_fc = list(range(h, h + len(predictions)))

        self.ax.plot(
            x_hist,
            history,
            color='#1b263b',
            label='history'
        )

        self.ax.plot(
            x_fc,
            predictions,
            color='#e63946',
            linestyle='--',
            label='forecast'
        )

        self.ax.fill_between(
            x_fc,
            low,
            high,
            color='#e63946',
            alpha=0.15,
            label='95% CI'
        )

        self.ax.set_title(
            title,
            fontsize=10
        )

        self.ax.legend(fontsize=8)
        self.ax.grid(True, alpha=0.3)

        self.fig.tight_layout()
        self.canvas.draw()