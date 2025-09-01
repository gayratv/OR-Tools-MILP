
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
    split_subjects = {'INFORMATIKA I IKT', 'INOSTRANNYY YaZYK', 'TEKhNOLOGIYa'}
    subgroup_ids = [1, 2]

    # --- Учебные планы ---
    plan_hours = {   ('5A', 'FIZIChESKAYa KULTURA'): 2.0,
    ('5A', 'GEOGRAFIYa'): 2.0,
    ('5A', 'ISTORIYa'): 2.0,
    ('5A', 'IZOBRAZITELNOE ISKUSSTVO'): 1.0,
    ('5A', 'LITERATURA'): 2.0,
    ('5A', 'MATEMATIKA'): 5.0,
    ('5A', 'MUZYKA'): 1.0,
    ('5A', 'OKRUZhAYuShchIY MIR'): 1.0,
    ('5A', 'RUSSKIY YaZYK/RODNOY YaZYK'): 6.0,
    ('5B', 'FIZIChESKAYa KULTURA'): 2.0,
    ('5B', 'GEOGRAFIYa'): 2.0,
    ('5B', 'ISTORIYa'): 2.0,
    ('5B', 'IZOBRAZITELNOE ISKUSSTVO'): 1.0,
    ('5B', 'LITERATURA'): 2.0,
    ('5B', 'MATEMATIKA'): 5.0,
    ('5B', 'MUZYKA'): 1.0,
    ('5B', 'OKRUZhAYuShchIY MIR'): 1.0,
    ('5B', 'RUSSKIY YaZYK/RODNOY YaZYK'): 6.0}
    subgroup_plan_hours = {   ('5A', 'INFORMATIKA I IKT', 1): 4.0,
    ('5A', 'INFORMATIKA I IKT', 2): 4.0,
    ('5A', 'INOSTRANNYY YaZYK', 1): 6.0,
    ('5A', 'INOSTRANNYY YaZYK', 2): 6.0,
    ('5A', 'TEKhNOLOGIYa', 1): 4.0,
    ('5A', 'TEKhNOLOGIYa', 2): 4.0,
    ('5B', 'INFORMATIKA I IKT', 1): 4.0,
    ('5B', 'INFORMATIKA I IKT', 2): 4.0,
    ('5B', 'INOSTRANNYY YaZYK', 1): 6.0,
    ('5B', 'INOSTRANNYY YaZYK', 2): 6.0,
    ('5B', 'TEKhNOLOGIYa', 1): 2.0,
    ('5B', 'TEKhNOLOGIYa', 2): 2.0}

    # --- Закрепления учителей ---
    assigned_teacher = {   ('5A', 'FIZIChESKAYa KULTURA'): 'ZOBNINA S.A.',
    ('5A', 'GEOGRAFIYa'): 'PLENKINA L.V.',
    ('5A', 'ISTORIYa'): 'SINYaVINA N.A.',
    ('5A', 'IZOBRAZITELNOE ISKUSSTVO'): 'ODEGOVA O.G.',
    ('5A', 'LITERATURA'): 'BISEROVA N.S.',
    ('5A', 'MATEMATIKA'): 'ShEROMOVA S.A.',
    ('5A', 'MUZYKA'): 'BATIShchEVA L.A.',
    ('5A', 'OKRUZhAYuShchIY MIR'): 'TOROPOVA I.V.',
    ('5A', 'RUSSKIY YaZYK/RODNOY YaZYK'): 'BISEROVA N.S.',
    ('5B', 'FIZIChESKAYa KULTURA'): 'ZOBNINA S.A.',
    ('5B', 'GEOGRAFIYa'): 'PLENKINA L.V.',
    ('5B', 'ISTORIYa'): 'SINYaVINA N.A.',
    ('5B', 'IZOBRAZITELNOE ISKUSSTVO'): 'ODEGOVA O.G.',
    ('5B', 'LITERATURA'): 'BISEROVA N.S.',
    ('5B', 'MATEMATIKA'): 'ShEROMOVA S.A.',
    ('5B', 'MUZYKA'): 'BATIShchEVA L.A.',
    ('5B', 'OKRUZhAYuShchIY MIR'): 'TOROPOVA I.V.',
    ('5B', 'RUSSKIY YaZYK/RODNOY YaZYK'): 'BISEROVA N.S.'}
    subgroup_assigned_teacher = {   ('5A', 'INFORMATIKA I IKT', 1): 'INFORMATIK1',
    ('5A', 'INFORMATIKA I IKT', 2): 'INFORMATIK1',
    ('5A', 'INOSTRANNYY YaZYK', 1): 'LUKINA S.G.',
    ('5A', 'INOSTRANNYY YaZYK', 2): 'REPNITsYNA N.V.',
    ('5A', 'TEKhNOLOGIYa', 1): 'TRUD2 DEVKI',
    ('5A', 'TEKhNOLOGIYa', 2): 'KROPOTOV S.G.',
    ('5B', 'INFORMATIKA I IKT', 1): 'INFORMATIK1',
    ('5B', 'INFORMATIKA I IKT', 2): 'INFORMATIK1',
    ('5B', 'INOSTRANNYY YaZYK', 1): 'LUKINA S.G.',
    ('5B', 'INOSTRANNYY YaZYK', 2): 'REPNITsYNA N.V.',
    ('5B', 'TEKhNOLOGIYa', 1): 'TRUD2 DEVKI',
    ('5B', 'TEKhNOLOGIYa', 2): 'KROPOTOV S.G.'}

    # --- Ограничения ---
    days_off = {'BISEROVA N.S.': {'Mon', 'Tue'}}
    forbidden_slots = {('5B', 'Mon', 1), ('5A', 'Mon', 1), ('5A', 'Thu', 2)}

    # --- Мягкие цели ---
    class_slot_weight = {('5A', 'Fri', 6): 5.0, ('5A', 'Fri', 7): 10.0}
    teacher_slot_weight = {('BOBROVA G.A.', 'Tue', 1): 8.0}
    class_subject_day_weight = {('5A', 'GEOGRAFIYa', 'Mon'): 6.0}

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
