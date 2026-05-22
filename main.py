import string
CHARSET = string.digits + string.ascii_lowercase + string.ascii_uppercase

def encode_base62(num):
    if num == 0:
        return CHARSET[0]
    arr = []
    while num:
        num, rem =  divmod(num, 62)
        arr.append(CHARSET[rem])

    arr.reverse()
    return ''.join(arr)

def decode_base62(s):
    num = 0
    for char in s:
        num = num * 62 + CHARSET.index(char)
    return num

