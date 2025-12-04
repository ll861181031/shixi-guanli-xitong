from app.utils.errors import APIError
import re

def validate_email(email):
    """验证邮箱格式"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise APIError('邮箱格式不正确', 400, 'INVALID_EMAIL')

def validate_phone(phone):
    """验证手机号格式"""
    pattern = r'^1[3-9]\d{9}$'
    if not re.match(pattern, phone):
        raise APIError('手机号格式不正确', 400, 'INVALID_PHONE')

def validate_student_id(student_id):
    """验证学号格式"""
    if not student_id or len(student_id) < 5:
        raise APIError('学号格式不正确', 400, 'INVALID_STUDENT_ID')

def validate_coordinates(latitude, longitude):
    """验证经纬度"""
    if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
        raise APIError('经纬度格式不正确', 400, 'INVALID_COORDINATES')
    if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
        raise APIError('经纬度范围不正确', 400, 'INVALID_COORDINATES_RANGE')

def validate_required(data, fields):
    """验证必填字段"""
    missing_fields = [field for field in fields if field not in data or not data[field]]
    if missing_fields:
        raise APIError(f'缺少必填字段: {", ".join(missing_fields)}', 400, 'MISSING_FIELDS')

