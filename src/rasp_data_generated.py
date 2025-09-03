
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
    subjects = ['Rus', 'Lit', 'Math', 'Phys', 'Bio', 'Chem', 'Geog', 'Env', 'Alg', 'Trud', 'Art', 'Hist', 'Eng', 'PE', 'VisArt', 'Mus', 'Draw', 'Soc', 'Safe', 'NatSci', 'СЫ', 'Geom', 'Stat', 'SchComp', 'Relig', 'El', 'Proj', 'MathAdv', 'Fin', 'Pol', 'ElRu', 'El']
    teachers = ['Gas_ASh', 'Vac_2', 'Ula_OV', 'Zhi_VI', 'Bel_IV', 'Kol_IL', 'Sol_MA', 'Los_AS', 'Vac_1', 'Ode_OG', 'Gos_EO', 'Sha_VE', 'Par_VYu', 'Osi_EM', 'Gri_TV', 'Obu_KV', 'Bad_MV', 'Var_SG', 'Kuk_EN', 'Vor_IG', 'Per_SI', 'Zue_SG', 'Got_EV', 'Sak_EV', 'Che_LN', 'Ode_DV', 'Pys_LP', 'Rad_OV', 'Put_MG', 'Sta_EV', 'Vac_IT', 'May_AYu', 'Kam_OV', 'Bul_AS', 'Kam_SI', 'Zue_M', 'Vac_fizra', 'Bur_NS', 'Fil_DM', 'Vac_Physics', 'Zal_DI']
    split_subjects = {'Trud', 'Eng', 'СЫ'}
    subgroup_ids = [1, 2]

    # --- Учебные планы ---
    plan_hours = {   ('5A', 'Bio'): 1,
    ('5A', 'Geog'): 1,
    ('5A', 'Hist'): 3,
    ('5A', 'Lit'): 3,
    ('5A', 'Math'): 6,
    ('5A', 'Mus'): 1,
    ('5A', 'PE'): 2,
    ('5A', 'Rus'): 6,
    ('5A', 'VisArt'): 1,
    ('5B', 'Bio'): 1,
    ('5B', 'Geog'): 1,
    ('5B', 'Hist'): 3,
    ('5B', 'Lit'): 3,
    ('5B', 'Math'): 6,
    ('5B', 'Mus'): 1,
    ('5B', 'PE'): 2,
    ('5B', 'Rus'): 6,
    ('5B', 'VisArt'): 1,
    ('5G', 'Bio'): 1,
    ('5G', 'Geog'): 1,
    ('5G', 'Hist'): 3,
    ('5G', 'Lit'): 3,
    ('5G', 'Math'): 6,
    ('5G', 'Mus'): 1,
    ('5G', 'PE'): 2,
    ('5G', 'Rus'): 6,
    ('5G', 'VisArt'): 1,
    ('5V', 'Bio'): 1,
    ('5V', 'Geog'): 1,
    ('5V', 'Hist'): 3,
    ('5V', 'Lit'): 3,
    ('5V', 'Math'): 6,
    ('5V', 'Mus'): 1,
    ('5V', 'PE'): 2,
    ('5V', 'Rus'): 6,
    ('5V', 'VisArt'): 1}
    subgroup_plan_hours = {   ('5A', 'Eng', 1): 3,
    ('5A', 'Eng', 2): 3,
    ('5A', 'Trud', 1): 2,
    ('5A', 'Trud', 2): 2,
    ('5B', 'Eng', 1): 3,
    ('5B', 'Eng', 2): 3,
    ('5B', 'Trud', 1): 2,
    ('5B', 'Trud', 2): 2,
    ('5G', 'Eng', 1): 3,
    ('5G', 'Eng', 2): 3,
    ('5G', 'Trud', 1): 2,
    ('5G', 'Trud', 2): 2,
    ('5V', 'Eng', 1): 3,
    ('5V', 'Eng', 2): 3,
    ('5V', 'Trud', 1): 2,
    ('5V', 'Trud', 2): 2}

    # --- Закрепления учителей ---
    assigned_teacher = {   ('5A', 'Bio'): 'Vor_IG',
    ('5A', 'Geog'): 'Sak_EV',
    ('5A', 'Hist'): 'Osi_EM',
    ('5A', 'Lit'): 'Bel_IV',
    ('5A', 'Math'): 'Put_MG',
    ('5A', 'Mus'): 'Gas_ASh',
    ('5A', 'PE'): 'Vac_fizra',
    ('5A', 'Rus'): 'Bel_IV',
    ('5A', 'VisArt'): 'Kam_SI',
    ('5B', 'Bio'): 'Vor_IG',
    ('5B', 'Geog'): 'Sak_EV',
    ('5B', 'Hist'): 'Osi_EM',
    ('5B', 'Lit'): 'Vac_2',
    ('5B', 'Math'): 'Zal_DI',
    ('5B', 'Mus'): 'Gas_ASh',
    ('5B', 'PE'): 'Vac_fizra',
    ('5B', 'Rus'): 'Vac_2',
    ('5B', 'VisArt'): 'Kam_SI',
    ('5G', 'Bio'): 'Vor_IG',
    ('5G', 'Geog'): 'Sak_EV',
    ('5G', 'Hist'): 'Sta_EV',
    ('5G', 'Lit'): 'Vac_2',
    ('5G', 'Math'): 'Gri_TV',
    ('5G', 'Mus'): 'Gas_ASh',
    ('5G', 'PE'): 'Bur_NS',
    ('5G', 'Rus'): 'Vac_2',
    ('5G', 'VisArt'): 'Kam_SI',
    ('5V', 'Bio'): 'Vor_IG',
    ('5V', 'Geog'): 'Sak_EV',
    ('5V', 'Hist'): 'Sta_EV',
    ('5V', 'Lit'): 'Vac_1',
    ('5V', 'Math'): 'Zal_DI',
    ('5V', 'Mus'): 'Gas_ASh',
    ('5V', 'PE'): 'Bur_NS',
    ('5V', 'Rus'): 'Vac_1',
    ('5V', 'VisArt'): 'Kam_SI'}
    subgroup_assigned_teacher = {   ('5A', 'Eng', 1): 'Got_EV',
    ('5A', 'Eng', 2): 'May_AYu',
    ('5A', 'Trud', 1): 'Gri_TV',
    ('5A', 'Trud', 2): 'Kam_OV',
    ('5B', 'Eng', 1): 'Got_EV',
    ('5B', 'Eng', 2): 'Sha_VE',
    ('5B', 'Trud', 1): 'Gri_TV',
    ('5B', 'Trud', 2): 'Kam_OV',
    ('5G', 'Eng', 1): 'Zhi_VI',
    ('5G', 'Eng', 2): 'Sha_VE',
    ('5G', 'Trud', 1): 'Gri_TV',
    ('5G', 'Trud', 2): 'Kam_OV',
    ('5V', 'Eng', 1): 'Sha_VE',
    ('5V', 'Eng', 2): 'Zhi_VI',
    ('5V', 'Trud', 1): 'Gri_TV',
    ('5V', 'Trud', 2): 'Kam_OV'}

    # --- Ограничения ---
    days_off = {'Osi_EM': {'Mon', 'Tue'}}
    forbidden_slots = {('5A', 'Mon', 1), ('5B', 'Mon', 1)}

    # --- Мягкие цели ---
    class_slot_weight = {('5A', 'Fri', 6): 5, ('5A', 'Fri', 7): 10}
    teacher_slot_weight = {('Vac_2', 'Tue', 1): 8}
    class_subject_day_weight = {('5A', 'Geog', 'Mon'): 6}

    # --- Совместимости ---
    compatible_pairs = {('Eng', 'СЫ')}

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
