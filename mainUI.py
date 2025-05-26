import sys
import csv
import sqlite3
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox
from window_book_ui import Ui_MainWindow

DB_NAME = "buku.db"

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.setup_database()
        self.load_data()

        self.editing_id = None

        self.ui.pushButton.clicked.connect(self.simpan_data)
        self.ui.pushButton_2.clicked.connect(self.ekspor_csv)
        self.ui.actionKeluar.triggered.connect(self.closeEvent)
        self.ui.actionSimpan.triggered.connect(self.simpan_data)
        self.ui.actionEkspor_ke_CSV.triggered.connect(self.ekspor_csv)
        self.ui.actionCari_Judul.triggered.connect(self.cari_judul)
        self.ui.actionHapus_Data.triggered.connect(self.hapus_data)
        self.ui.cariJudul.textChanged.connect(self.cari_judul)
        self.ui.delete_btn.clicked.connect(self.hapus_data)
        self.ui.tableWidget.itemChanged.connect(self.perbarui_data_di_database)
        self.is_updating_table = False

    def setup_database(self):
        self.conn = sqlite3.connect(DB_NAME)
        self.db_cursor = self.conn.cursor()
        self.db_cursor.execute('''
            CREATE TABLE IF NOT EXISTS buku (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                judul TEXT NOT NULL,
                pengarang TEXT NOT NULL,
                tahun TEXT NOT NULL
            )
        ''')
        self.conn.commit()

    def load_data(self):
        self.is_updating_table = True
        self.ui.tableWidget.setRowCount(0)
        self.db_cursor.execute("SELECT * FROM buku")
        for row_index, row_data in enumerate(self.db_cursor.fetchall()):
            self.ui.tableWidget.insertRow(row_index)
            for col_index, data in enumerate(row_data):
                self.ui.tableWidget.setItem(row_index, col_index, QtWidgets.QTableWidgetItem(str(data)))
        self.is_updating_table = False

    def simpan_data(self):
        judul = self.ui.judulLineEdit.text()
        pengarang = self.ui.pengarangLineEdit.text()
        tahun = self.ui.tahunLineEdit.text()

        if not (judul and pengarang and tahun):
            QMessageBox.warning(self, "Input Error", "Semua field harus diisi!")
            return

        if self.editing_id is not None:
            self.db_cursor.execute(
                "UPDATE buku SET judul = ?, pengarang = ?, tahun = ? WHERE id = ?",
                (judul, pengarang, tahun, self.editing_id)
            )
            QMessageBox.information(self, "Sukses", "Data berhasil diperbarui.")
        else:
            self.db_cursor.execute(
                "INSERT INTO buku (judul, pengarang, tahun) VALUES (?, ?, ?)",
                (judul, pengarang, tahun)
            )
            QMessageBox.information(self, "Sukses", "Data berhasil disimpan.")

        self.conn.commit()
        self.load_data()

        self.ui.judulLineEdit.clear()
        self.ui.pengarangLineEdit.clear()
        self.ui.tahunLineEdit.clear()
        self.editing_id = None

    def ekspor_csv(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Simpan CSV", "", "CSV Files (*.csv)")
        if not path:
            return

        with open(path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            headers = ["ID", "Judul", "Pengarang", "Tahun"]
            writer.writerow(headers)

            for row in range(self.ui.tableWidget.rowCount()):
                data_row = []
                for col in range(self.ui.tableWidget.columnCount()):
                    item = self.ui.tableWidget.item(row, col)
                    data_row.append(item.text() if item else '')
                writer.writerow(data_row)

        QMessageBox.information(self, "Sukses", "Data berhasil diekspor ke CSV.")

    def cari_judul(self):
        keyword = self.ui.cariJudul.text().strip().lower()
        self.ui.tableWidget.setRowCount(0)

        if keyword == "":
            self.load_data()
            return

        query = "SELECT * FROM buku WHERE LOWER(judul) LIKE ?"
        self.db_cursor.execute(query, ('%' + keyword + '%',))

        for row_index, row_data in enumerate(self.db_cursor.fetchall()):
            self.ui.tableWidget.insertRow(row_index)
            for col_index, data in enumerate(row_data):
                self.ui.tableWidget.setItem(row_index, col_index, QtWidgets.QTableWidgetItem(str(data)))

    def hapus_data(self):
        selected_row = self.ui.tableWidget.currentRow()
        if selected_row >= 0:
            item = self.ui.tableWidget.item(selected_row, 0)
            if item:
                reply = QMessageBox.question(
                    self,
                    "Konfirmasi Hapus",
                    "Apakah Anda yakin ingin menghapus data ini?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    book_id = int(item.text())
                    self.db_cursor.execute("DELETE FROM buku WHERE id = ?", (book_id,))
                    self.conn.commit()
                    self.load_data()
                    if self.editing_id == book_id:
                        self.editing_id = None
                        self.ui.judulLineEdit.clear()
                        self.ui.pengarangLineEdit.clear()
                        self.ui.tahunLineEdit.clear()
        else:
            QMessageBox.warning(self, "Peringatan", "Pilih baris yang akan dihapus.")
    
    def perbarui_data_di_database(self, item):
        if self.is_updating_table:
            return  

        row = item.row()

        # Ambil semua item di baris yang diubah
        item_id = self.ui.tableWidget.item(row, 0)
        item_judul = self.ui.tableWidget.item(row, 1)
        item_pengarang = self.ui.tableWidget.item(row, 2)
        item_tahun = self.ui.tableWidget.item(row, 3)

        if not (item_id and item_judul and item_pengarang and item_tahun):
            return 

        try:
            book_id = int(item_id.text())
            judul = item_judul.text()
            pengarang = item_pengarang.text()
            tahun = item_tahun.text()

            if not (judul and pengarang and tahun):
                return  

            self.db_cursor.execute(
                "UPDATE buku SET judul = ?, pengarang = ?, tahun = ? WHERE id = ?",
                (judul, pengarang, tahun, book_id)
            )
            self.conn.commit()

            QMessageBox.information(self, "Sukses", "Data berhasil diperbarui.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Gagal memperbarui data: {str(e)}")


    def edit_data(self, row, column):
        item_id = self.ui.tableWidget.item(row, 0)
        item_judul = self.ui.tableWidget.item(row, 1)
        item_pengarang = self.ui.tableWidget.item(row, 2)
        item_tahun = self.ui.tableWidget.item(row, 3)

        if item_id and item_judul and item_pengarang and item_tahun:
            self.editing_id = int(item_id.text())
            self.ui.judulLineEdit.setText(item_judul.text())
            self.ui.pengarangLineEdit.setText(item_pengarang.text())
            self.ui.tahunLineEdit.setText(item_tahun.text())

    def closeEvent(self, event):
        self.conn.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec_())