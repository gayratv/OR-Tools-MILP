def add_teacher_window_optimization_v4(self):
    """
    Эффективная оптимизация окон учителей через минимизацию разрывов
    """

    # 1. Создаем вспомогательные переменные для начала и конца работы каждого учителя
    teacher_first_slot = {}
    teacher_last_slot = {}

    for teacher_id in range(self.num_teachers):
        # Переменная для первого слота работы учителя
        teacher_first_slot[teacher_id] = self.model.NewIntVar(
            0, self.num_slots - 1, f'teacher_{teacher_id}_first_slot'
        )
        # Переменная для последнего слота работы учителя
        teacher_last_slot[teacher_id] = self.model.NewIntVar(
            0, self.num_slots - 1, f'teacher_{teacher_id}_last_slot'
        )

        # Ограничение: последний слот >= первый слот
        self.model.Add(teacher_last_slot[teacher_id] >= teacher_first_slot[teacher_id])

    # 2. Связываем эти переменные с фактическим расписанием
    for teacher_id in range(self.num_teachers):
        teacher_slots = []

        # Собираем все слоты, где учитель работает
        for product_id in self.products_by_teacher[teacher_id]:
            for slot in range(self.num_slots):
                # Используем существующую переменную product_in_slot
                teacher_slots.append((slot, self.product_in_slot[(product_id, slot)]))

        if teacher_slots:
            # Ограничения для первого слота
            # Если учитель работает в слоте s, то first_slot <= s
            for slot, var in teacher_slots:
                self.model.Add(teacher_first_slot[teacher_id] <= slot).OnlyEnforceIf(var)

            # Ограничения для последнего слота
            # Если учитель работает в слоте s, то last_slot >= s
            for slot, var in teacher_slots:
                self.model.Add(teacher_last_slot[teacher_id] >= slot).OnlyEnforceIf(var)

            # 3. Добавляем ограничение компактности через вспомогательную переменную
            # Считаем количество "дырок" в расписании
            holes_count = self.model.NewIntVar(0, self.num_slots, f'teacher_{teacher_id}_holes')

            # Количество дырок = (последний - первый + 1) - количество рабочих слотов
            working_slots = self.model.NewIntVar(0, self.num_slots, f'teacher_{teacher_id}_working_slots')
            self.model.Add(working_slots == sum(var for _, var in teacher_slots))

            window_size = self.model.NewIntVar(0, self.num_slots, f'teacher_{teacher_id}_window')
            self.model.Add(window_size == teacher_last_slot[teacher_id] - teacher_first_slot[teacher_id] + 1)

            self.model.Add(holes_count == window_size - working_slots)

            # Минимизируем количество дырок
            self.teacher_holes.append(holes_count)

    # 4. Альтернативный подход через "активные периоды"
    self.add_active_periods_optimization()

    return sum(self.teacher_holes)


def add_active_periods_optimization(self):
    """
    Оптимизация через минимизацию количества активных периодов
    """

    for teacher_id in range(self.num_teachers):
        if teacher_id not in self.products_by_teacher:
            continue

        # Создаем бинарные переменные для "активных периодов"
        # Период активен, если есть хотя бы один урок в течение WINDOW_SIZE слотов
        WINDOW_SIZE = 3  # Размер окна для группировки

        num_windows = (self.num_slots + WINDOW_SIZE - 1) // WINDOW_SIZE
        teacher_active_windows = []

        for window_id in range(num_windows):
            window_start = window_id * WINDOW_SIZE
            window_end = min((window_id + 1) * WINDOW_SIZE, self.num_slots)

            # Переменная: активно ли это окно для учителя
            is_active = self.model.NewBoolVar(f'teacher_{teacher_id}_window_{window_id}_active')

            # Окно активно, если есть хотя бы один урок
            window_lessons = []
            for product_id in self.products_by_teacher[teacher_id]:
                for slot in range(window_start, window_end):
                    if slot < self.num_slots:
                        window_lessons.append(self.product_in_slot[(product_id, slot)])

            if window_lessons:
                # Если хотя бы один урок есть, окно активно
                self.model.AddMaxEquality(is_active, window_lessons)
                teacher_active_windows.append(is_active)

        # Минимизируем количество активных окон
        if teacher_active_windows:
            self.teacher_active_periods[teacher_id] = sum(teacher_active_windows)


