from PyQt5.QtWidgets import QApplication, QWidget, QComboBox, QPushButton, QLabel, QHBoxLayout, QVBoxLayout
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView, QDesktopWidget, QLineEdit
from PyQt5 import QtCore

from quickstart import get_teachers_data_from_google_sheets
from enviar_aviso_profes import send_payloads, check_teachers_id, read_teachers_from_file
from guardar_profes import run_discord_bot
from pathlib import Path

import os
import sys
import pandas as pd
import ctypes


# Icon
if getattr(sys, 'frozen', False):
    icon_path = os.path.join(sys._MEIPASS, 'icon.png')
else:
    icon_path = os.path.abspath(Path(__file__).parent / "icon.png")

class DiscordWindow(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.tabla_discord = QTableWidget()
        self.tabla_discord.setColumnCount(1)
        self.tabla_discord.setHorizontalHeaderLabels(["Nombres"])        
        self.tabla_discord.setSortingEnabled(False)
        self.tabla_discord.sortByColumn(0, QtCore.Qt.SortOrder.AscendingOrder)
        self.search_bar = QLineEdit()
        self.search_bar.textChanged.connect(self.search_teacher_name)
        layout.addWidget(self.search_bar)
        layout.addWidget(self.tabla_discord)        
        self.setLayout(layout)   
        self.setWindowTitle("Nombres de los profesores en discord") 
        self.setFixedSize(600, 600)

        # Get names
        teachers_names = read_teachers_from_file()

        # Set names in table
        self.tabla_discord.setRowCount(0)
        teachers_dict = {self.fixedTeacherName(teacher) : value for teacher, value in teachers_names.items()}

        i :int = 0
        for teacher in teachers_dict.keys():            
            self.tabla_discord.insertRow(i)
            self.tabla_discord.setItem(i,0, QTableWidgetItem(self.fixedTeacherName(teacher)))
            i += 1  
        self.tabla_discord.setSortingEnabled(True)
        self.tabla_discord.horizontalHeader().setStretchLastSection(True)
        self.tabla_discord.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def fixedTeacherName(self, teacher : str) -> str:
        return teacher.replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u')
        
    def search_teacher_name(self, name):
        self.tabla_discord.setCurrentItem(None)
        if not name:
            return
        matching_names = self.tabla_discord.findItems(name, QtCore.Qt.MatchFlag.MatchContains)
        if matching_names:            
            self.tabla_discord.setCurrentItem(matching_names[0])
                    
class Home(QWidget):
    # Constructor
    def __init__(self):
        super().__init__()
        try:
            run_discord_bot()
        except Exception as e:
            if e.args[0] == "ENV_NOT_FOUND":
                self.alerta("Error", "No se encontraron las credenciales del bot.")                
                exit()
            else:
                self.alerta("Error", "Ha ocurrido un error inesperado con el bot de discord.")
                exit()    
        self.discord_window = DiscordWindow()        
        self.initUI()
        self.settings()

    # App Object and Design
    def initUI(self):
        self.title = QLabel("Menciones de profesores")
        self.description = QLabel("Para hacer una sustitución,\ncambia el nombre de un profesor\ny manda la mención.")
        self.see_discord_names = QPushButton("Ver nombres en discord")
        self.see_discord_names.clicked.connect(self.discordWindow)
        self.quick_check = QPushButton("Comprobar profesores discord")
        self.quick_check.clicked.connect(self.button_quick_check)
        self.input_week_day = QComboBox()
        self.input_week_day.addItems(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
        self.input_week_day.setCurrentIndex(-1)
        self.input_week_day.currentTextChanged.connect(self.get_mention)

        self.input_hour = QComboBox()
        self.input_hour.setVisible(False)
        self.reset = QPushButton("Reset")
        self.reset.clicked.connect(self.button_reset)
        self.send_mention = QPushButton("Enviar Mencion")
        self.send_mention.clicked.connect(self.button_mentions)
        self.sheet_table = QTableWidget()
        self.sheet_table.setColumnCount(3)
        self.sheet_table.setHorizontalHeaderLabels(["Nombre", "Dia", "Hora"])
        header = self.sheet_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)        
                  

        master = QHBoxLayout()

        col1 = QVBoxLayout()
        col1.addWidget(self.title)
        col1.addWidget(self.description)
        col1.addWidget(self.see_discord_names)
        col1.addWidget(self.quick_check)
        col1.addWidget(self.input_week_day)        
        col1.addWidget(self.input_hour)
        col1.addWidget(self.send_mention)
        col1.addWidget(self.reset)

        col2 = QVBoxLayout()
        col2.addWidget(self.sheet_table)

        master.addLayout(col1, 20)
        master.addLayout(col2, 80)
        self.setLayout(master)

    # App Settings
    def settings(self):
        self.setWindowTitle("Menciones de profesores")
        qtRectangle = self.frameGeometry()
        # centerPoint = QDesktopWidget().availableGeometry().center()
        # qtRectangle.moveCenter(centerPoint)
        # self.move(qtRectangle.topLeft())
        centerPoint = QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())
        self.setFixedSize(600, 600)
        self.setWindowIcon(QIcon(icon_path))                      
        

    # Get info
    def get_mention(self):
        if not self.input_hour.isVisible():
            self.input_hour.setVisible(True)
            self.input_hour.clear()
        try:    
            data_raw = get_teachers_data_from_google_sheets()        
            if data_raw is None:
                self.alerta("Error", "No se pudo obtener la informacion.")
                exit()     
            dataPD = pd.DataFrame(data_raw)
            dataPD.columns = dataPD.iloc[0]
            dataPD = dataPD[2:]
            
            dataPD = dataPD[dataPD["DAYOFWEEK"] == self.input_week_day.currentText()]    

            dataPD = dataPD.drop(dataPD[dataPD["HOURS"] == ""].index)

            dataPD = dataPD[['TEACHER', 'DAYOFWEEK', 'HOURS']]            
            hour_dict = dataPD["HOURS"].value_counts().to_dict()            
            self.input_hour.clear()
            self.input_hour.addItems([key for key in sorted(hour_dict.keys())])
            self.input_hour.setCurrentIndex(-1)
            self.input_hour.currentTextChanged.connect(lambda: self.update_table(dataPD)) 
        except Exception as e:
            self.alerta("Error", f"Ha ocurrido un error inesperado a la hora de tomar la información de Google Sheets.\n{e}")            
            exit()

    # Update Table
    @QtCore.pyqtSlot(int)
    def update_table(self, data : pd.DataFrame):  
        self.sheet_table.setRowCount(0)

        data = data[data["HOURS"] == self.input_hour.currentText()]
        self.sheet_table.setRowCount(0)
        i : int = 0
        for g, row in data.iterrows():
            self.sheet_table.insertRow(i)
            self.sheet_table.setItem(i, 0, QTableWidgetItem(row["TEACHER"]))
            self.sheet_table.setItem(i, 1, QTableWidgetItem(row["DAYOFWEEK"]))
            self.sheet_table.setItem(i, 2, QTableWidgetItem(row["HOURS"])) 
            i += 1                
    # Send mentions
    def button_mentions(self):
        if self.input_week_day.currentText() == "":
            self.alerta("Error", "Por favor selecciona un dia")
            return
        if self.input_hour.currentText() == "":
            self.alerta("Error", "Por favor selecciona una hora")
            return        
        if self.sheet_table.rowCount() == 0:
            self.alerta("Error", "No hay profesores en esta hora")
            return
        
        nombres_profes = ""
        for i in range(self.sheet_table.rowCount()):
            if self.sheet_table.item(i, 0).text().strip() != "":
                nombres_profes += self.sheet_table.item(i, 0).text() + '\n'
        nombres_profes = nombres_profes.rstrip('\n')
        try:
            send_payloads(nombres_profes, self.input_hour.currentText())
            self.alerta("Correcto", "Menciones enviadas correctamente")
        except KeyError as e:
            self.alerta("Error", f"Error en la lista de profesores a mencionar:\n{e.args[0]}"
                        "\nPrueba a escribir a los profesores como aparecen en discord")                  
        except Exception as e:
            self.alerta("Error", f"Ha ocurrido un error inesperado a la hora de enviar las menciones.\n{e}")
            exit()
    # Reset App
    def button_reset(self):
        self.input_week_day.setCurrentIndex(-1)
        self.input_hour.clear()
        self.input_hour.setVisible(False)
        self.sheet_table.setRowCount(0)
        self.sheet_table.clearContents()
        
    # Quick check
    def button_quick_check(self):
        data_raw = get_teachers_data_from_google_sheets()        
        if data_raw is None:
            self.alerta("Error", "No se pudo obtener la informacion.")
            exit()     
        dataPD = pd.DataFrame(data_raw)
        dataPD.columns = dataPD.iloc[0]
        dataPD = dataPD[2:]
        teachers_names = "\n".join(dataPD["TEACHER"].unique())
        isOk, bad_names = check_teachers_id(read_teachers_from_file(), teachers_names)
        if isOk:
            self.alerta("Correcto", "Todos los profesores de Google Sheets estan en el fichero de profesores.")
        else:
            self.alerta("Error", f"Algunos profesores de Google Sheets no estan en el fichero de profesores.\n{bad_names}")
          
    # New Discord Window
    def discordWindow(self):
        self.discord_window.show()                

    # Alert box
    def alerta(self, title: str, text: str):
        alert = QMessageBox()
        alert.setText(text)
        alert.setWindowTitle(title)
        alert.setWindowIcon(QIcon(icon_path))
        alert.exec_()
# Main Run
if __name__ == '__main__':
    myappid = 'Coding_Giants.Menciones.Envio.1.0' 
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    app = QApplication([])
    app.setWindowIcon(QIcon(icon_path))
    main = Home()
    main.show()    
    sys.exit(app.exec_())