import pprint
import os

# Эти импорты должны работать, так как скрипт находится в директории 'src'
from input_data import InputData
from access_loader import load_data_from_access


def generate_function_string(data: InputData) -> str:
    """
    Генерирует строку, содержащую полный Python-код для функции
    create_timetable_data(), заполненной данными из объекта InputData.
    """
    # Используем pformat для красивого форматирования сложных объектов в строку
    plan_hours_str = pprint.pformat(data.plan_hours, indent=4, width=120)
    subgroup_plan_hours_str = pprint.pformat(data.subgroup_plan_hours, indent=4, width=120)
    assigned_teacher_str = pprint.pformat(data.assigned_teacher, indent=4, width=120)
    subgroup_assigned_teacher_str = pprint.pformat(data.subgroup_assigned_teacher, indent=4, width=120)
    days_off_str = pprint.pformat(data.days_off, indent=4, width=120)
    class_slot_weight_str = pprint.pformat(data.class_slot_weight, indent=4, width=120)
    teacher_slot_weight_str = pprint.pformat(data.teacher_slot_weight, indent=4, width=120)
    class_subject_day_weight_str = pprint.pformat(data.class_subject_day_weight, indent=4, width=120)
    forbidden_slots_str = pprint.pformat(data.forbidden_slots, indent=4, width=120)
    split_subjects_str = pprint.pformat(data.split_subjects, indent=4, width=120)
    compatible_pairs_str = pprint.pformat(data.compatible_pairs, indent=4, width=120)
    paired_subjects_str = pprint.pformat(data.paired_subjects, indent=4, width=120)
    # Новые поля
    grade_max_lessons_per_day_str = pprint.pformat(data.grade_max_lessons_per_day, indent=4, width=120)
    teacher_forbidden_slots_str = pprint.pformat(data.teacher_forbidden_slots, indent=4, width=120)
    subjects_not_last_lesson_str = pprint.pformat(data.subjects_not_last_lesson, indent=4, width=120)
    elementary_english_periods_str = pprint.pformat(data.elementary_english_periods, indent=4, width=120)
    grade_subject_max_consecutive_days_str = pprint.pformat(data.grade_subject_max_consecutive_days, indent=4, width=120)
    must_sync_split_subjects_str = pprint.pformat(data.must_sync_split_subjects, indent=4, width=120)
    display_subject_names_str = pprint.pformat(data.display_subject_names, indent=4, width=120)
    display_teacher_names_str = pprint.pformat(data.display_teacher_names, indent=4, width=120)

    # Собираем итоговый код функции в виде многострочной f-строки
    function_code = f"""
from input_data import InputData, ClassInfo

# ====================================================================
# Этот файл был сгенерирован автоматически скриптом generate_static_data_file.py
# Не редактируйте его вручную.
# ====================================================================

def create_timetable_data() -> InputData:
    \"\"\"
    Создает объект InputData со статичными данными,
    сгенерированными из базы данных.
    \"\"\"
    days = {data.days}
    periods = {data.periods}
    classes = {data.classes}
    subjects = {data.subjects}
    teachers = {data.teachers}
    split_subjects = {split_subjects_str}
    subgroup_ids = {data.subgroup_ids}

    # --- Учебные планы ---
    plan_hours = {plan_hours_str}
    subgroup_plan_hours = {subgroup_plan_hours_str}

    # --- Закрепления учителей ---
    assigned_teacher = {assigned_teacher_str}
    subgroup_assigned_teacher = {subgroup_assigned_teacher_str}

    # --- Ограничения ---
    days_off = {days_off_str}
    forbidden_slots = {forbidden_slots_str}

    # --- Мягкие цели ---
    class_slot_weight = {class_slot_weight_str}
    teacher_slot_weight = {teacher_slot_weight_str}
    class_subject_day_weight = {class_subject_day_weight_str}

    # --- Совместимости ---
    compatible_pairs = {compatible_pairs_str}

    # --- Спаривание ---
    paired_subjects = {paired_subjects_str}

    # --- Дополнительные политики ---
    english_subject_name = "{data.english_subject_name}"
    teacher_forbidden_slots = {teacher_forbidden_slots_str}
    grade_max_lessons_per_day = {grade_max_lessons_per_day_str}
    subjects_not_last_lesson = {subjects_not_last_lesson_str}
    elementary_english_periods = {elementary_english_periods_str}
    grade_subject_max_consecutive_days = {grade_subject_max_consecutive_days_str}
    must_sync_split_subjects = {must_sync_split_subjects_str}

    # --- Словари для отображения ---
    display_subject_names = {display_subject_names_str}
    display_teacher_names = {display_teacher_names_str}

    return InputData(
        days=days,
        periods=periods,
        classes=classes,
        subjects=subjects,
        teachers=teachers,
        split_subjects=split_subjects,
        subgroup_ids=subgroup_ids,
        plan_hours=plan_hours,
        subgroup_plan_hours=subgroup_plan_hours,
        assigned_teacher=assigned_teacher,
        subgroup_assigned_teacher=subgroup_assigned_teacher,
        days_off=days_off,
        forbidden_slots=forbidden_slots,
        class_slot_weight=class_slot_weight,
        teacher_slot_weight=teacher_slot_weight,
        class_subject_day_weight=class_subject_day_weight,
        compatible_pairs=compatible_pairs,
        paired_subjects=paired_subjects,
        english_subject_name=english_subject_name,
        teacher_forbidden_slots=teacher_forbidden_slots,
        grade_max_lessons_per_day=grade_max_lessons_per_day,
        subjects_not_last_lesson=subjects_not_last_lesson,
        elementary_english_periods=elementary_english_periods,
        grade_subject_max_consecutive_days=grade_subject_max_consecutive_days,
        must_sync_split_subjects=must_sync_split_subjects,
        display_subject_names=display_subject_names,
        display_teacher_names=display_teacher_names
    )
"""
    return function_code


if __name__ == '__main__':
    # Определяем пути
    project_root = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(project_root, 'db', 'rasp3-new-calculation.accdb')
    output_file_path = os.path.join(project_root, 'rasp_data_generated.py')

    # 1. Загружаем данные из Access
    print(f"--- Загружаем данные из {db_path} ---")
    data_from_db = load_data_from_access(db_path)
    print("Данные успешно загружены.")

    # 2. Генерируем код функции в виде строки
    print("--- Генерируем код функции create_timetable_data() ---")
    function_code_string = generate_function_string(data_from_db)
    print("Код успешно сгенерирован.")

    # 3. Сохраняем сгенерированный код в файл
    try:
        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write(function_code_string)
        print(f"\\n[УСПЕХ] Функция create_timetable_data() сохранена в файл:\\n{output_file_path}")
    except Exception as e:
        print(f"\\n[ОШИБКА] Не удалось сохранить файл: {e}")