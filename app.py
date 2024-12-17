import streamlit as st
import re

st.title("Примерный подсчет объема выборки по схеме данных")

st.markdown("""
Это приложение позволит предварительно посчитать объем памяти, занимаемый выборкой с заданным числом строк по метаданным таблицы.
""")

# Вариант ввода: через CREATE TABLE или вручную
input_mode = st.radio("Выберите режим ввода схемы", ["CREATE TABLE", "Ручной ввод столбцов"])

def parse_create_table_ddl(ddl):
    """
    Примитивный парсер для извлечения столбцов и их типов из DDL вида CREATE TABLE.
    Предполагаем формат:
    CREATE TABLE table_name (
       col1 INT,
       col2 VARCHAR(100),
       ...
    )
    """
    # Упростим задачу: достанем всё, что внутри круглых скобок, разобьём по запятой и вытащим типы
    
    # Найдём содержимое скобок
    m = re.search(r'CREATE TABLE.*?\((.*?)\)', ddl, flags=re.IGNORECASE|re.DOTALL)
    if not m:
        return []
    columns_part = m.group(1)
    
    # Разбиваем по запятым с учётом, что могут быть переносы строк
    raw_columns = [c.strip() for c in columns_part.split(',') if c.strip()]
    
    columns = []
    type_pattern = re.compile(r'(\w+)\s+(\w+(\(\d+\))?)', re.IGNORECASE)
    for col_def in raw_columns:
        match = type_pattern.search(col_def)
        if match:
            col_name = match.group(1)
            col_type = match.group(2)
            columns.append((col_name, col_type))
    return columns

def estimate_column_size(col_type):
    """
    Оценка размера столбца на основе типа.
    Предполагаем простые типы: INT, BIGINT, FLOAT, DOUBLE, DATE, TIMESTAMP, VARCHAR(N), CHAR(N).
    """
    col_type = col_type.upper().strip()
    
    # Словарь с размерами типов
    type_sizes = {
        "INT": 4,
        "BIGINT": 8,
        "FLOAT": 4,
        "DOUBLE": 8,
        "DATE": 3,
        "TIMESTAMP": 8,
        # Для VARCHAR и CHAR специальная логика ниже
    }
    
    var_match = re.match(r'(VARCHAR|CHAR)\((\d+)\)', col_type)
    if var_match:
        base_type = var_match.group(1)
        length = int(var_match.group(2))
        return length  # для упрощения считаем кол-во байт = длине
    
    # Если просто VARCHAR без длины - 255
    if col_type.startswith("VARCHAR"):
        return 255
    
    # Если просто CHAR без длины - 1
    if col_type.startswith("CHAR"):
        return 1
    
    if col_type in type_sizes:
        return type_sizes[col_type]
    
    # Неизвестный тип - 4 байта
    return 4

def format_size(bytes_size):
    """
    Форматирование размера в человекочитаемый вид (байты, КБ, МБ, ГБ).
    """
    for unit in ['Б', 'КБ', 'МБ', 'ГБ', 'ТБ']:
        if bytes_size < 1024.0:
            return f"{bytes_size:3.1f} {unit}"
        bytes_size /= 1024.0


if input_mode == "CREATE TABLE":
    ddl_input = st.text_area("Вставьте выражение CREATE TABLE:", height=200)
    if ddl_input:
        columns = parse_create_table_ddl(ddl_input)
        if columns:
            st.write("Найденные столбцы:")
            for c in columns:
                st.write(f"- {c[0]}: {c[1]}")
            
            row_count = st.number_input("Количество строк:", min_value=1, value=1000000)
            if st.button("Рассчитать"):
                total_per_row = 0
                for _, col_t in columns:
                    total_per_row += estimate_column_size(col_t)
                
                total_size = total_per_row * row_count
                st.write(f"Размер одной строки: {total_per_row} байт")
                st.write(f"Общий размер: {total_size} байт ({format_size(total_size)})")
        else:
            st.warning("Не удалось распарсить столбцы из DDL.")
            
else:
    st.write("Добавьте столбцы вручную")
    num_cols = st.number_input("Сколько столбцов?", min_value=1, value=3)
    
    cols_data = []
    for i in range(num_cols):
        st.markdown(f"**Столбец {i+1}**")
        c_name = st.text_input(f"Имя столбца {i+1}", value=f"col{i+1}")
        c_type = st.selectbox(f"Тип столбца {i+1}", 
                              ["INT", "BIGINT", "FLOAT", "DOUBLE", "DATE", "TIMESTAMP", "VARCHAR(255)", "CHAR(10)"],
                              index=0,
                              key=f"type_{i}")
        cols_data.append((c_name, c_type))
        
        if i < num_cols - 1:
            st.markdown("---")
    
    row_count = st.number_input("Количество строк:", min_value=1, value=1000000)
    
    if st.button("Рассчитать"):
        total_per_row = sum(estimate_column_size(ct) for _, ct in cols_data)
        total_size = total_per_row * row_count
        st.write(f"Размер одной строки: {total_per_row} байт")
        st.write(f"Общий размер: {total_size} байт ({format_size(total_size)})")
