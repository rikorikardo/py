import itertools
import hashlib
import time
import random
from datetime import datetime, timedelta, timezone
from tqdm import tqdm
from multiprocessing import Pool, cpu_count

def linear_congruential_generator(seed, a=1664525, c=1013904223, m=2**32):
    """ Линейный конгруэнтный генератор (LCG), использовался в старых генераторах паролей """
    while True:
        seed = (a * seed + c) % m
        yield seed

def mersenne_twister(seed):
    """ Используем стандартный random с seed, чтобы эмулировать MT19937 """
    random.seed(seed)
    while True:
        yield random.randint(0, 2**32 - 1)

def sha1_based_generator(seed):
    """ SHA-1 генератор, использовался в некоторых старых программах """
    while True:
        seed = hashlib.sha1(str(seed).encode()).hexdigest()
        yield int(seed[:8], 16)  # Берем первые 8 символов как число

def generate_password_batch(args):
    """ Функция для генерации паролей в параллельных процессах """
    timestamp, method, length, charset, timezone_offset = args
    generated_passwords = set()
    gen = method(timestamp)
    
    # Определяем допустимые символы
    charsets = {
        "digits": "0123456789",
        "letters": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
        "special": "!@#$%^&*()-_=+[]{}|;:,.<>?/",
        "alnum": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
        "alnum_special": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()-_=+[]{}|;:,.<>?/"
    }
    chars = charsets.get(charset, charsets["alnum"])
    
    for _ in range(5):  # Генерируем несколько паролей на один timestamp
        rand_value = next(gen)
        password = "".join(random.choices(chars, k=length))
        generated_passwords.add(password)
    
    return generated_passwords

def generate_passwords(start_date, end_date, methods, num_passwords=1000, charset="alnum", lengths=[10, 11, 12, 13, 14, 15, 16], timezone_offsets=[0]):
    """ Генератор паролей с привязкой ко времени и разными тайм-зонами """
    start_timestamp = int(time.mktime(datetime.strptime(start_date, "%d.%m.%Y").timetuple()))
    end_timestamp = int(time.mktime(datetime.strptime(end_date, "%d.%m.%Y").timetuple()))
    
    pool = Pool(cpu_count())
    generated_passwords = set()
    
    # Подготовка списка задач для параллельного выполнения
    tasks = []
    for timezone_offset in timezone_offsets:
        adjusted_start = int(start_timestamp + timezone_offset * 3600)
        adjusted_end = int(end_timestamp + timezone_offset * 3600)
        
        for timestamp in range(adjusted_start, adjusted_end, 1):  # Перебираем по часам
            for method in methods:
                for length in lengths:
                    tasks.append((timestamp, method, length, charset, timezone_offset))
    
    # Прогресс-бар
    total_iterations = len(tasks)
    progress = tqdm(total=total_iterations, desc="Генерация паролей", unit="пароль", position=0, leave=True)
    
    # Параллельное выполнение
    for result in pool.imap_unordered(generate_password_batch, tasks):
        generated_passwords.update(result)
        progress.update(1)
    
    progress.close()
    pool.close()
    pool.join()
    
    return list(generated_passwords)[:num_passwords]

# Выбор генераторов, которые имитируют 2008-2009 годы
methods = [linear_congruential_generator, mersenne_twister, sha1_based_generator]

# Настройки генерации паролей
start_date = "01.12.2008"  # Начало диапазона
end_date = "03.02.2009"  # Конец диапазона
num_passwords = None  # Количество паролей
charset = "alnum_special"  # Тип символов: digits, letters, special, alnum, alnum_special
lengths = [10, 11, 12, 13, 14, 15, 16]  # Разные длины паролей
timezone_offsets = [0, 5.5, -5, -8]  # Великобритания (UTC+0), Индия (UTC+5.5), США (UTC-5, UTC-8)

# Генерируем пароли
password_list = generate_passwords(start_date, end_date, methods, num_passwords, charset, lengths, timezone_offsets)

# Сохраняем пароли в файл для использования с hashcat
password_file_path = f"passwords_{start_date.replace('.', '_')}_to_{end_date.replace('.', '_')}.txt"
with open(password_file_path, "w") as f:
    for password in password_list:
        f.write(password + "\n")

print(f"Генерация завершена. Пароли сохранены в {password_file_path}")
