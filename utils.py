def log(*args, **kwargs):
    print(*args, **kwargs)
    with open('shit.log', 'a', encoding='utf-8') as f:
        print(*args, file=f, **kwargs)