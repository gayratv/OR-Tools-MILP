
import os
import json
from typing import Dict, Any, Tuple

# Import the database connection function using a relative import
from .db_connector import get_db_connection

# --- JSON serialization helper ---

class GenericEncoder(json.JSONEncoder):
    """
    A universal JSON encoder that handles dataclasses,
    other objects (via __dict__), and sets.
    """
    def default(self, o):
        if hasattr(o, '__dict__'):
            return o.__dict__
        if isinstance(o, set):
            return list(o)
        return super().default(o)

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
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. Serialize complex objects to JSON
        # Tuple keys in solution_maps need to be converted to strings
        s_maps_serializable = {
            'x': {str(k): v for k, v in solution_maps.get('x', {}).items()},
            'z': {str(k): v for k, v in solution_maps.get('z', {}).items()}
        }

        weights_json = json.dumps(weights, cls=GenericEncoder, ensure_ascii=False, indent=4)
        input_data_json = json.dumps(data, cls=GenericEncoder, ensure_ascii=False, indent=4)
        solution_maps_json = json.dumps(s_maps_serializable, indent=4)
        display_maps_json = json.dumps(display_maps, ensure_ascii=False, indent=4)

        # 2. Insert into calculation_results table
        insert_results_query = '''
        INSERT INTO calculation_results (
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
        cursor.execute(insert_results_query, results_data)
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
            INSERT INTO schedule_details (
                job_id, class_name, subject_name, teacher_name, day, period, subgroup_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            '''
            cursor.executemany(insert_schedule_query, schedule_records)
            print(f"{cursor.rowcount} detailed schedule records have been saved.")

        conn.commit()
        print("All data has been successfully saved to the database.")

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error while saving to DB: {e}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
            print("Database connection closed.")
