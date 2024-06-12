import sys
import os
import numpy as np
import pandas as pd
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, QFileDialog, QLineEdit, QComboBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
from matplotlib.ticker import FuncFormatter

class GraphingMachine(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Graficador de funciones de osciloscopio")
        self.setFixedSize(600, 600)

        self.file_name = ""
        self.initUI()

    def initUI(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.central_widget.setLayout(main_layout)

        self.banner_label = QLabel()
        pixmap = QPixmap("banner.png")
        self.banner_label.setPixmap(pixmap)
        self.banner_label.setAlignment(Qt.AlignTop | Qt.AlignCenter)  # Alinear arriba y centro
        main_layout.addWidget(self.banner_label)

        self.label = QLabel("Arrastra y suelta un archivo CSV aquí o haz clic para buscar.")
        self.label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.label)

        button_layout = QHBoxLayout()
        main_layout.addLayout(button_layout)

        self.btn_browse = QPushButton("Buscar")
        self.btn_browse.clicked.connect(self.browse_file)
        button_layout.addWidget(self.btn_browse)

        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            valid_data = self.leer_y_validar_csv(file_path)
            if valid_data is not False:
                self.file_name = os.path.basename(file_path)
                self.open_plot_window(valid_data)

    def browse_file(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Abrir archivo CSV", "", "Archivos CSV (*.csv)", options=options)
        if file_path:
            valid_data = self.leer_y_validar_csv(file_path)
            if valid_data is not False:
                self.file_name = os.path.basename(file_path)
                self.open_plot_window(valid_data)

    def leer_y_validar_csv(self, ruta):
        try:
            if not ruta.lower().endswith('.csv'):
                raise ValueError("El archivo no es de tipo CSV.")
            if not os.path.isfile(ruta):
                raise FileNotFoundError("El archivo no existe.")

            df = pd.read_csv(ruta, header=None)

            try:
                if df.iat[0, 0]!= "x-axis":
                    raise ValueError('La primera celda no contiene "x-axis".')
                for i in range(1, len(df.columns)):
                    if df.iat[0, i]!= str(i):
                        raise ValueError(f'Se esperaba {i} pero se encontró {df.iat[0, i]}.')
                if df.iat[1, 0]!= "second":
                    raise ValueError('La segunda celda de la primera columna no contiene "second".')
                for i in range(1, len(df.columns)):
                    if df.iat[1, i]!= "Volt":
                        raise ValueError(f'Se esperaba "Volt" pero se encontró {df.iat[1, i]}.')

                return df
            except ValueError as ve:
                self.label.setText("Error en la validación del DataFrame: " + str(ve))
                return False

        except ValueError as ve:
            self.label.setText("Error al leer el archivo CSV: " + str(ve))
            return False
        except FileNotFoundError as fnfe:
            self.label.setText("Error al leer el archivo CSV: " + str(fnfe))
            return False
        except Exception as e:
            self.label.setText("Error al leer el archivo CSV: " + str(e))
            return False

    def open_plot_window(self, dataframe):
        self.plot_window = PlotWindow(self.file_name, dataframe)
        self.plot_window.show()

class PlotWindow(QMainWindow):
    def __init__(self, file_name, dataframe):
        super().__init__()
        self.setWindowTitle(f"Gráfico de {file_name}")
        self.file_name = file_name
        self.dataframe = dataframe

        self.x_offsets = [0.0] * len(dataframe.columns)  # Initialize x offsets for each channel
        self.y_offsets = [0.0] * len(dataframe.columns)  # Initialize y offsets for each channel

        self.selected_channel = 0
        self.amplitude = 1.0  # Inicializar la amplitud

        self.initUI()

    def initUI(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        layout = QVBoxLayout(self.central_widget)
        
        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.fig)
        self.toolbar = NavigationToolbar(self.canvas, self)

        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

        self.combo = QComboBox(self)
        for i in range(1, self.dataframe.shape[1]):
            self.combo.addItem(f'Canal {i}')
        self.combo.setCurrentIndex(0)
        self.combo.activated.connect(self.update_selected_channel)
        layout.addWidget(self.combo)

        # Ajustar la posición de la barra deslizante para evitar superposición con el gráfico y las etiquetas
        slider_ax = plt.axes([0.15, 0.01, 0.7, 0.03], facecolor='lightgoldenrodyellow')  # Posición ajustada
        self.slider = Slider(slider_ax, 'Amplitud', valmin=0.1, valmax=2.0, valinit=self.amplitude, valstep=0.1)
        self.slider.on_changed(self.update_amplitude)

        offset_x_layout = QHBoxLayout()
        self.offset_x_input = QLineEdit()
        self.offset_x_input.setPlaceholderText("Desplazamiento en X")
        self.update_x_btn = QPushButton("Actualizar X")
        self.update_x_btn.clicked.connect(self.update_x_offset)
        offset_x_layout.addWidget(self.offset_x_input)
        offset_x_layout.addWidget(self.update_x_btn)

        offset_y_layout = QHBoxLayout()
        self.offset_y_input = QLineEdit()
        self.offset_y_input.setPlaceholderText("Desplazamiento en Y")
        self.update_y_btn = QPushButton("Actualizar Y")
        self.update_y_btn.clicked.connect(self.update_y_offset)
        offset_y_layout.addWidget(self.offset_y_input)
        offset_y_layout.addWidget(self.update_y_btn)

        layout.addLayout(offset_x_layout)
        layout.addLayout(offset_y_layout)

        self.plot_csv(self.dataframe)

    def update_selected_channel(self, index):
        self.selected_channel = index
        self.replot()

    def plot_csv(self, dataframe):
        try:
            time = dataframe.iloc[2:, 0].tolist()
            volts = [dataframe.iloc[2:, i+1].tolist() for i in range(dataframe.shape[1]-1)]
            for i in range(len(time)):
                time[i] = float(time[i])
            for i in range(len(volts)):
                for j in range(len(volts[i])):
                    volts[i][j] = float(volts[i][j])
            self.plot(time, volts)
        except Exception as e:
            print(f"Error: {e}")

    def plot(self, time, volts):
        self.time = time
        self.volts = volts
        self.ax.clear()
        for i, channel_data in enumerate(volts):
            self.ax.plot(time, channel_data, label=f"Canal {i+1}")

        def format_func(value, tick_number):
            if value == 0:
                return '0'
            else:
                exp = int(np.floor(np.log10(np.abs(value))))
                mant = value / 10**exp
                return f'{mant:.2f}'

        self.ax.xaxis.set_major_formatter(FuncFormatter(format_func))
        self.ax.yaxis.set_major_formatter(FuncFormatter(format_func))

        def update_labels():
            x_min, x_max = self.ax.get_xlim()
            y_min, y_max = self.ax.get_ylim()
            x_scale = (x_max - x_min) / 10
            y_scale = (y_max - y_min) / 10
            x_exponent = int(f"{x_scale:.1e}".split('e')[1])
            y_exponent = int(f"{y_scale:.1e}".split('e')[1])
            self.ax.set_xlabel(f'Segundos [e{x_exponent} s]')
            self.ax.set_ylabel(f'Voltios [e{y_exponent} v]')
            self.fig.subplots_adjust(bottom=0.14)  # Set the bottom margin to 0.14
            self.fig.canvas.draw_idle()

        update_labels()
        self.ax.callbacks.connect('xlim_changed', lambda ax: update_labels())
        self.ax.callbacks.connect('ylim_changed', lambda ax: update_labels())

        self.ax.grid(True)  # Agregar grillado al gráfico

        plt.suptitle(f'Gráfico de {self.file_name}', fontsize=14, fontweight='bold')  # Título arriba
        plt.legend()

        self.fig.subplots_adjust(top=0.9)  # Ajustar posición del título

        self.fig.canvas.draw()

    def update_amplitude(self, val):
        self.amplitude = val
        channel_data = np.array(self.volts[self.selected_channel])
        self.ax.lines[self.selected_channel].set_ydata((self.amplitude * channel_data) + self.y_offsets[self.selected_channel])
        self.fig.canvas.draw_idle()

    def update_x_offset(self):
        try:
            new_offset = float(self.offset_x_input.text())
            self.x_offsets[self.selected_channel] += new_offset
            self.replot()
        except ValueError:
            print("Error: el desplazamiento en X no es válido.")

    def update_y_offset(self):
        try:
            new_offset = float(self.offset_y_input.text())
            self.y_offsets[self.selected_channel] += new_offset
            self.replot()
        except ValueError:
            print("Error: el desplazamiento en Y no es válido.")

    def replot(self):
        volts_aux = np.array(self.volts[self.selected_channel])
        shifted_time = [t + self.x_offsets[self.selected_channel] for t in self.time]
        shifted_volts = [(self.amplitude * v) + self.y_offsets[self.selected_channel] for v in volts_aux]
        
        self.ax.lines[self.selected_channel].set_data(shifted_time, shifted_volts)

        self.ax.legend()
        self.fig.canvas.draw_idle()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GraphingMachine()
    window.show()
    sys.exit(app.exec_())
