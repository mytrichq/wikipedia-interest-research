# negative-unrelated — env `clean`, model `haiku`

- Tool calls: **0**, skills used: none
- Cost: $0.0182, duration: 5.7 s, tokens in/out: 10/483 (cache read 15295)

## Turn 1

> **User:** Напиши функцію на Python, яка рахує медіану списку чисел.

**Assistant:** ```python
def median(numbers):
    """Рахує медіану списку чисел."""
    sorted_nums = sorted(numbers)
    n = len(sorted_nums)
    
    if n % 2 == 1:
        return sorted_nums[n // 2]
    else:
        mid1 = sorted_nums[n // 2 - 1]
        mid2 = sorted_nums[n // 2]
        return (mid1 + mid2) / 2

# Приклади
print(median([3, 1, 4, 1, 5, 9, 2, 6]))  # 3.5
print(median([7, 2, 5]))                   # 5
print(median([10]))                        # 10
```

Функція працює так:
1. Сортує список
2. Якщо кількість елементів непарна — повертає середній елемент
3. Якщо кількість елементів парна — повертає середнє арифметичне двох середніх елементів

Альтернативно, можна використати модуль `statistics`:

```python
from statistics import median

print(median([3, 1, 4, 1, 5, 9, 2, 6]))  # 3.5
```

### Final answer

```python
def median(numbers):
    """Рахує медіану списку чисел."""
    sorted_nums = sorted(numbers)
    n = len(sorted_nums)

    if n % 2 == 1:
        return sorted_nums[n // 2]
    else:
        mid1 = sorted_nums[n // 2 - 1]
        mid2 = sorted_nums[n // 2]
        return (mid1 + mid2) / 2


# Приклади
print(median([3, 1, 4, 1, 5, 9, 2, 6]))  # 3.5
print(median([7, 2, 5]))  # 5
print(median([10]))  # 10
```

Функція працює так:
1. Сортує список
2. Якщо кількість елементів непарна — повертає середній елемент
3. Якщо кількість елементів парна — повертає середнє арифметичне двох середніх елементів

Альтернативно, можна використати модуль `statistics`:

```python
from statistics import median

print(median([3, 1, 4, 1, 5, 9, 2, 6]))  # 3.5
```
