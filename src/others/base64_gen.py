import base64

def string_to_base64(input_string):
    # Кодируем строку в байты
    byte_string = input_string.encode('utf-8')
    # Преобразуем байты в base64
    base64_bytes = base64.b64encode(byte_string)
    # Декодируем байты обратно в строку
    base64_string = base64_bytes.decode('utf-8')
    return base64_string


print(string_to_base64(''))
