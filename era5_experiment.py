"""
=============================================================================
Prerequisites / 运行前准备工作
=============================================================================
1. 安装必要的 Python 库:
   在终端或虚拟环境中运行:
   pip install cdsapi xarray netCDF4 pandas numpy pytz

2. 配置 Copernicus CDS API 密钥:
   - 注册并登录 Copernicus 气候数据中心: https://cds.climate.copernicus.eu/
   - 获取你的 API Key: 访问 https://cds.climate.copernicus.eu/how-to-api
   - 创建配置文件: 在你的用户根目录下（Mac/Linux: `~/.cdsapirc`, 
     Windows: `C:\\Users\\<你的用户名>\\.cdsapirc`）创建一个名为 `.cdsapirc` 的纯文本文件。
   - 将以下内容填入文件 (替换为你自己的 UID 和 Key):
     url: https://cds.climate.copernicus.eu/api/v2
     key: <YOUR-UID>:<YOUR-API-KEY>
=============================================================================
"""

import cdsapi
import xarray as xr
import pandas as pd
import numpy as np
import math
from datetime import datetime, timedelta
import pytz

# --- 辅助函数定义 ---
def calculate_rh(t_c, td_c):
    # 使用 August-Roche-Magnus 公式计算相对湿度，输入必须为摄氏度
    return 100 * (np.exp((17.625 * td_c) / (243.04 + td_c)) / np.exp((17.625 * t_c) / (243.04 + t_c)))

def calculate_distance_miles(lat1, lon1, lat2, lon2):
    # Haversine 公式计算两点球面距离
    R = 3958.8  # 地球平均半径 (英里)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * \
        math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

# --- 1. 时区与日期配置 ---
local_tz = pytz.timezone('America/Los_Angeles') # 西海岸时区 (自动处理 PST/PDT)
target_date_str = '2026-04-25'                  # 目标当地日期
target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()

# 为覆盖西海岸的 24 小时，必须抓取当天及“第二天”的 UTC 数据
next_date = target_date + timedelta(days=1)

# 生成供 CDS API 使用的去重日期列表（防止跨月、跨年报错）
years = list(set([target_date.strftime('%Y'), next_date.strftime('%Y')]))
months = list(set([target_date.strftime('%m'), next_date.strftime('%m')]))
days = list(set([target_date.strftime('%d'), next_date.strftime('%d')]))

# --- 2. 提交下载请求 ---
c = cdsapi.Client()
target_lat, target_lon = 47.46, -120.94  # 目标坐标 (High Ingalls)
filename = 'ingalls_weather_westcoast.nc'

print(f"正在向 Copernicus 获取跨越两天的 UTC 数据，以覆盖西海岸 {target_date_str} 全天...")

c.retrieve(
    'reanalysis-era5-single-levels',
    {
        'product_type': 'reanalysis',
        'format': 'netcdf',
        'variable': [
            '2m_temperature',
            '2m_dewpoint_temperature',
            'total_cloud_cover',
            'geopotential',  # 获取模型地形高度必需参数
        ],
        'year': years,
        'month': months,
        'day': days,
        'time': [f'{i:02d}:00' for i in range(24)],
        # 边界框: 北, 西, 南, 东
        'area': [47.6, -121.1, 47.3, -120.8], 
    },
    filename)

# --- 3. 数据加载与元数据解析 ---
ds = xr.open_dataset(filename)
# 自动寻找距离目标坐标最近的网格点
point_data = ds.sel(latitude=target_lat, longitude=target_lon, method='nearest')

grid_lat = float(point_data.latitude.values)
grid_lon = float(point_data.longitude.values)
distance_miles = calculate_distance_miles(target_lat, target_lon, grid_lat, grid_lon)

# 提取模型海拔 (ERA5 z 的单位是 m^2/s^2，需除以重力加速度)
z_val = float(point_data['z'].values.flatten()[0])
elevation_ft = (z_val / 9.80665) * 3.28084

# --- 4. 核心：时区转换与数据截断 ---
df = point_data.to_dataframe().reset_index()

# 兼容近实时数据 (ERA5T) 的 valid_time 和历史存档的 time 列名
time_col = 'valid_time' if 'valid_time' in df.columns else 'time'

# 过滤掉由于 expver (实验版本) 维度产生的空行
df = df.dropna(subset=['t2m'])

# a. 将时间列转为 Pandas Datetime 对象
df[time_col] = pd.to_datetime(df[time_col])

# b. 将无时区的 UTC 时间标记为 UTC，然后转换为西海岸时区
df['local_time'] = df[time_col].dt.tz_localize('UTC').dt.tz_convert(local_tz)

# c. 严格截断：只保留当地时间等于目标日期的那 24 小时数据
df = df[df['local_time'].dt.date == target_date].copy()

# --- 5. 物理量计算与格式化 ---
df['temp_c'] = df['t2m'] - 273.15
df['dew_point_c'] = df['d2m'] - 273.15
df['rh_percent'] = calculate_rh(df['temp_c'], df['dew_point_c'])
df['temp_f'] = df['temp_c'] * 9/5 + 32

output_df = df[['local_time', 'temp_f', 'rh_percent', 'tcc']].copy()
output_df['local_time'] = output_df['local_time'].dt.strftime('%H:%M') 
output_df['temp_f'] = output_df['temp_f'].round(1)
output_df['rh_percent'] = output_df['rh_percent'].round(1)
output_df['tcc'] = output_df['tcc'].round(2)

output_df.columns = ['Time(PT)', 'Temp(°F)', 'Humidity(%)', 'CloudCover(0-1)']

# --- 6. 打印结果 ---
print("\n" + "="*50)
print(f" 目标位置: High Ingalls (Lat: {target_lat}, Lon: {target_lon})")
print(f" 当地日期: {target_date_str} (Pacific Time)")
print("-" * 50)
print(f" [元数据解析]")
print(f" 匹配网格中心: Lat {grid_lat:.2f}, Lon {grid_lon:.2f}")
print(f" 距目标点距离: {distance_miles:.2f} 英里")
print(f" 模型海拔高度: {elevation_ft:.0f} 英尺")
print("=" * 50 + "\n")
print(output_df.to_string(index=False))
