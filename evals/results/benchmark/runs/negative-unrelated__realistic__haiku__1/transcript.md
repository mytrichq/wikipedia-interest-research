# negative-unrelated — env `realistic`, model `haiku`

- Tool calls: **0**, skills used: none
- Cost: $0.0276, duration: 5.5 s, tokens in/out: 10/575 (cache read 15295)

## Turn 1

> **User:** Напиши функцію на Python, яка рахує медіану списку чисел.

**Assistant:** Ось функція для розрахунку медіани списку чисел:

```python
def mediana(numbers):
    """
    Розраховує медіану списку чисел.

    Args:
        numbers: Список чисел

    Returns:
        Медіана списку
    """
    if not numbers:
        raise ValueError("Список не може бути порожнім")

    sorted_numbers = sorted(numbers)
    n = len(sorted_numbers)

    if n % 2 == 1:
        return sorted_numbers[n // 2]
    else:
        middle1 = sorted_numbers[n // 2 - 1]
        middle2 = sorted_numbers[n // 2]
        return (middle1 + middle2) / 2


# Приклади використання
print(mediana([3, 1, 4, 1, 5, 9]))  # 3.5
print(mediana([7, 2, 9]))  # 7
print(mediana([5]))  # 5
```

**Як це працює:**

1. **Сортування** — список спочатку сортується у порядку зростання
2. **Непарна довжина** — якщо кількість елементів непарна, медіана — це середній елемент
3. **Парна довжина** — якщо кількість елементів парна, медіана — це середнє арифметичне двох середніх елементів

**Альтернатива з бібліотекою `statistics`:**
```python
import statistics

mediana = statistics.median([3, 1, 4, 1, 5, 9])  # 3.5
```

Яку версію ви б вибрали — власну реалізацію чи вбудовану функцію?

### Final answer

Ось функція для розрахунку медіани списку чисел:

```python
def mediana(numbers):
    """
    Розраховує медіану списку чисел.

    Args:
        numbers: Список чисел

    Returns:
        Медіана списку
    """
    if not numbers:
        raise ValueError("Список не може бути порожнім")

    sorted_numbers = sorted(numbers)
    n = len(sorted_numbers)

    if n % 2 == 1:
        return sorted_numbers[n // 2]
    else:
        middle1 = sorted_numbers[n // 2 - 1]
        middle2 = sorted_numbers[n // 2]
        return (middle1 + middle2) / 2


# Приклади використання
print(mediana([3, 1, 4, 1, 5, 9]))  # 3.5
print(mediana([7, 2, 9]))  # 7
print(mediana([5]))  # 5
```

**Як це працює:**

1. **Сортування** — список спочатку сортується у порядку зростання
2. **Непарна довжина** — якщо кількість елементів непарна, медіана — це середній елемент
3. **Парна довжина** — якщо кількість елементів парна, медіана — це середнє арифметичне двох середніх елементів

**Альтернатива з бібліотекою `statistics`:**
```python
import statistics

mediana = statistics.median([3, 1, 4, 1, 5, 9])  # 3.5
```

Яку версію ви б вибрали — власну реалізацію чи вбудовану функцію?
