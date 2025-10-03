# optimization_weights.py
# -----------------------------------------------------------------------------
# Содержит определение dataclass'а OptimizationWeights и функцию для
# получения весов по умолчанию.
# -----------------------------------------------------------------------------
from dataclasses import dataclass
from typing import Optional


@dataclass
class OptimizationWeights:
    """
    Весовые коэффициенты и параметры решателя для составной целевой функции.

    Примечание к «окнам»:
    - В улучшенной модели «окна» минимизируются как суммарная длина «конверта» (количество
      занятых + пустых слотов между первым и последним занятием) для учителей/классов.
      Поэтому веса alpha_runs / alpha_runs_teacher применяются к этой метрике.

    Также добавлены:
    - use_lexico, lexico_primary: включая «двухфазную» лексикографическую оптимизацию
      (сначала окна одного типа, затем остальные цели).
    - Параметры решателя: num_search_workers, random_seed, time_limit_s, relative_gap_limit.
    """
    # --- Веса целей ---
    alpha_runs: int
    alpha_runs_teacher: int
    beta_early: int
    gamma_balance: int
    delta_tail: int
    epsilon_pairing: int

    # Пользовательские предпочтения (масштаб), если используются вне модели
    pref_scale: int

    # После этого слота начинаются «хвосты» (используется в delta_tail)
    last_ok_period: int

    # --- Параметры решателя ---
    num_search_workers: int
    random_seed: Optional[int]
    time_limit_s: Optional[float]
    relative_gap_limit: float


def get_default_optimization_weights() -> OptimizationWeights:
    """Возвращает экземпляр OptimizationWeights с весами по умолчанию."""
    return OptimizationWeights(
        alpha_runs=10,
        alpha_runs_teacher=2,
        beta_early=1,
        gamma_balance=1,
        delta_tail=10,
        epsilon_pairing=20,
        pref_scale=1,
        last_ok_period=6,
        num_search_workers=20,
        random_seed=1,
        time_limit_s=None,
        relative_gap_limit=0.05,
    )