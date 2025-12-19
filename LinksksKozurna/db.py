# Бібліотека для табличок SQLite
import sqlite3

# Сам path(шлях) до файлу дб(бази даних ор дата бейс)
db_file = "school_journal.db"

# Підключення до SQLite
conn = sqlite3.connect(db_file)
conn.execute("PRAGMA foreign_keys = ON;")  # Включаємо підтримку 
    # foreign key(зовнішніх ключів для звязків між таблицями)
cursor = conn.cursor()

# Тут якраз створення таблиць

cursor.execute("""
CREATE TABLE IF NOT EXISTS Students (
    StudentID INTEGER PRIMARY KEY AUTOINCREMENT,
    FirstName TEXT CHECK(length(FirstName) <= 50),
    LastName TEXT CHECK(length(LastName) <= 50),
    Class TEXT CHECK(length(Class) <= 10)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS Teachers (
    TeacherID INTEGER PRIMARY KEY AUTOINCREMENT,
    FirstName TEXT CHECK(length(FirstName) <= 50),
    LastName TEXT CHECK(length(LastName) <= 50),
    Subject TEXT CHECK(length(Subject) <= 50)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS Subjects (
    SubjectID INTEGER PRIMARY KEY AUTOINCREMENT,
    Name TEXT CHECK(length(Name) <= 50)
)
""")

cursor.execute("""
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

cursor.execute("""
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
cursor.executemany(
    "INSERT INTO Students (FirstName, LastName, Class) VALUES (?, ?, ?)",
    students
)

# Те саме, тільки з вчителями
teachers = [
    ("Ірина", "Савчук", "Математика"),
    ("Олег", "Романюк", "Історія"),
    ("Наталія", "Бондар", "Українська мова")
]
cursor.executemany(
    "INSERT INTO Teachers (FirstName, LastName, Subject) VALUES (?, ?, ?)",
    teachers
)

# Предмети, зе сейм(польський оф корс)
subjects = [
    ("Математика",),
    ("Історія",),
    ("Українська мова",)
]
cursor.executemany(
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
cursor.executemany(
    "INSERT INTO Grades (StudentID, SubjectID, TeacherID, Grade, DateGiven) VALUES (?, ?, ?, ?, ?)",
    grades
)

# Пропуски, да да, все ж та сама схема
absences = [
    (1, 1, "2025-02-05", 1),
    (3, 2, "2025-02-06", 0)
]
cursor.executemany(
    "INSERT INTO Absences (StudentID, SubjectID, DateAbsent, IsExcused) VALUES (?, ?, ?, ?)",
    absences
)

# Шоб понять що все спрацювало
print("School journal database created successfully!")

# ---------------- ВИВІД ДАНИХ ----------------
# Ну а тепер нанчинаєця... Імітація аксес зв'язків на практиці

print("\n=== УСПІШНІСТЬ УЧНІВ ===")

# Откриваємо табличку і шукаєм усе повязане з учнями
cursor.execute("""
SELECT 
    Students.FirstName,
    Students.LastName,
    Students.Class,
    Subjects.Name,
    Grades.Grade,
    Grades.DateGiven
FROM Grades
JOIN Students ON Grades.StudentID = Students.StudentID
JOIN Subjects ON Grades.SubjectID = Subjects.SubjectID
ORDER BY Students.StudentID
""")

rows = cursor.fetchall()

# Цикл для виводу кожного учнівського рядочка
for row in rows:
    print(f"Учень: {row[0]} {row[1]} ({row[2]}) | Предмет: {row[3]} | Оцінка: {row[4]} | Дата: {row[5]}")

# Як прошле, тільки тепер про прогули
print("\n=== ПРОПУСКИ УЧНІВ ===")

cursor.execute("""
SELECT
    Students.FirstName,
    Students.LastName,
    Subjects.Name,
    Absences.DateAbsent,
    Absences.IsExcused
FROM Absences
JOIN Students ON Absences.StudentID = Students.StudentID
JOIN Subjects ON Absences.SubjectID = Subjects.SubjectID
""")

rows = cursor.fetchall()

for row in rows:
    status = "Поважна" if row[4] == 1 else "Без поважної"
    print(f"Учень: {row[0]} {row[1]} | Предмет: {row[2]} | Дата: {row[3]} | Причина: {status}")

# Знов, тільки тепер табличка з вчителями і їх предметами
print("\n=== ВЧИТЕЛІ ТА ЇХ ПРЕДМЕТИ ===")

cursor.execute("""
SELECT
    FirstName,
    LastName,
    Subject
FROM Teachers
""")

rows = cursor.fetchall()

for row in rows:
    print(f"Вчитель: {row[0]} {row[1]} | Предмет: {row[2]}")

print("\n=== ХТО КОМУ СТАВИВ ОЦІНКИ ===")

cursor.execute("""
SELECT
    Teachers.FirstName,
    Teachers.LastName,
    Students.FirstName,
    Students.LastName,
    Subjects.Name,
    Grades.Grade
FROM Grades
JOIN Teachers ON Grades.TeacherID = Teachers.TeacherID
JOIN Students ON Grades.StudentID = Students.StudentID
JOIN Subjects ON Grades.SubjectID = Subjects.SubjectID
""")

rows = cursor.fetchall()

for row in rows:
    print(f"{row[0]} {row[1]} → {row[2]} {row[3]} | {row[4]} | {row[5]}")

# Закриття зєднання, все колись мусить закінчитись
cursor.close()
conn.commit()
conn.close()
