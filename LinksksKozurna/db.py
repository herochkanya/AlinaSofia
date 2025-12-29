# PySide6 — бібліотека для віконець, кнопочок і всього красивого
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QScrollArea, QTextEdit
)
from PySide6.QtCore import Qt
import sqlite3
import sys
import os


def resource_path(relative_path):
    # Якщо ми в exe — PyInstaller сховав файли тут
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    # Якщо запускаємось як звичайний .py
    return os.path.join(os.path.abspath("."), relative_path)

# Маленький клас — вся програма в одному місці, без цирку
class SchoolJournalApp(QWidget):
    def __init__(self):
        super().__init__()

        # Підключення до бази, спокійно і без фанфар
        db_path = resource_path("school_journal.db")
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self.cursor = self.conn.cursor()

        # Стек для кнопки "Назад", типу памʼять куди ми ходили
        self.history = []

        self.init_ui()
        self.show_main_menu()

        # Чистим таблиці, шоб не клонувалось
        self.cursor.execute("DELETE FROM Grades")
        self.cursor.execute("DELETE FROM Absences")
        self.cursor.execute("DELETE FROM Students")
        self.cursor.execute("DELETE FROM Teachers")
        self.cursor.execute("DELETE FROM Subjects")

        # Обнуляєм лічильники айді, шоб не було приколів
        self.cursor.execute("DELETE FROM sqlite_sequence")

        # Тут якраз створення таблиць

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS Students (
            StudentID INTEGER PRIMARY KEY AUTOINCREMENT,
            FirstName TEXT CHECK(length(FirstName) <= 50),
            LastName TEXT CHECK(length(LastName) <= 50),
            Class TEXT CHECK(length(Class) <= 10)
        )
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS Teachers (
            TeacherID INTEGER PRIMARY KEY AUTOINCREMENT,
            FirstName TEXT CHECK(length(FirstName) <= 50),
            LastName TEXT CHECK(length(LastName) <= 50),
            Subject TEXT CHECK(length(Subject) <= 50)
        )
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS Subjects (
            SubjectID INTEGER PRIMARY KEY AUTOINCREMENT,
            Name TEXT CHECK(length(Name) <= 50)
        )
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS Grades (
            GradeID INTEGER PRIMARY KEY AUTOINCREMENT,
            StudentID INTEGER,
            SubjectID INTEGER,
            TeacherID INTEGER,
            Grade INTEGER CHECK(Grade BETWEEN 1 AND 12),
            DateGiven TEXT,
            FOREIGN KEY (StudentID) REFERENCES Students(StudentID),
            FOREIGN KEY (SubjectID) REFERENCES Subjects(SubjectID),
            FOREIGN KEY (TeacherID) REFERENCES Teachers(TeacherID)
        )
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS Absences (
            AbsenceID INTEGER PRIMARY KEY AUTOINCREMENT,
            StudentID INTEGER,
            SubjectID INTEGER,
            DateAbsent TEXT,
            IsExcused INTEGER CHECK(IsExcused IN (0,1)),
            FOREIGN KEY (StudentID) REFERENCES Students(StudentID),
            FOREIGN KEY (SubjectID) REFERENCES Subjects(SubjectID)
        )
        """)

        # Це не обовязково, просто для прикладу(зверху вже вся таблиця зроблена)
        # (тільки не забуть прописать для conn і cursor .close() в кінці)
        # Неактуально, вже вони прописані, так шо пофіг

        # Ну це учні, спершу список -- потім вставка
        students = [
            ("Олександр", "Ковальчук", "10-А"),
            ("Марія", "Петренко", "10-А"),
            ("Андрій", "Мельник", "9-Б"),
            ("Софія", "Іваненко", "9-Б")
        ]
        self.cursor.executemany(
            "INSERT INTO Students (FirstName, LastName, Class) VALUES (?, ?, ?)",
            students
        )

        # Те саме, тільки з вчителями
        teachers = [
            ("Ірина", "Савчук", "Математика"),
            ("Олег", "Романюк", "Історія"),
            ("Наталія", "Бондар", "Українська мова")
        ]
        self.cursor.executemany(
            "INSERT INTO Teachers (FirstName, LastName, Subject) VALUES (?, ?, ?)",
            teachers
        )

        # Предмети, зе сейм(польський оф корс)
        subjects = [
            ("Математика",),
            ("Історія",),
            ("Українська мова",)
        ]
        self.cursor.executemany(
            "INSERT INTO Subjects (Name) VALUES (?)",
            subjects
        )

        # Оцінки, лень повторять
        grades = [
            (1, 1, 1, 10, "2025-02-10"),
            (2, 1, 1, 12, "2025-02-10"),
            (3, 2, 2, 9, "2025-02-11"),
            (4, 3, 3, 11, "2025-02-12")
        ]
        self.cursor.executemany(
            "INSERT INTO Grades (StudentID, SubjectID, TeacherID, Grade, DateGiven) VALUES (?, ?, ?, ?, ?)",
            grades
        )

        # Пропуски, да да, все ж та сама схема
        absences = [
            (1, 1, "2025-02-05", 1),
            (3, 2, "2025-02-06", 0)
        ]
        self.cursor.executemany(
            "INSERT INTO Absences (StudentID, SubjectID, DateAbsent, IsExcused) VALUES (?, ?, ?, ?)",
            absences
        )

        # Шоб понять що все спрацювало
        print("School journal database created successfully!")

    def init_ui(self):
        self.setWindowTitle("Ступницька Козиренко")
        self.resize(600, 500)

        main_layout = QVBoxLayout(self)

        # Верхня панель: кнопка назад + заголовок
        top_layout = QHBoxLayout()

        self.back_button = QPushButton("← Назад")
        self.back_button.clicked.connect(self.go_back)
        self.back_button.setEnabled(False)
        top_layout.addWidget(self.back_button, alignment=Qt.AlignLeft)

        self.title_label = QLabel("Ступницька Козиренко")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        top_layout.addWidget(self.title_label)

        top_layout.addStretch()
        main_layout.addLayout(top_layout)

        # Текст над списком — підказка, що від нас хочуть
        self.info_label = QLabel("")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("font-size: 14px;")
        main_layout.addWidget(self.info_label)

        # Скрол для кнопок (щоб не розлазилось)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.list_widget = QWidget()
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.addStretch()

        self.scroll_area.setWidget(self.list_widget)
        main_layout.addWidget(self.scroll_area, stretch=2)

        # Нижня текстова панель — тут вся мудрість світу
        self.text_panel = QTextEdit()
        self.text_panel.setReadOnly(True)
        self.text_panel.setPlaceholderText("Тут зʼявиться інформація ✨")
        main_layout.addWidget(self.text_panel, stretch=1)

    # Чистим список кнопок, бо ми не фанати хаосу
    def clear_list(self):
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    # Головне меню: Учні / Вчителі
    def show_main_menu(self):
        self.history.clear()
        self.back_button.setEnabled(False)

        self.clear_list()
        self.text_panel.clear()
        self.info_label.setText("Виберіть, кого хочете глянути")

        self.add_button("Учні", self.show_students)
        self.add_button("Вчителі", self.show_teachers)

    # Додає кнопку в список, акуратно
    def add_button(self, text, callback):
        btn = QPushButton(text)
        btn.clicked.connect(callback)
        self.list_layout.insertWidget(self.list_layout.count() - 1, btn)

    # Кнопка назад — повертаємось на крок
    def go_back(self):
        if self.history:
            last = self.history.pop()
            last()
        self.back_button.setEnabled(bool(self.history))

    # ---------------- УЧНІ ----------------

    def show_students(self):
        self.history.append(self.show_main_menu)
        self.back_button.setEnabled(True)

        self.clear_list()
        self.text_panel.clear()
        self.info_label.setText("Виберіть учня")

        self.cursor.execute(
            "SELECT StudentID, FirstName, LastName FROM Students"
        )
        for sid, fn, ln in self.cursor.fetchall():
            self.add_button(
                f"{fn} {ln}",
                lambda _, s=sid: self.show_student_details(s)
            )

    def show_student_details(self, student_id):
        self.history.append(self.show_students)
        self.back_button.setEnabled(True)

        self.clear_list()
        self.text_panel.clear()

        # Імʼя учня
        self.cursor.execute(
            "SELECT FirstName, LastName, Class FROM Students WHERE StudentID = ?",
            (student_id,)
        )
        fn, ln, cl = self.cursor.fetchone()
        self.info_label.setText(f"{fn} {ln} ({cl})")

        text = "=== УСПІШНІСТЬ ===\n"

        self.cursor.execute("""
        SELECT Subjects.Name, Grades.Grade, Grades.DateGiven,
               Teachers.FirstName, Teachers.LastName
        FROM Grades
        JOIN Subjects ON Grades.SubjectID = Subjects.SubjectID
        JOIN Teachers ON Grades.TeacherID = Teachers.TeacherID
        WHERE Grades.StudentID = ?
        """, (student_id,))

        rows = self.cursor.fetchall()
        if rows:
            for subj, grade, date, tfn, tln in rows:
                text += f"{subj}: {grade} ({date}) — {tfn} {tln}\n"
        else:
            text += "Нема оцінок. Життя попереду.\n"

        text += "\n=== ПРОПУСКИ ===\n"

        self.cursor.execute("""
        SELECT Subjects.Name, DateAbsent, IsExcused
        FROM Absences
        JOIN Subjects ON Absences.SubjectID = Subjects.SubjectID
        WHERE StudentID = ?
        """, (student_id,))

        rows = self.cursor.fetchall()
        if rows:
            for subj, date, exc in rows:
                reason = "Поважна" if exc else "Без поважної"
                text += f"{subj}: {date} — {reason}\n"
        else:
            text += "Прогулів нема, чемна людина.\n"

        self.text_panel.setText(text)

    # ---------------- ВЧИТЕЛІ ----------------

    def show_teachers(self):
        self.history.append(self.show_main_menu)
        self.back_button.setEnabled(True)

        self.clear_list()
        self.text_panel.clear()
        self.info_label.setText("Виберіть вчителя")

        self.cursor.execute(
            "SELECT TeacherID, FirstName, LastName FROM Teachers"
        )
        for tid, fn, ln in self.cursor.fetchall():
            self.add_button(
                f"{fn} {ln}",
                lambda _, t=tid: self.show_teacher_details(t)
            )

    def show_teacher_details(self, teacher_id):
        self.history.append(self.show_teachers)
        self.back_button.setEnabled(True)

        self.clear_list()
        self.text_panel.clear()

        self.cursor.execute(
            "SELECT FirstName, LastName, Subject FROM Teachers WHERE TeacherID = ?",
            (teacher_id,)
        )
        fn, ln, subj = self.cursor.fetchone()
        self.info_label.setText(f"{fn} {ln}")

        text = f"Предмет: {subj}\n\n=== ОЦІНКИ, ЯКІ СТАВИВ(ЛА) ===\n"

        self.cursor.execute("""
        SELECT Students.FirstName, Students.LastName,
               Subjects.Name, Grades.Grade, Grades.DateGiven
        FROM Grades
        JOIN Students ON Grades.StudentID = Students.StudentID
        JOIN Subjects ON Grades.SubjectID = Subjects.SubjectID
        WHERE Grades.TeacherID = ?
        """, (teacher_id,))

        rows = self.cursor.fetchall()
        if rows:
            for sfn, sln, subj, grade, date in rows:
                text += f"{sfn} {sln} — {subj}: {grade} ({date})\n"
        else:
            text += "Оцінок поки нема. Мирний вчитель.\n"

        self.text_panel.setText(text)


# Запуск програми — без цього нічого не станеться
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SchoolJournalApp()
    window.show()
    sys.exit(app.exec())
