import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTreeWidget, QTreeWidgetItem,
    QDialog, QDialogButtonBox, QComboBox, QRadioButton, QButtonGroup,
    QMessageBox, QFormLayout, QGroupBox, QInputDialog
)

from room_calculator.models import Room, Apartment, Building
from room_calculator.report_generator import ReportGenerator


class NumericField(QWidget):
    """Поле ввода с меткой ошибки снизу."""

    def __init__(self, label_text, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        layout.addWidget(QLabel(label_text))

        self.entry = QLineEdit()
        self.entry.setPlaceholderText("Например: 3.5")
        layout.addWidget(self.entry)

        # Красная метка для ошибки (по умолчанию невидима)
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: red; font-size: 10px;")
        self.error_label.setVisible(False)
        layout.addWidget(self.error_label)

        # Сигнал на изменение текста
        self.entry.textChanged.connect(self._validate)

    def _validate(self):
        text = self.entry.text().strip()
        if not text:
            self.error_label.setVisible(False)
            return
        try:
            value = float(text)
            if value <= 0:
                self.error_label.setText("Ошибка: число должно быть больше 0")
                self.error_label.setVisible(True)
            else:
                self.error_label.setVisible(False)
        except ValueError:
            self.error_label.setText("Ошибка: нужно ввести число (например, 3.5)")
            self.error_label.setVisible(True)

    def is_valid(self):
        text = self.entry.text().strip()
        if not text:
            return False
        try:
            return float(text) > 0
        except ValueError:
            return False

    def value(self):
        return float(self.entry.text().strip())


class RoomDialog(QDialog):
    """Диалог добавления комнаты."""

    def __init__(self, building: Building, parent=None):
        super().__init__(parent)
        self.building = building
        self.setWindowTitle("Добавление комнаты")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        # Квартира
        layout.addWidget(QLabel("Квартира:"))
        self.apt_combo = QComboBox()
        self.apt_combo.addItems([apt.name for apt in building.apartments])
        layout.addWidget(self.apt_combo)

        # Название комнаты
        layout.addWidget(QLabel("Название комнаты:"))
        self.name_entry = QLineEdit()
        self.name_entry.setPlaceholderText("Например: Спальня")
        layout.addWidget(self.name_entry)

        # Числовые поля с валидацией
        self.length_field = NumericField("Длина (м):")
        layout.addWidget(self.length_field)

        self.width_field = NumericField("Ширина (м):")
        layout.addWidget(self.width_field)

        self.height_field = NumericField("Высота (м):")
        layout.addWidget(self.height_field)

        # Утепление
        layout.addWidget(QLabel("Уровень утепления:"))
        insulation_layout = QHBoxLayout()
        self.insulation_group = QButtonGroup(self)
        self.rb_low = QRadioButton("Низкий")
        self.rb_medium = QRadioButton("Средний")
        self.rb_high = QRadioButton("Высокий")
        self.rb_medium.setChecked(True)
        self.insulation_group.addButton(self.rb_low)
        self.insulation_group.addButton(self.rb_medium)
        self.insulation_group.addButton(self.rb_high)
        insulation_layout.addWidget(self.rb_low)
        insulation_layout.addWidget(self.rb_medium)
        insulation_layout.addWidget(self.rb_high)
        layout.addLayout(insulation_layout)

        # Кнопки
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Ok).setText("Добавить")
        button_box.button(QDialogButtonBox.Cancel).setText("Отмена")
        button_box.accepted.connect(self._on_add)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _on_add(self):
        apt_name = self.apt_combo.currentText()
        room_name = self.name_entry.text().strip()

        if not room_name:
            QMessageBox.warning(self, "Ошибка ввода", "Введите название комнаты.")
            return

        if not (self.length_field.is_valid() and
                self.width_field.is_valid() and
                self.height_field.is_valid()):
            QMessageBox.warning(self, "Ошибка ввода",
                                "Проверьте правильность заполнения размеров.")
            return

        # Определяем утепление
        if self.rb_low.isChecked():
            insulation = "low"
        elif self.rb_high.isChecked():
            insulation = "high"
        else:
            insulation = "medium"

        room = Room(
            room_name,
            self.length_field.value(),
            self.width_field.value(),
            self.height_field.value(),
            insulation
        )

        # Добавляем в нужную квартиру
        for apt in self.building.apartments:
            if apt.name == apt_name:
                apt.add_room(room)
                break

        self.accept()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Калькулятор помещений (MVP)")
        self.resize(950, 650)

        self.building = None  # модель данных

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Панель здания
        building_box = QGroupBox("Здание")
        building_layout = QHBoxLayout(building_box)
        self.building_label = QLabel("Название здания: (не задано)")
        building_layout.addWidget(self.building_label)
        building_layout.addStretch()
        btn_rename = QPushButton("Изменить название")
        btn_rename.clicked.connect(self._ask_building_name)
        building_layout.addWidget(btn_rename)
        layout.addWidget(building_box)

        # Дерево структуры
        tree_box = QGroupBox("Структура: Квартиры и Комнаты")
        tree_layout = QVBoxLayout(tree_box)
        self.tree = QTreeWidget()
        self.tree.setColumnCount(5)
        self.tree.setHeaderLabels(
            ["Уровень", "Название", "Площадь, кв.м", "Тепловая мощность, кВт", "Доп. параметры"]
        )
        self.tree.setColumnWidth(0, 100)
        self.tree.setColumnWidth(1, 180)
        self.tree.setColumnWidth(2, 120)
        self.tree.setColumnWidth(3, 170)
        self.tree.setColumnWidth(4, 250)
        tree_layout.addWidget(self.tree)
        layout.addWidget(tree_box)

        # Кнопки управления
        btn_layout = QHBoxLayout()

        btn_add_apt = QPushButton(" Добавить квартиру")
        btn_add_apt.clicked.connect(self._add_apartment)

        btn_add_room = QPushButton(" Добавить комнату")
        btn_add_room.clicked.connect(self._add_room)

        btn_delete = QPushButton(" Удалить выбранное")
        btn_delete.clicked.connect(self._delete_selected)

        btn_refresh = QPushButton(" Обновить расчёт")
        btn_refresh.clicked.connect(self._refresh_tree)

        btn_save = QPushButton(" Сохранить отчёт в Word")
        btn_save.clicked.connect(self._save_report)

        btn_layout.addWidget(btn_add_apt)
        btn_layout.addWidget(btn_add_room)
        btn_layout.addWidget(btn_delete)
        btn_layout.addWidget(btn_refresh)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

        # Итоги
        result_box = QGroupBox("Итоги по зданию")
        result_layout = QVBoxLayout(result_box)
        self.result_label = QLabel("Нет данных")
        self.result_label.setStyleSheet("font-size: 13px; font-weight: bold;")
        result_layout.addWidget(self.result_label)
        layout.addWidget(result_box)

        # Спрашиваем название здания при старте
        self._ask_building_name()

    # Логика
    def _ask_building_name(self):
        name, ok = QInputDialog.getText(
            self, "Название здания", "Введите название здания:",
            text=self.building.name if self.building else ""
        )
        if ok and name.strip():
            if self.building is None:
                self.building = Building(name.strip())
            else:
                self.building.name = name.strip()
            self.building_label.setText(f"Название здания: {self.building.name}")
            self._refresh_tree()

    def _add_apartment(self):
        if not self.building:
            QMessageBox.warning(self, "Внимание", "Сначала задайте название здания.")
            return
        name, ok = QInputDialog.getText(self, "Новая квартира", "Название/номер квартиры:")
        if ok and name.strip():
            self.building.add_apartment(Apartment(name.strip()))
            self._refresh_tree()

    def _add_room(self):
        if not self.building or not self.building.apartments:
            QMessageBox.warning(self, "Внимание", "Сначала добавьте хотя бы одну квартиру.")
            return
        dialog = RoomDialog(self.building, self)
        if dialog.exec():
            self._refresh_tree()

    def _delete_selected(self):
        item = self.tree.currentItem()
        if item is None:
            QMessageBox.information(self, "Информация", "Ничего не выбрано.")
            return

        item_type = item.text(0)

        if item_type == "Квартира":
            apt_name = item.text(1)
            self.building.apartments = [a for a in self.building.apartments if a.name != apt_name]
        elif item_type == "Комната":
            parent = item.parent()
            if parent:
                apt_name = parent.text(1)
                room_name = item.text(1)
                for apt in self.building.apartments:
                    if apt.name == apt_name:
                        apt.rooms = [r for r in apt.rooms if r.name != room_name]
                        break
        else:
            QMessageBox.information(self, "Информация", "Выберите квартиру или комнату.")
            return

        self._refresh_tree()

    def _refresh_tree(self):
        self.tree.clear()

        if not self.building:
            return

        for apt in self.building.apartments:
            apt_item = QTreeWidgetItem([
                "Квартира",
                apt.name,
                f"{apt.total_area():.2f}",
                f"{apt.total_heating_power():.2f}",
                ""
            ])
            self.tree.addTopLevelItem(apt_item)

            for room in apt.rooms:
                room_item = QTreeWidgetItem([
                    "Комната",
                    room.name,
                    f"{room.area():.2f}",
                    f"{room.heating_power():.2f}",
                    f"{room.length}×{room.width}×{room.height} м; утепл.: {room.insulation}"
                ])
                apt_item.addChild(room_item)

            apt_item.setExpanded(True)

        # Итоги
        if self.building.apartments:
            self.result_label.setText(
                f"Общая площадь: {self.building.total_area():.2f} кв.м    |    "
                f"Требуемая тепловая мощность: {self.building.total_heating_power():.2f} кВт"
            )
        else:
            self.result_label.setText("Нет данных для расчёта")

    def _save_report(self):
        if not self.building or not self.building.apartments:
            QMessageBox.warning(self, "Внимание", "Нет данных для сохранения.")
            return
        try:
            ReportGenerator.save_to_word(self.building, "report.docx")
            QMessageBox.information(self, "Успех", "Отчёт сохранён в файл report.docx")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить отчёт: {e}")

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()