import json
from typing import Dict, Any, Tuple

# Import the database connection function using a relative import
# from .db_connector import get_db_connection
from mysql_io.sql_connector_pool import Database

# --- JSON serialization helper ---

db = Database()

def to_serializable(obj: Any) -> Any:
    """
    Recursively converts an object to a JSON-serializable format.
    - Converts dict keys to strings.
    - Converts objects with __dict__ to dicts.
    - Converts sets and tuples to lists.
    """
    if isinstance(obj, dict):
        return {str(k): to_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, set, tuple)):
        return [to_serializable(elem) for elem in obj]
    if hasattr(obj, "__dict__"):
        return to_serializable(obj.__dict__)
    return obj

# --- Main save function ---

def save_calculation_results(
    job_id: int,
    data: Any, # InputData
    solution_maps: Dict[str, Dict[Tuple, float]],
    display_maps: Dict[str, Dict[str, str]],
    solution_stats: Dict[str, Any],
    weights: Any # OptimizationWeights
):
    """
    Saves all calculation results (stats, schedule, input data)
    to a MySQL database.

    Args:
        job_id (int): The job identifier.
        data (InputData): The input data object.
        solution_maps (dict): Solution maps (x_sol, z_sol).
        display_maps (dict): Maps for displaying names.
        solution_stats (dict): Statistics from the solver.
        weights (OptimizationWeights): Weights used for optimization.
    """
    conn = None
    cursor = None
    try:
        # conn = get_db_connection()
        # cursor = conn.cursor()

        print(f"======== Save to MYSQL ==============")

        # 1. Serialize complex objects to JSON
        weights_json = json.dumps(to_serializable(weights), ensure_ascii=False, indent=4)
        input_data_json = json.dumps(to_serializable(data), ensure_ascii=False, indent=4)
        solution_maps_json = json.dumps(to_serializable(solution_maps), indent=4)
        display_maps_json = json.dumps(display_maps, ensure_ascii=False, indent=4)

        # 2. Insert into calculation_results table
        insert_results_query = '''
        INSERT INTO calc_results(
            job_id, status, objective_value, wall_time_s,
            total_lonely_lessons, total_teacher_windows,
            weights_json, input_data_json, solution_maps_json, display_maps_json
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        '''
        results_data = (
            job_id,
            solution_stats.get("status"),
            solution_stats.get("objective_value"),
            solution_stats.get("wall_time_s"),
            solution_stats.get("total_lonely_lessons"),
            solution_stats.get("total_teacher_windows"),
            weights_json,
            input_data_json,
            solution_maps_json,
            display_maps_json
        )
        # cursor.execute(insert_results_query, results_data)
        db.execute(insert_results_query, results_data)
        print(f"Summary results for job_id={job_id} have been saved.")

        # 3. Prepare and insert detailed schedule into schedule_details
        x_sol = solution_maps.get('x', {})
        z_sol = solution_maps.get('z', {})
        subject_names = display_maps.get("subject_names", {})
        teacher_names = display_maps.get("teacher_names", {})

        def get_name(name_map, key, default_key):
            return name_map.get(key, default_key)

        schedule_records = []
        # Non-split subjects
        for (c, s, d, p), val in x_sol.items():
            if val > 0.5:
                t_id = data.assigned_teacher.get((c, s), '?')
                record = (job_id, c, get_name(subject_names, s, s), get_name(teacher_names, t_id, t_id), d, p, None)
                schedule_records.append(record)

        # Split subjects
        for (c, s, g, d, p), val in z_sol.items():
            if val > 0.5:
                t_id = data.subgroup_assigned_teacher.get((c, s, g), '?')
                record = (job_id, c, get_name(subject_names, s, s), get_name(teacher_names, t_id, t_id), d, p, g)
                schedule_records.append(record)

        if schedule_records:
            insert_schedule_query = '''
            INSERT INTO  calc_schedule_details(
                job_id, class_name, subject_name, teacher_name, day, period, subgroup_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            '''
            # cursor.executemany(insert_schedule_query, schedule_records)

            # - List[int]:
            #             Возвращается для пакетных INSERT-операций с `executemany`
            #             (когда `rows=False`, `many=True` и SQL начинается с "INSERT").
            #             Список содержит новые ID, сгенерированные для вставленных строк,
            #             в том же порядке, в котором были переданы данные.
            #             Пример: db.executemany("INSERT INTO users (name) VALUES (%s)", [("Alice",), ("Bob",)])
            id_list =db.executemany(insert_schedule_query,  schedule_records)
            print(f"{len(id_list)} detailed schedule records have been saved. New IDs: {id_list}")

        # conn.commit()
        print("All data has been successfully saved to the database.")

    # except Exception as e:
    #     if conn:
    #         conn.rollback()
    #     print(f"Error while saving to DB: {e}")
    finally:
    #     if conn and conn.is_connected():
    #         if cursor:
    #             cursor.close()
    #         conn.close()
            print("Database connection closed.")
