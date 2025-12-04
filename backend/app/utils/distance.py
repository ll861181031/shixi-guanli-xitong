import math

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    使用Haversine公式计算两点之间的距离（米）
    
    Args:
        lat1: 第一个点的纬度
        lon1: 第一个点的经度
        lat2: 第二个点的纬度
        lon2: 第二个点的经度
    
    Returns:
        距离（米）
    """
    # 地球半径（米）
    R = 6371000
    
    # 转换为弧度
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    # Haversine公式
    a = math.sin(delta_phi / 2) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    # 计算距离
    distance = R * c
    
    return distance

def check_checkin_status(distance, normal_distance=200, abnormal_distance=500):
    """
    根据距离判断签到状态
    
    Args:
        distance: 距离（米）
        normal_distance: 正常签到距离阈值（米）
        abnormal_distance: 异常签到距离阈值（米）
    
    Returns:
        'normal' 或 'abnormal'
    """
    if distance <= normal_distance:
        return 'normal'
    elif distance > abnormal_distance:
        return 'abnormal'
    else:
        # 200-500米之间，根据配置可以设为normal或abnormal
        # 这里设为normal，但可以记录为警告
        return 'normal'

