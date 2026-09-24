# negative-unrelated — env `clean`, model `haiku`

- Tool calls: **0**, skills used: none
- Cost: $0.0185, duration: 4.9 s, tokens in/out: 10/536 (cache read 15295)

## Turn 1

> **User:** Напиши функцію на Python, яка рахує медіану списку чисел.

**Assistant:** Ось простих способи обчислити медіану:

**Варіант 1: Вбудована функція (найлегший)**
```python
from statistics import median


def calculate_median(numbers):
    return median(numbers)
```

**Варіант 2: Власна реалізація**
```python
def calculate_median(numbers):
    if not numbers:
        raise ValueError("Список не може бути порожнім")
    
    sorted_numbers = sorted(numbers)
    n = len(sorted_numbers)
    
    if n % 2 == 1:
        # Непарна кількість елементів
        return sorted_numbers[n // 2]
    else:
        # Парна кількість елементів
        mid1 = sorted_numbers[n // 2 - 1]
        mid2 = sorted_numbers[n // 2]
        return (mid1 + mid2) / 2
```

**Приклади використання:**
```python
print(calculate_median([3, 1, 4, 1, 5]))  # 3
print(calculate_median([1, 2, 3, 4]))  # 2.5
print(calculate_median([42]))  # 42
```

**Пояснення:**
- Для непарної кількості елементів медіана — це середній елемент відсортованого списку
- Для парної кількості елементів медіана — це середнє арифметичне двох середніх елементів

Використовуйте варіант 2 для повної контролю, або `statistics.median()` для простоти.

### Final answer

Ось простих способи обчислити медіану:

**Варіант 1: Вбудована функція (найлегший)**
```python
from statistics import median


def calculate_median(numbers):
    return median(numbers)
```

**Варіант 2: Власна реалізація**
```python
def calculate_median(numbers):
    if not numbers:
        raise ValueError("Список не може бути порожнім")
    
    sorted_numbers = sorted(numbers)
    n = len(sorted_numbers)
    
    if n % 2 == 1:
        # Непарна кількість елементів
        return sorted_numbers[n // 2]
    else:
        # Парна кількість елементів
        mid1 = sorted_numbers[n // 2 - 1]
        mid2 = sorted_numbers[n // 2]
        return (mid1 + mid2) / 2
```

**Приклади використання:**
```python
print(calculate_median([3, 1, 4, 1, 5]))  # 3
print(calculate_median([1, 2, 3, 4]))  # 2.5
print(calculate_median([42]))  # 42
```

**Пояснення:**
- Для непарної кількості елементів медіана — це середній елемент відсортованого списку
- Для парної кількості елементів медіана — це середнє арифметичне двох середніх елементів

Використовуйте варіант 2 для повної контролю, або `statistics.median()` для простоти.
