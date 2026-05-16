import requests
import base64
import json
import re
import urllib.parse

SOURCES = [
    "https://etoneya.best/1",
    "https://github.com/sakha1370/OpenRay/raw/refs/heads/main/output/all_valid_proxies.txt"
]

def extract_flag(text):
    # Ищем флаги стран (Regional Indicator Symbols)
    flags = re.findall(r'[\U0001F1E6-\U0001F1FF]{2}', text)
    if flags:
        return flags[0]
    # Если флага нет, поищем любые другие эмодзи (локации часто помечают ими)
    emojis = re.findall(r'[\u2600-\u27BF:\U0001F300-\U0001F64F\U0001F680-\U0001F6FF]', text)
    return emojis[0] if emojis else ""

def decode_base64(data):
    try:
        # Добавляем паддинг, если нужно
        missing_padding = len(data) % 4
        if missing_padding:
            data += '=' * (4 - missing_padding)
        return base64.b64decode(data).decode('utf-8', errors='ignore')
    except Exception:
        return ""

def get_configs():
    raw_lines = []
    for url in SOURCES:
        try:
            response = requests.get(url, timeout=15)
            if response.status_code != 200:
                continue
            content = response.text.strip()
            
            # Если контент похож на чистый base64, декодируем
            if "://" not in content and len(content) > 100:
                decoded = decode_base64(content)
                lines = decoded.splitlines()
            else:
                lines = content.splitlines()
                
            for line in lines:
                line = line.strip()
                if line and "://" in line:
                    raw_lines.append(line)
        except Exception as e:
            print(f"Ошибка при чтении {url}: {e}")
    return raw_lines

def process_configs(raw_configs):
    unique_configs = {}
    
    for config in raw_configs:
        try:
            if config.startswith("vmess://"):
                # Разбираем vmess (он внутри в base64 json)
                b64_data = config.split("://")[1]
                decoded_json = decode_base64(b64_data)
                data = json.loads(decoded_json)
                
                # Ключ для уникальности (сервер + порт + id)
                unique_key = f"vmess-{data.get('add')}-{data.get('port')}-{data.get('id')}"
                
                old_remark = data.get('ps', '')
                flag = extract_flag(old_remark)
                
                # Переименовываем
                data['ps'] = f"{flag} @anonymouskeys".strip()
                
                # Собираем обратно
                new_json = json.dumps(data)
                new_b64 = base64.b64encode(new_json.encode('utf-8')).decode('utf-8')
                unique_configs[unique_key] = f"vmess://{new_b64}"
                
            else:
                # Для vless, trojan, ss, hysteria и т.д.
                # Делим по решетке, чтобы отделить параметры от названия
                if "#" in config:
                    base_part, old_remark = config.split("#", 1)
                    old_remark = urllib.parse.unquote(old_remark)
                else:
                    base_part, old_remark = config, ""
                
                # Ключ уникальности — сам конфиг без названия
                unique_key = base_part
                
                flag = extract_flag(old_remark)
                new_remark = urllib.parse.quote(f"{flag} @anonymouskeys".strip())
                
                unique_configs[unique_key] = f"{base_part}#{new_remark}"
                
        except Exception as e:
            continue
            
    return list(unique_configs.values())

def main():
    print("Сбор конфигураций...")
    raw_configs = get_configs()
    print(f"Собрано сырых строк: {len(raw_configs)}")
    
    final_configs = process_configs(raw_configs)
    print(f"После удаления дубликатов осталось: {len(final_configs)}")
    
    # 1. Сохраняем в обычном текстовом виде (для современных клиентов)
    with open("subscription.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(final_configs))
        
    # 2. Сохраняем в формате Base64 (для старых клиентов)
    b64_content = base64.b64encode("\n".join(final_configs).encode('utf-8')).decode('utf-8')
    with open("subscription_base64.txt", "w", encoding="utf-8") as f:
        f.write(b64_content)

if __name__ == "__main__":
    main()

