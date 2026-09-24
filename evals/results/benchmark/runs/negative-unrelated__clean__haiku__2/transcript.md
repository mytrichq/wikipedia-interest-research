# negative-unrelated — env `clean`, model `haiku`

- Tool calls: **0**, skills used: none
- Cost: $0.018, duration: 5.6 s, tokens in/out: 10/438 (cache read 15295)

## Turn 1

> **User:** Напиши функцію на Python, яка рахує медіану списку чисел.

**Assistant:** Ось функція для розрахування медіани списку чисел:

```python
def median(numbers):
    sorted_nums = sorted(numbers)
    n = len(sorted_nums)
    
    if n % 2 == 1:
        return sorted_nums[n // 2]
    else:
        mid1 = sorted_nums[n // 2 - 1]
        mid2 = sorted_nums[n // 2]
        return (mid1 + mid2) / 2
```

**Як це працює:**
- Сортує список
- Якщо кількість елементів непарна, повертає середній елемент
- Якщо кількість елементів парна, повертає середнє арифметичне двох середніх елементів

**Приклади використання:**
```python
print(median([3, 1, 4, 1, 5]))  # 3
print(median([10, 20, 30, 40]))  # 25.0
print(median([7]))  # 7
```

Альтернативно, можна використати модуль `statistics`:
```python
from statistics import median

print(median([3, 1, 4, 1, 5]))  # 3
```

### Final answer

Ось функція для розрахування медіани списку чисел:

```python
def median(numbers):
    sorted_nums = sorted(numbers)
    n = len(sorted_nums)
    
    if n % 2 == 1:
        return sorted_nums[n // 2]
    else:
        mid1 = sorted_nums[n // 2 - 1]
        mid2 = sorted_nums[n // 2]
        return (mid1 + mid2) / 2
```

**Як це працює:**
- Сортує список
- Якщо кількість елементів непарна, повертає середній елемент
- Якщо кількість елементів парна, повертає середнє арифметичне двох середніх елементів

**Приклади використання:**
```python
print(median([3, 1, 4, 1, 5]))  # 3
print(median([10, 20, 30, 40]))  # 25.0
print(median([7]))  # 7
```

Альтернативно, можна використати модуль `statistics`:
```python
from statistics import median

print(median([3, 1, 4, 1, 5]))  # 3
```