def add_efficient_teacher_optimization(self):
    """
    Комбинированный эффективный подход
    """

    # 1. Используем агрегированные переменные для уменьшения пространства поиска
    for teacher_id in range(self.num_teachers):
        if teacher_id not in self.products_by_teacher:
            continue

        products = self.products_by_teacher[teacher_id]

        # Создаем переменную "занятости" для каждого слота
        teacher_busy = {}
        for slot in range(self.num_slots):
            # Учитель занят в слоте, если любой из его продуктов производится
            slot_products = [self.product_in_slot[(p, slot)] for p in products
                             if (p, slot) in self.product_in_slot]

            if slot_products:
                teacher_busy[slot] = self.model.NewBoolVar(f'teacher_{teacher_id}_busy_{slot}')
                self.model.AddMaxEquality(teacher_busy[slot], slot_products)

        if not teacher_busy:
            continue

        # 2. Минимизируем переключения (transitions)
        transitions = []
        for slot in range(self.num_slots - 1):
            if slot in teacher_busy and (slot + 1) in teacher_busy:
                # Переход из незанятого в занятый слот
                transition = self.model.NewBoolVar(f'teacher_{teacher_id}_transition_{slot}')

                # transition = 1 если (not busy[slot]) and busy[slot+1]
                not_busy_current = self.model.NewBoolVar(f'not_busy_{teacher_id}_{slot}')
                self.model.Add(not_busy_current == 1 - teacher_busy[slot])

                self.model.AddMultiplicationEquality(
                    transition, [not_busy_current, teacher_busy[slot + 1]]
                )
                transitions.append(transition)

        # Количество переходов = количество "разрывов" + 1
        if transitions:
            self.teacher_transitions[teacher_id] = sum(transitions)


# Модификация целевой функции
def create_objective_with_efficient_windows(self):
    """
    Целевая функция с эффективной оптимизацией окон
    """

    objective_terms = []

    # Основная цель - минимизация makespan
    objective_terms.append(self.makespan * 1000)

    # Добавляем штраф за окна учителей
    if self.teacher_holes:  # Из add_teacher_window_optimization_v4
        # Меньший вес для окон, чтобы не доминировать над основной целью
        window_penalty = sum(self.teacher_holes) * 10
        objective_terms.append(window_penalty)

    # Или используем активные периоды
    if self.teacher_active_periods:
        periods_penalty = sum(self.teacher_active_periods.values()) * 50
        objective_terms.append(periods_penalty)

    # Или используем переходы
    if self.teacher_transitions:
        transitions_penalty = sum(self.teacher_transitions.values()) * 20
        objective_terms.append(transitions_penalty)

    self.model.Minimize(sum(objective_terms))


# Добавляем симметрию для ускорения
def add_symmetry_breaking_constraints(self):
    """
    Ограничения для устранения симметричных решений
    """

    # Упорядочиваем продукты одного учителя
    for teacher_id in range(self.num_teachers):
        if teacher_id not in self.products_by_teacher:
            continue

        products = sorted(self.products_by_teacher[teacher_id])

        # Если продукты идентичны, упорядочиваем их выполнение
        for i in range(len(products) - 1):
            p1, p2 = products[i], products[i + 1]

            # Проверяем, идентичны ли продукты
            if (self.input_data.products[p1].product_volume ==
                    self.input_data.products[p2].product_volume):
                # Добавляем ограничение: p1 должен начаться раньше p2
                self.model.Add(self.starts[p1] <= self.starts[p2])


## Рекомендации по использованию:

# 1. **Начните с `add_teacher_window_optimization_v4`** - она использует меньше переменных
# 2. **Настройте веса в целевой функции** в зависимости от приоритетов
# 3. **Используйте `add_symmetry_breaking_constraints`** для ускорения поиска
# 4. **Экспериментируйте с WINDOW_SIZE** в `add_active_periods_optimization`
#
# Эти подходы должны работать значительно быстрее, так как:
# - Используют меньше бинарных переменных
# - Применяют агрегацию для уменьшения пространства поиска
# - Устраняют симметричные решения
# - Используют более простые ограничения
