import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTreeWidget, QTreeWidgetItem,
    QDialog, QDialogButtonBox, QComboBox, QRadioButton, QButtonGroup,
    QMessageBox, QInputDialog, QGroupBox
)

from room_calculator.models import Room, Apartment, Building
from room_calculator.report_generator import ReportGenerator


class NumericField(QWidget):
    def __init__(self, label_text, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        layout.addWidget(QLabel(label_text))
        self.entry = QLineEdit()
        self.entry.setPlaceholderText("Например: 3.5")
        layout.addWidget(self.entry)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: red; font-size: 10px;")
        self.error_label.setVisible(False)
        layout.addWidget(self.error_label)

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
        try:
            return float(text) > 0
        except ValueError:
            return False

    def value(self):
        return float(self.entry.text().strip())


class RoomDialog(QDialog):
    def __init__(self, building: Building, parent=None):
        super().__init__(parent)
        self.building = building
        self.setWindowTitle("Добавление комнаты")
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Квартира:"))
        self.apt_combo = QComboBox()
        self.apt_combo.addItems([apt.name for apt in building.apartments])
        layout.addWidget(self.apt_combo)

        layout.addWidget(QLabel("Название комнаты:"))
        self.name_entry = QLineEdit()
        self.name_entry.setPlaceholderText("Например: Спальня")
        layout.addWidget(self.name_entry)

        self.length_field = NumericField("Длина (м):")
        layout.addWidget(self.length_field)
        self.width_field = NumericField("Ширина (м):")
        layout.addWidget(self.width_field)
        self.height_field = NumericField("Высота (м):")
        layout.addWidget(self.height_field)

        layout.addWidget(QLabel("Уровень утепления:"))
        ins_layout = QHBoxLayout()
        self.ins_group = QButtonGroup(self)
        self.rb_low = QRadioButton("Низкий")
        self.rb_med = QRadioButton("Средний")
        self.rb_high = QRadioButton("Высокий")
        self.rb_med.setChecked(True)
        self.ins_group.addButton(self.rb_low)
        self.ins_group.addButton(self.rb_med)
        self.ins_group.addButton(self.rb_high)
        ins_layout.addWidget(self.rb_low)
        ins_layout.addWidget(self.rb_med)
        ins_layout.addWidget(self.rb_high)
        layout.addLayout(ins_layout)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.button(QDialogButtonBox.Ok).setText("Добавить")
        btn_box.button(QDialogButtonBox.Cancel).setText("Отмена")
        btn_box.accepted.connect(self._on_add)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def _on_add(self):
        if not self.name_entry.text().strip():
            QMessageBox.warning(self, "Ошибка", "Введите название комнаты.")
            return

        if not (self.length_field.is_valid()
                and self.width_field.is_valid()
                and self.height_field.is_valid()):
            QMessageBox.warning(self, "Ошибка", "Проверьте правильность размеров.")
            return

        if self.rb_low.isChecked():
            ins = "low"
        elif self.rb_high.isChecked():
            ins = "high"
        else:
            ins = "medium"

        # ВАЖНО: эта строка должна быть без лишних отступов (не внутри else)
        room = Room(
            self.name_entry.text().strip(),
            self.length_field.value(),
            self.width_field.value(),
            self.height_field.value(),
            ins
        )

        apt_name = self.apt_combo.currentText()
        for apt in self.building.apartments:
            if apt.name == apt_name:
                # Проверка на дубликат комнаты в этой квартире
                for existing_room in apt.rooms:
                    if existing_room.name == room.name:
                        QMessageBox.warning(self, "Ошибка", f"Комната с названием '{room.name}' уже существует в этой квартире!")
                        return
                
                apt.add_room(room)
                break

        self.accept()



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Калькулятор помещений (MVP)")
        self.resize(950, 650)

        self.building = None

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # --- Панель здания ---
        bld_box = QGroupBox("Здание")
        bld_layout = QHBoxLayout(bld_box)
        self.building_label = QLabel("Название здания: (не задано)")
        bld_layout.addWidget(self.building_label)
        bld_layout.addStretch()

        btn_rename = QPushButton("Изменить название")
        btn_rename.clicked.connect(self._ask_building_name)
        bld_layout.addWidget(btn_rename)
        layout.addWidget(bld_box)

        # --- Дерево структуры ---
        tree_box = QGroupBox("Структура: Квартиры и Комнаты")
        tree_layout = QVBoxLayout(tree_box)
        self.tree = QTreeWidget()
        self.tree.setColumnCount(5)
        self.tree.setHeaderLabels([
            "Уровень", "Название", "Площадь, кв.м",
            "Тепловая мощность, кВт", "Доп. параметры"
        ])
        self.tree.setColumnWidth(0, 100)
        self.tree.setColumnWidth(1, 180)
        self.tree.setColumnWidth(2, 120)
        self.tree.setColumnWidth(3, 170)
        self.tree.setColumnWidth(4, 250)
        tree_layout.addWidget(self.tree)
        layout.addWidget(tree_box)

        # --- Панель кнопок ---
        btn_layout = QHBoxLayout()

        btn_add_apt = QPushButton(" Добавить квартиру")
        btn_add_apt.clicked.connect(self._add_apartment)

        btn_add_room = QPushButton(" Добавить комнату")
        btn_add_room.clicked.connect(self._add_room)

        btn_delete = QPushButton("Удалить выбранное")
        btn_delete.clicked.connect(self._delete_selected)

        btn_refresh = QPushButton("Обновить расчёт")
        btn_refresh.clicked.connect(self._refresh_tree)

        # === КНОПКА СПРАВКИ ===
        btn_help = QPushButton("Справка")
        btn_help.setToolTip("Открыть руководство пользователя")
        btn_help.clicked.connect(self._show_help)

        btn_save = QPushButton("Сохранить отчёт в Word")
        btn_save.clicked.connect(self._save_report)

        btn_layout.addWidget(btn_add_apt)
        btn_layout.addWidget(btn_add_room)
        btn_layout.addWidget(btn_delete)
        btn_layout.addWidget(btn_refresh)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_help)   # Справка перед сохранением
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

        # --- Итоги ---
        result_box = QGroupBox("Итоги по зданию")
        result_layout = QVBoxLayout(result_box)
        self.result_label = QLabel("Нет данных")
        self.result_label.setStyleSheet("font-size: 13px; font-weight: bold;")
        result_layout.addWidget(self.result_label)
        layout.addWidget(result_box)

        # Запрос названия при старте
        self._ask_building_name()

    # ---------- Логика ----------
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
            name_clean = name.strip()
                
            # Проверка на дубликат
            for apt in self.building.apartments:
                if apt.name == name_clean:
                    QMessageBox.warning(self, "Ошибка", f"Квартира с названием '{name_clean}' уже существует!")
                    return
                
            self.building.add_apartment(Apartment(name_clean))
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
            self.building.apartments = [
                a for a in self.building.apartments if a.name != apt_name
            ]
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

        if self.building.apartments:
            self.result_label.setText(
                f"Общая площадь: {self.building.total_area():.2f} кв.м    |    "
                f"Требуемая тепловая мощность: {self.building.total_heating_power():.2f} кВт"
            )
        else:
            self.result_label.setText("Нет данных для расчёта")

    def _show_help(self):
        """Показывает окно справки с руководством пользователя."""
        help_text = (
            "<h2>Руководство пользователя</h2>"
            "<p><b>Калькулятор помещений (MVP)</b> — приложение для расчёта "
            "площади и тепловой мощности здания.</p>"

            "<h3>Порядок работы:</h3>"
            "<ol>"
            "<li><b>Задать здание:</b> при запуске введите название здания "
            "(или нажмите «Изменить название» в любой момент).</li>"
            "<li><b>Добавить квартиру:</b> нажмите кнопку « Добавить квартиру» "
            "и введите её номер или название.</li>"
            "<li><b>Добавить комнату:</b> выберите нужную квартиру в дереве слева, "
            "нажмите « Добавить комнату» и заполните форму.</li>"
            "<li><b>Ввод размеров:</b> в полях «Длина», «Ширина», «Высота» "
            "указываются только положительные числа (в метрах). "
            "При некорректном вводе под полем появляется красная подсказка.</li>"
            "<li><b>Утепление:</b> выберите уровень (низкий/средний/высокий). "
            "Он влияет на расчёт тепловой мощности.</li>"
            "<li><b>Удаление:</b> выберите объект в дереве и нажмите « Удалить выбранное».</li>"
            "<li><b>Сохранение:</b> нажмите « Сохранить отчёт в Word» — "
            "будет создан файл <code>report.docx</code>.</li>"
            "</ol>"

            "<h3>Формулы расчёта:</h3>"
            "<ul>"
            "<li>Площадь комнаты: <b>Длина × Ширина</b></li>"
            "<li>Тепловая мощность (базовая): <b>Площадь / 10</b> кВт</li>"
            "<li>Коэффициенты утепления: низкий ×1.5, средний ×1.0, высокий ×0.8</li>"
            "</ul>"

            "<p><i>Совет: для точных расчётов используйте реальные размеры помещений.</i></p>"
        )

        msg = QMessageBox(self)
        msg.setWindowTitle("Справка")
        msg.setTextFormat(Qt.RichText)
        msg.setText(help_text)
        msg.setIcon(QMessageBox.Information)
        msg.exec()

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