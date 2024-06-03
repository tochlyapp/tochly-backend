import time
import random
import string


def generate_id(i:str, x:int, y:int):
    timestamp = str(int(time.time()))[-x:]
    random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=y))
    return f'{i}{timestamp}{random_chars}'
