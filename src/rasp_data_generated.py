
from input_data_OptimizationWeights_types import InputData

# ====================================================================
# Этот файл был сгенерирован автоматически скриптом generate_static_data_file.py
# Не редактируйте его вручную.
# ====================================================================

def create_timetable_data() -> InputData:
    """
    Создает объект InputData со статичными данными,
    сгенерированными из базы данных.
    """
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
    periods = [1, 2, 3, 4, 5, 6, 7, 8]
    classes = ['5A', '5B']
    subjects = ['RUSSKIY YaZYK/RODNOY YaZYK', 'LITERATURA', 'MATEMATIKA', 'FIZIKA', 'BIOLOGIYa', 'KhIMIYa', 'GEOGRAFIYa', 'OKRUZhAYuShchIY MIR', 'ALGEBRA', 'TEKhNOLOGIYa', 'ISKUSSTVO (MKhK)', 'ISTORIYa', 'INOSTRANNYY YaZYK', 'FIZIChESKAYa KULTURA', 'IZOBRAZITELNOE ISKUSSTVO', 'MUZYKA', 'ChERChENIE', 'OBShchESTVOZNANIE', 'OSNOVY BEZOPASNOSTI ZhIZNEDEYaTELNOSTI', 'PRIRODOVEDENIE', 'INFORMATIKA I IKT', 'GEOMETRIYa']
    teachers = ['BISEROVA N.S.', 'BOBROVA G.A.', 'LEDENTsOVA N.N.', 'NOVOSELOVA G.P.', 'KhARLAMOVA N.A.', 'BEKhTEREVA I.P.', 'ONUChINA G.N.', 'SKURIKhINA S.A.', 'PLENKINA L.V.', 'BALEZINA L.N.', 'ODEGOVA O.G.', 'REPNITsYNA N.V.', 'LUKINA S.G.', 'KRIVAL A.A.', 'SINYaVINA N.A.', 'KROPOTOV S.G.', 'OBUKhOVA K.V.', 'ZONOVA N.P.', 'BATIShchEVA L.A.', 'VYLEGZhANINA L.I.', 'TOROPOVA I.V.', 'MIKhEEVA O.N.', 'PERMINOV S.I.', 'ZOBNINA S.A.', 'BEKhTEREVA A.V.', 'ShEROMOVA S.A.', 'TRUD2 DEVKI', 'INFORMATIK1']
    split_subjects = {'INOSTRANNYY YaZYK', 'INFORMATIKA I IKT', 'TEKhNOLOGIYa'}
    subgroup_ids = [1, 2]

    # --- Учебные планы ---
    plan_hours = {   ('5A', 'FIZIChESKAYa KULTURA'): 2,
    ('5A', 'GEOGRAFIYa'): 2,
    ('5A', 'ISTORIYa'): 2,
    ('5A', 'IZOBRAZITELNOE ISKUSSTVO'): 1,
    ('5A', 'LITERATURA'): 2,
    ('5A', 'MATEMATIKA'): 5,
    ('5A', 'MUZYKA'): 1,
    ('5A', 'OKRUZhAYuShchIY MIR'): 1,
    ('5A', 'RUSSKIY YaZYK/RODNOY YaZYK'): 6,
    ('5B', 'FIZIChESKAYa KULTURA'): 2,
    ('5B', 'GEOGRAFIYa'): 2,
    ('5B', 'ISTORIYa'): 2,
    ('5B', 'IZOBRAZITELNOE ISKUSSTVO'): 1,
    ('5B', 'LITERATURA'): 2,
    ('5B', 'MATEMATIKA'): 5,
    ('5B', 'MUZYKA'): 1,
    ('5B', 'OKRUZhAYuShchIY MIR'): 1,
    ('5B', 'RUSSKIY YaZYK/RODNOY YaZYK'): 6}
    subgroup_plan_hours = {   ('5A', 'INFORMATIKA I IKT', 1): 4,
    ('5A', 'INFORMATIKA I IKT', 2): 4,
    ('5A', 'INOSTRANNYY YaZYK', 1): 6,
    ('5A', 'INOSTRANNYY YaZYK', 2): 6,
    ('5A', 'TEKhNOLOGIYa', 1): 4,
    ('5A', 'TEKhNOLOGIYa', 2): 4,
    ('5B', 'INFORMATIKA I IKT', 1): 4,
    ('5B', 'INFORMATIKA I IKT', 2): 4,
    ('5B', 'INOSTRANNYY YaZYK', 1): 6,
    ('5B', 'INOSTRANNYY YaZYK', 2): 6,
    ('5B', 'TEKhNOLOGIYa', 1): 2,
    ('5B', 'TEKhNOLOGIYa', 2): 2}

    # --- Закрепления учителей ---
    assigned_teacher = {   ('5A', 'FIZIChESKAYa KULTURA'): 0,
    ('5A', 'GEOGRAFIYa'): 0,
    ('5A', 'ISTORIYa'): 0,
    ('5A', 'IZOBRAZITELNOE ISKUSSTVO'): 0,
    ('5A', 'LITERATURA'): 0,
    ('5A', 'MATEMATIKA'): 0,
    ('5A', 'MUZYKA'): 0,
    ('5A', 'OKRUZhAYuShchIY MIR'): 0,
    ('5A', 'RUSSKIY YaZYK/RODNOY YaZYK'): 0,
    ('5B', 'FIZIChESKAYa KULTURA'): 0,
    ('5B', 'GEOGRAFIYa'): 0,
    ('5B', 'ISTORIYa'): 0,
    ('5B', 'IZOBRAZITELNOE ISKUSSTVO'): 0,
    ('5B', 'LITERATURA'): 0,
    ('5B', 'MATEMATIKA'): 0,
    ('5B', 'MUZYKA'): 0,
    ('5B', 'OKRUZhAYuShchIY MIR'): 0,
    ('5B', 'RUSSKIY YaZYK/RODNOY YaZYK'): 0}
    subgroup_assigned_teacher = {   ('5A', 'INFORMATIKA I IKT', 1): 0,
    ('5A', 'INFORMATIKA I IKT', 2): 0,
    ('5A', 'INOSTRANNYY YaZYK', 1): 0,
    ('5A', 'INOSTRANNYY YaZYK', 2): 0,
    ('5A', 'TEKhNOLOGIYa', 1): 0,
    ('5A', 'TEKhNOLOGIYa', 2): 0,
    ('5B', 'INFORMATIKA I IKT', 1): 0,
    ('5B', 'INFORMATIKA I IKT', 2): 0,
    ('5B', 'INOSTRANNYY YaZYK', 1): 0,
    ('5B', 'INOSTRANNYY YaZYK', 2): 0,
    ('5B', 'TEKhNOLOGIYa', 1): 0,
    ('5B', 'TEKhNOLOGIYa', 2): 0}

    # --- Ограничения ---
    days_off = {'SINYaVINA N.A.': {'Mon', 'Tue'}}
    forbidden_slots = {('5B', 'Mon', 1), ('5A', 'Mon', 1)}

    # --- Мягкие цели ---
    class_slot_weight = {('5A', 'Fri', 6): 5, ('5A', 'Fri', 7): 10}
    teacher_slot_weight = {('BOBROVA G.A.', 'Tue', 1): 8}
    class_subject_day_weight = {('5A', 'GEOGRAFIYa', 'Mon'): 6}

    # --- Совместимости ---
    compatible_pairs = {('INFORMATIKA I IKT', 'INOSTRANNYY YaZYK')}

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
        compatible_pairs=compatible_pairs
    )
