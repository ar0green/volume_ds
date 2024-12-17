import math
from typing import Dict, List, Union
import re

class DatasetMemoryCalculator:
    """
    Calculates estimated memory consumption for datasets based on column types and row count.
    """
    
    # Memory sizes in bytes for different data types
    DATA_TYPE_SIZES = {
        'int8': 1,
        'int16': 2,
        'int32': 4,
        'int64': 8,
        'bigint': 8,
        'smallint': 2,
        'float': 4,
        'float32': 4,
        'float64': 8,
        'decimal': 8,  # Estimate for decimal
        'bool': 1,
        'boolean': 1,
        'datetime': 8,
        'string': lambda length: length  # Variable length
    }
    
    def __init__(self):
        self.columns = []
    
    def add_column(self, name: str, data_type: str, length: int = None):
        """
        Add a column to the dataset schema.
        
        Args:
            name (str): Column name
            data_type (str): Data type of the column
            length (int, optional): Length for variable-length types like string
        """
        # Normalize data type
        data_type = data_type.lower().strip()
        
        # Handle decimal type with precision
        if data_type.startswith('decimal'):
            data_type = 'decimal'
        
        # Default length for string types
        if data_type in ['varchar', 'string'] and length is None:
            length = 50
        
        self.columns.append({
            'name': name,
            'type': data_type,
            'length': length
        })
    
    def calculate_column_size(self, column: Dict, row_count: int) -> int:
        """
        Calculate memory size for a single column.
        
        Args:
            column (Dict): Column definition
            row_count (int): Number of rows
        
        Returns:
            int: Estimated memory size in bytes
        """
        # Normalize type
        col_type = column['type'].lower()
        
        # Handle string-like types
        if col_type in ['varchar', 'string', 'char']:
            avg_length = column.get('length', 50)
            return avg_length * row_count
        
        # Get size from predefined types
        size_func = self.DATA_TYPE_SIZES.get(col_type)
        
        # Handle callable size functions (like for strings)
        if callable(size_func):
            return size_func(column.get('length', 0)) * row_count
        
        # Handle potential None values with a default
        if size_func is None:
            print(f"Warning: Unknown type {col_type}. Defaulting to 1 byte.")
            size_func = 1
        
        return size_func * row_count
    
    def calculate_total_memory(self, row_count: int) -> Dict[str, Union[int, float]]:
        """
        Calculate total estimated memory consumption.
        
        Args:
            row_count (int): Number of rows in the dataset
        
        Returns:
            Dict containing memory details
        """
        if not self.columns:
            return {
                'total_bytes': 0,
                'total_kb': 0,
                'total_mb': 0,
                'total_gb': 0
            }
        
        total_bytes = sum(self.calculate_column_size(col, row_count) for col in self.columns)
        
        return {
            'total_bytes': total_bytes,
            'total_kb': total_bytes / 1024,
            'total_mb': total_bytes / (1024 * 1024),
            'total_gb': total_bytes / (1024 * 1024 * 1024)
        }
    
    def parse_create_table_sql(self, sql: str):
        """
        Parse a CREATE TABLE SQL statement to extract column definitions.
        
        Args:
            sql (str): SQL CREATE TABLE statement
        """
        # Reset existing columns
        self.columns = []
        
        # Remove newlines and extra spaces
        sql = re.sub(r'\s+', ' ', sql.strip())
        
        # Comprehensive column parsing regex
        column_pattern = r'"?(\w+)"?\s+(BIGINT|SMALLINT|INT|DECIMAL\(\d+,\d+\)|FLOAT|DOUBLE|VARCHAR\(\d+\)|CHAR\(\d+\)|DATETIME|BOOLEAN|BOOL)(?:\s*NOT\s+NULL)?(?:\s*PRIMARY\s+KEY)?'
        
        # Case-insensitive matching
        matches = re.findall(column_pattern, sql, re.IGNORECASE)
        
        for match in matches:
            column_name, data_type = match
            
            # Extract length for varchar/char
            length_match = re.search(rf'{column_name}\s+{data_type}\((\d+)\)'.replace(' ', r'\s*'), sql, re.IGNORECASE)
            length = int(length_match.group(1)) if length_match else None
            
            # Type mapping and normalization
            type_mapping = {
                'BIGINT': 'bigint',
                'SMALLINT': 'smallint',
                'INT': 'int32',
                'DECIMAL': 'decimal',
                'FLOAT': 'float',
                'DOUBLE': 'float64',
                'VARCHAR': 'string',
                'CHAR': 'string',
                'DATETIME': 'datetime',
                'BOOLEAN': 'bool',
                'BOOL': 'bool'
            }
            
            # Map the type, default to original if not found
            mapped_type = type_mapping.get(data_type.split('(')[0].upper(), data_type.lower())
            
            self.add_column(column_name, mapped_type, length)