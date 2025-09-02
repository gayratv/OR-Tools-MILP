
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
    classes = ['5G', '5A', '5B', '5V']
    subjects = ['RUSSKIY_YaZYK_RODNOY_YaZYK', 'LITERATURA', 'MATEMATIKA', 'FIZIKA', 'BIOLOGIYa', 'KhIMIYa', 'GEOGRAFIYa', 'OKRUZhAYuShchIY_MIR', 'ALGEBRA', 'TEKhNOLOGIYa', 'ISKUSSTVO_MKhK_', 'ISTORIYa', 'INOSTRANNYY_YaZYK', 'FIZIChESKAYa_KULTURA', 'IZOBRAZITELNOE_ISKUSSTVO', 'MUZYKA', 'ChERChENIE', 'OBShchESTVOZNANIE', 'OSNOVY_BEZOPASNOSTI_ZhIZNEDEYaTELNOSTI', 'PRIRODOVEDENIE', 'INFORMATIKA_I_IKT', 'GEOMETRIYa', 'Probability_and_Statistics', 'School_Component', 'Spiritual_Local_History_of_the_Moscow_Region', 'Elective_Parameters', 'Individual_Project', 'Selected_Topics_in_Mathematics', 'Financial_Literacy_in_the_Digital_World', 'Political_Science', 'Elective_Russian_Language', 'Elective']
    teachers = ['Gasanova_A_Sh', 'Vacancy_2', 'Ulanova_O_V', 'Zhivoglotova_V_I', 'Belova_I_V', 'Kolganov_I_L', 'Solostovskaya_M_A', 'Loskutov_A_S', 'Vacancy_1', 'Odegova_O_G', 'Gostishcheva_E_O', 'Shamenskaya_V_E', 'Parunina_V_Yu', 'Osipova_E_M', 'Grigorovich_T_V', 'Obukhova_K_V', 'Badyukevich_M_V', 'Varennikova_S_G', 'Kuchkarova_E_N', 'Voronova_I_G', 'Perminov_S_I', 'Zueva_S_G', 'Gotseva_E_V', 'Sakharova_E_V', 'Cherkasova_L_N', 'Oderkova_D_V', 'Pysenkova_L_P', 'Radzivanovskaya_O_V', 'Putushkina_M_G', 'Stasyuk_E_V', 'Vacancy_IT', 'Mayorova_A_Yu', 'Kamyschnikova_O_V', 'Bulekov_A_S', 'Kamonina_S_I', 'Zueva_M', 'Vacancy_Physical_Education', 'Burlakov_N_S', 'Fillipov_D_M', 'Vacancy_Physics', 'Zaletskaya_D_I']
    split_subjects = {'INOSTRANNYY_YaZYK', 'TEKhNOLOGIYa', 'INFORMATIKA_I_IKT'}
    subgroup_ids = [1, 2]

    # --- Учебные планы ---
    plan_hours = {   ('5A', 'BIOLOGIYa'): 1,
    ('5A', 'FIZIChESKAYa_KULTURA'): 2,
    ('5A', 'GEOGRAFIYa'): 1,
    ('5A', 'ISTORIYa'): 3,
    ('5A', 'IZOBRAZITELNOE_ISKUSSTVO'): 1,
    ('5A', 'LITERATURA'): 3,
    ('5A', 'MATEMATIKA'): 6,
    ('5A', 'MUZYKA'): 1,
    ('5A', 'RUSSKIY_YaZYK_RODNOY_YaZYK'): 6,
    ('5B', 'BIOLOGIYa'): 1,
    ('5B', 'FIZIChESKAYa_KULTURA'): 2,
    ('5B', 'GEOGRAFIYa'): 1,
    ('5B', 'ISTORIYa'): 3,
    ('5B', 'IZOBRAZITELNOE_ISKUSSTVO'): 1,
    ('5B', 'LITERATURA'): 3,
    ('5B', 'MATEMATIKA'): 6,
    ('5B', 'MUZYKA'): 1,
    ('5B', 'RUSSKIY_YaZYK_RODNOY_YaZYK'): 6,
    ('5G', 'BIOLOGIYa'): 1,
    ('5G', 'FIZIChESKAYa_KULTURA'): 2,
    ('5G', 'GEOGRAFIYa'): 1,
    ('5G', 'ISTORIYa'): 3,
    ('5G', 'IZOBRAZITELNOE_ISKUSSTVO'): 1,
    ('5G', 'LITERATURA'): 3,
    ('5G', 'MATEMATIKA'): 6,
    ('5G', 'MUZYKA'): 1,
    ('5G', 'RUSSKIY_YaZYK_RODNOY_YaZYK'): 6,
    ('5V', 'BIOLOGIYa'): 1,
    ('5V', 'FIZIChESKAYa_KULTURA'): 2,
    ('5V', 'GEOGRAFIYa'): 1,
    ('5V', 'ISTORIYa'): 3,
    ('5V', 'IZOBRAZITELNOE_ISKUSSTVO'): 1,
    ('5V', 'LITERATURA'): 3,
    ('5V', 'MATEMATIKA'): 6,
    ('5V', 'MUZYKA'): 1,
    ('5V', 'RUSSKIY_YaZYK_RODNOY_YaZYK'): 6}
    subgroup_plan_hours = {   ('5A', 'INOSTRANNYY_YaZYK', 1): 3,
    ('5A', 'INOSTRANNYY_YaZYK', 2): 3,
    ('5A', 'TEKhNOLOGIYa', 1): 2,
    ('5A', 'TEKhNOLOGIYa', 2): 2,
    ('5B', 'INOSTRANNYY_YaZYK', 1): 3,
    ('5B', 'INOSTRANNYY_YaZYK', 2): 3,
    ('5B', 'TEKhNOLOGIYa', 1): 2,
    ('5B', 'TEKhNOLOGIYa', 2): 2,
    ('5G', 'INOSTRANNYY_YaZYK', 1): 3,
    ('5G', 'INOSTRANNYY_YaZYK', 2): 3,
    ('5G', 'TEKhNOLOGIYa', 1): 2,
    ('5G', 'TEKhNOLOGIYa', 2): 2,
    ('5V', 'INOSTRANNYY_YaZYK', 1): 3,
    ('5V', 'INOSTRANNYY_YaZYK', 2): 3,
    ('5V', 'TEKhNOLOGIYa', 1): 2,
    ('5V', 'TEKhNOLOGIYa', 2): 2}

    # --- Закрепления учителей ---
    assigned_teacher = {   ('5A', 'BIOLOGIYa'): 'Voronova_I_G',
    ('5A', 'FIZIChESKAYa_KULTURA'): 'Vacancy_Physical_Education',
    ('5A', 'GEOGRAFIYa'): 'Sakharova_E_V',
    ('5A', 'ISTORIYa'): 'Osipova_E_M',
    ('5A', 'IZOBRAZITELNOE_ISKUSSTVO'): 'Kamonina_S_I',
    ('5A', 'LITERATURA'): 'Belova_I_V',
    ('5A', 'MATEMATIKA'): 'Putushkina_M_G',
    ('5A', 'MUZYKA'): 'Gasanova_A_Sh',
    ('5A', 'RUSSKIY_YaZYK_RODNOY_YaZYK'): 'Belova_I_V',
    ('5B', 'BIOLOGIYa'): 'Voronova_I_G',
    ('5B', 'FIZIChESKAYa_KULTURA'): 'Vacancy_Physical_Education',
    ('5B', 'GEOGRAFIYa'): 'Sakharova_E_V',
    ('5B', 'ISTORIYa'): 'Osipova_E_M',
    ('5B', 'IZOBRAZITELNOE_ISKUSSTVO'): 'Kamonina_S_I',
    ('5B', 'LITERATURA'): 'Vacancy_2',
    ('5B', 'MATEMATIKA'): 'Zaletskaya_D_I',
    ('5B', 'MUZYKA'): 'Gasanova_A_Sh',
    ('5B', 'RUSSKIY_YaZYK_RODNOY_YaZYK'): 'Vacancy_2',
    ('5G', 'BIOLOGIYa'): 'Voronova_I_G',
    ('5G', 'FIZIChESKAYa_KULTURA'): 'Burlakov_N_S',
    ('5G', 'GEOGRAFIYa'): 'Sakharova_E_V',
    ('5G', 'ISTORIYa'): 'Stasyuk_E_V',
    ('5G', 'IZOBRAZITELNOE_ISKUSSTVO'): 'Kamonina_S_I',
    ('5G', 'LITERATURA'): 'Vacancy_2',
    ('5G', 'MATEMATIKA'): 'Grigorovich_T_V',
    ('5G', 'MUZYKA'): 'Gasanova_A_Sh',
    ('5G', 'RUSSKIY_YaZYK_RODNOY_YaZYK'): 'Vacancy_2',
    ('5V', 'BIOLOGIYa'): 'Voronova_I_G',
    ('5V', 'FIZIChESKAYa_KULTURA'): 'Burlakov_N_S',
    ('5V', 'GEOGRAFIYa'): 'Sakharova_E_V',
    ('5V', 'ISTORIYa'): 'Stasyuk_E_V',
    ('5V', 'IZOBRAZITELNOE_ISKUSSTVO'): 'Kamonina_S_I',
    ('5V', 'LITERATURA'): 'Vacancy_1',
    ('5V', 'MATEMATIKA'): 'Zaletskaya_D_I',
    ('5V', 'MUZYKA'): 'Gasanova_A_Sh',
    ('5V', 'RUSSKIY_YaZYK_RODNOY_YaZYK'): 'Vacancy_1'}
    subgroup_assigned_teacher = {   ('5A', 'INOSTRANNYY_YaZYK', 1): 'Gotseva_E_V',
    ('5A', 'INOSTRANNYY_YaZYK', 2): 'Mayorova_A_Yu',
    ('5A', 'TEKhNOLOGIYa', 1): 'Grigorovich_T_V',
    ('5A', 'TEKhNOLOGIYa', 2): 'Kamyschnikova_O_V',
    ('5B', 'INOSTRANNYY_YaZYK', 1): 'Gotseva_E_V',
    ('5B', 'INOSTRANNYY_YaZYK', 2): 'Shamenskaya_V_E',
    ('5B', 'TEKhNOLOGIYa', 1): 'Grigorovich_T_V',
    ('5B', 'TEKhNOLOGIYa', 2): 'Kamyschnikova_O_V',
    ('5G', 'INOSTRANNYY_YaZYK', 1): 'Zhivoglotova_V_I',
    ('5G', 'INOSTRANNYY_YaZYK', 2): 'Shamenskaya_V_E',
    ('5G', 'TEKhNOLOGIYa', 1): 'Grigorovich_T_V',
    ('5G', 'TEKhNOLOGIYa', 2): 'Kamyschnikova_O_V',
    ('5V', 'INOSTRANNYY_YaZYK', 1): 'Shamenskaya_V_E',
    ('5V', 'INOSTRANNYY_YaZYK', 2): 'Zhivoglotova_V_I',
    ('5V', 'TEKhNOLOGIYa', 1): 'Grigorovich_T_V',
    ('5V', 'TEKhNOLOGIYa', 2): 'Kamyschnikova_O_V'}

    # --- Ограничения ---
    days_off = {'Osipova_E_M': {'Mon', 'Tue'}}
    forbidden_slots = {('5A', 'Mon', 1), ('5B', 'Mon', 1)}

    # --- Мягкие цели ---
    class_slot_weight = {('5A', 'Fri', 6): 5, ('5A', 'Fri', 7): 10}
    teacher_slot_weight = {('Vacancy_2', 'Tue', 1): 8}
    class_subject_day_weight = {('5A', 'GEOGRAFIYa', 'Mon'): 6}

    # --- Совместимости ---
    compatible_pairs = {('INFORMATIKA_I_IKT', 'INOSTRANNYY_YaZYK')}

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
