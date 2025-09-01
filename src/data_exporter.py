from pprint import pprint

# Эти импорты должны работать, так как data_exporter.py находится в той же
# директории 'src', что и другие модули.
from input_data_OptimizationWeights_types import InputData
from access_loader import load_data_from_access


def print_data_for_manual_creation(data: InputData):
    """Печатает загруженные данные в формате, готовом для копирования в Python-код."""
    print("\n" + "="*20 + " ДАННЫЕ ДЛЯ РУЧНОГО СОЗДАНИЯ InputData " + "="*20)
    print("# Скопируйте этот код в вашу функцию create_timetable_data() в rasp_data.py")
    print("-" * 80)

    print(f"days = {data.days}")
    print(f"periods = {data.periods}")
    print(f"classes = {data.classes}")
    print(f"subjects = {data.subjects}")
    print(f"teachers = {data.teachers}")
    print(f"split_subjects = {data.split_subjects!r}")  # !r для корректного вывода set
    print(f"subgroup_ids = {data.subgroup_ids}")

    print("\n# --- Учебные планы ---")
    print("plan_hours = \\")
    pprint(data.plan_hours)
    print("subgroup_plan_hours = \\")
    pprint(data.subgroup_plan_hours)

    print("\n# --- Закрепления учителей ---")
    print("assigned_teacher = \\")
    pprint(data.assigned_teacher)
    print("subgroup_assigned_teacher = \\")
    pprint(data.subgroup_assigned_teacher)

    print("\n# --- Ограничения ---")
    print("days_off = \\")
    pprint(data.days_off)
    print(f"forbidden_slots = {data.forbidden_slots!r}")

    print("\n# --- Мягкие цели ---")
    print("class_slot_weight = \\")
    pprint(data.class_slot_weight)
    print("teacher_slot_weight = \\")
    pprint(data.teacher_slot_weight)
    print("class_subject_day_weight = \\")
    pprint(data.class_subject_day_weight)

    print("\n# --- Совместимости ---")
    print(f"compatible_pairs = {data.compatible_pairs!r}")

    print("-" * 80)
    print("# Не забудьте в конце функции вернуть объект: return InputData(...)")


if __name__ == '__main__':
    # Путь к базе данных для запуска
    db_path_for_test = r"F:/_prg/python/OR-Tools-MILP/src/db/rasp3.accdb"

    print(f"--- Запускаем загрузку данных из {db_path_for_test} для экспорта ---")
    data_from_db = load_data_from_access(db_path_for_test)

    # Выводим данные в формате, готовом для копирования
    print_data_for_manual_creation(data_from_db)