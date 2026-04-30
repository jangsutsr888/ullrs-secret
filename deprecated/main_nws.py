import argparse
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import math
import pandas as pd
from scipy.optimize import fsolve
import pytz
import sys
import os

def es(T_c):
    """计算饱和水汽压 (hPa)"""
    return 6.112 * math.exp((17.67 * T_c) / (T_c + 243.5))

def psychrometric_eq(Tw_c, T_c, e, P_hpa):
    """干湿球方程，用于fsolve求解"""
    A = 6.66e-4
    return es(Tw_c) - P_hpa * A * (1 + 0.00115 * Tw_c) * (T_c - Tw_c) - e

def main():
    parser = argparse.ArgumentParser(description="根据 NWS XML 天气数据计算并绘制修正海拔后的湿球温度。")
    parser.add_argument("xml_path", type=str, help="输入的 weather.xml 文件路径")
    parser.add_argument("--days", type=float, default=3.0, help="需要绘制的天数 (默认: 3 天)")
    args = parser.parse_args()

    # 1. 加载并修复 XML
    if not os.path.exists(args.xml_path):
        print(f"错误: 找不到文件 {args.xml_path}")
        sys.exit(1)

    with open(args.xml_path, 'r', encoding='utf-8') as f:
        xml_data = f.read()

    # 修复 NWS XML 中经常出现的未转义 & 符号
    xml_data = xml_data.replace('&lon=', '&amp;lon=').replace('&FcstType=', '&amp;FcstType=')
    try:
        root = ET.fromstring(xml_data)
    except ET.ParseError as e:
        print(f"XML 解析失败: {e}")
        sys.exit(1)

    # 2. 提取海拔与标准气压
    height_elem = root.find('.//location/height')
    elevation_ft = float(height_elem.text) if height_elem is not None else 0.0
    elevation_m = elevation_ft * 0.3048
    P_hpa = 1013.25 * (1 - 2.25577e-5 * elevation_m)**5.25588
    print(f"检测到海拔: {elevation_ft} ft. 计算所得当地标准气压: {P_hpa:.2f} hPa")

    # 3. 提取时间、气温、相对湿度
    pt_zone = pytz.timezone('America/Los_Angeles')
    times, temps_f, rh_values = [], [], []
    time_layout_key = 'k-p1h-n1-0'
    
    for tl in root.findall('.//time-layout'):
        if tl.find('layout-key').text == time_layout_key:
            for st in tl.findall('start-valid-time'):
                dt_obj = datetime.fromisoformat(st.text)
                times.append(dt_obj.astimezone(pt_zone))
            break

    for temp in root.findall('.//parameters/temperature'):
        if temp.get('type') == 'hourly' and temp.get('time-layout') == time_layout_key:
            for v in temp.findall('value'):
                temps_f.append(float(v.text) if v.text is not None else None)
            break

    for rh in root.findall('.//parameters/humidity'):
        if rh.get('type') == 'relative' and rh.get('time-layout') == time_layout_key:
            for v in rh.findall('value'):
                rh_values.append(float(v.text) if v.text is not None else None)
            break

    # 确保列表长度一致
    min_len = min(len(times), len(temps_f), len(rh_values))
    times, temps_f, rh_values = times[:min_len], temps_f[:min_len], rh_values[:min_len]

    if not times:
        print("错误: 在 XML 中未找到有效的时间序列数据。")
        sys.exit(1)

    # 4. 根据传入的天数过滤数据
    start_time = times[0]
    cutoff_date = start_time + timedelta(days=args.days)
    
    f_times, f_temps, f_rhs = [], [], []
    for t, temp, rh in zip(times, temps_f, rh_values):
        if t <= cutoff_date:
            f_times.append(t)
            f_temps.append(temp)
            f_rhs.append(rh)

    # 5. 计算修正后的湿球温度
    f_adjusted_wbs = []
    for t_f, rh in zip(f_temps, f_rhs):
        if t_f is not None and rh is not None:
            t_c = (t_f - 32) * 5.0 / 9.0
            e_actual = es(t_c) * (rh / 100.0)
            try:
                tw_c_adj = fsolve(psychrometric_eq, t_c, args=(t_c, e_actual, P_hpa))[0]
                f_adjusted_wbs.append(tw_c_adj * 9.0 / 5.0 + 32)
            except:
                f_adjusted_wbs.append(None)
        else:
            f_adjusted_wbs.append(None)

    # 6. 绘图
    fig, ax = plt.subplots(figsize=(20, 7))

    # [新增] 过滤出有效的湿球温度数据，用于计算交点和积分
    valid_data = [(t, w) for t, w in zip(f_times, f_adjusted_wbs) if w is not None]
    if valid_data:
        v_times = [d[0] for d in valid_data]
        v_wbs = [d[1] for d in valid_data]
        
        segments = []
        current_segment = [(v_times[0], v_wbs[0])]
        crossing_times = []
        
        # 寻找与 32°F 的精确交点并切分数据段
        for i in range(len(v_wbs) - 1):
            t1, w1 = v_times[i], v_wbs[i]
            t2, w2 = v_times[i+1], v_wbs[i+1]
            
            # 判断是否穿过 32°F 零度线
            if (w1 - 32) * (w2 - 32) < 0:
                # 发生穿透，使用线性插值计算精确的交点时间
                ratio = (32 - w1) / (w2 - w1)
                delta_t = t2 - t1
                t_cross = t1 + delta_t * ratio
                
                crossing_times.append(t_cross)
                current_segment.append((t_cross, 32.0))
                segments.append(current_segment)
                # 开启新的一段
                current_segment = [(t_cross, 32.0), (t2, w2)]
            else:
                current_segment.append((t2, w2))
        segments.append(current_segment)

        # 获取坐标轴的混合变换：X 为实际数据坐标，Y 为 0~1 的相对坐标
        # 这样可以确保文本永远贴在图表的绝对顶部或底部，不受温度数值极值影响
        trans = ax.get_xaxis_transform()

        # 遍历所有线段，计算积分并填充颜色
        for seg in segments:
            if len(seg) < 2:
                continue
                
            seg_times = [p[0] for p in seg]
            seg_wbs = [p[1] for p in seg]
            
            # 使用梯形法则计算这段区域的面积 (华氏度·小时)
            integral = 0.0
            for i in range(len(seg)-1):
                dt_hours = (seg_times[i+1] - seg_times[i]).total_seconds() / 3600.0
                integral += 0.5 * abs((seg_wbs[i] - 32) + (seg_wbs[i+1] - 32)) * dt_hours
                
            # 判断这段积分是融化还是冻结
            mid_idx = len(seg) // 2
            is_melt = seg_wbs[mid_idx] > 32.0
            
            # 找到时间的中点，用于放置文本框
            mid_time = seg_times[0] + (seg_times[-1] - seg_times[0]) / 2
            
            # 只有当积分 > 0.5 时才进行标注，避免微小波动的文本相互重叠
            if integral > 0.5:
                if is_melt:
                    # 融化区：红色填充，文本放顶部
                    ax.fill_between(seg_times, seg_wbs, 32, color='red', alpha=0.15, linewidth=0, zorder=1)
                    ax.text(mid_time, 0.96, f"melting\n+{integral:.1f}", transform=trans, 
                            color='darkred', ha='center', va='top', fontsize=12, fontweight='bold',
                            bbox=dict(facecolor='white', alpha=0.6, edgecolor='none', pad=2), zorder=6)
                else:
                    # 冻结区：蓝色填充，文本放底部
                    ax.fill_between(seg_times, seg_wbs, 32, color='dodgerblue', alpha=0.15, linewidth=0, zorder=1)
                    ax.text(mid_time, 0.04, f"freezing\n-{integral:.1f}", transform=trans, 
                            color='darkblue', ha='center', va='bottom', fontsize=12, fontweight='bold',
                            bbox=dict(facecolor='white', alpha=0.6, edgecolor='none', pad=2), zorder=6)

        # 绘制划分周期的垂直虚线
        for ct in crossing_times:
            ax.axvline(x=ct, color='gray', linestyle='-.', alpha=0.8, linewidth=1.5, zorder=2)

    # 绘制基础温度曲线 (加入 zorder 保证线在填充图层之上)
    ax.plot(f_times, f_adjusted_wbs, marker='o', markersize=5, linestyle='-', color='teal', label='Altitude-Adjusted Wet Bulb Temp', zorder=4)
    ax.plot(f_times, f_temps, marker='.', markersize=4, linestyle='-', color='orange', alpha=0.6, label='Air Temp', zorder=3)
    ax.axhline(y=32, color='red', linestyle='--', linewidth=2, label='Freezing Point (32°F)', zorder=5)

    ax.set_title(f'Hourly Wet Bulb vs Air Temp ({args.days} Days Forecast) - Elev: {elevation_ft} ft\nTimezone: US Pacific Time (PT)', fontsize=18)
    ax.set_ylabel('Temperature (°F)', fontsize=14)

    # X轴刻度设置
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=6, tz=pt_zone))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:00', tz=pt_zone))
    ax.xaxis.set_minor_locator(mdates.HourLocator(interval=1, tz=pt_zone))

    ax.grid(True, which='major', axis='x', color='gray', linestyle='-', alpha=0.6)
    ax.grid(True, which='minor', axis='x', color='gray', linestyle=':', alpha=0.4)
    ax.grid(True, which='major', axis='y', color='gray', linestyle='--', alpha=0.5)

    # 根据数据动态调整一下 Y 轴上下限，给顶底部的文字留出空间
    if valid_data:
        ax.set_ylim(bottom=min(v_wbs + f_temps) - 4, top=max(v_wbs + f_temps) + 4)

    plt.xticks(rotation=45, ha='right', fontsize=12)
    plt.yticks(fontsize=12)
    plt.legend(fontsize=14, loc='upper left')
    plt.tight_layout()

    # === 从这行开始，替换掉你原代码的 plt.tight_layout() 及之后的保存部分 ===

    # 1. 下“猛药”：把画布拉得更高 (+4.5英寸)
    current_size = fig.get_size_inches()
    fig.set_size_inches(current_size[0], current_size[1] + 4.5) 
    
    # 把主图表的底部边界强行推到整个画幅 45% 的高度 (给 X 轴标签和手册留出接近一半的画幅)
    plt.subplots_adjust(bottom=0.45)

    ax.legend(loc='upper left', bbox_to_anchor=(0, -0.25), fontsize=12, frameon=True)

    # 2. 全英文手册内容 (保持纯 ASCII)
    manual_content = (
        "Snow Quality Reference Manual\n"
        "----------------------------------------------------------------------------------------------------------------------\n"
        "[North Aspect Powder]                                   [South Aspect Corn Cycle]\n"
        " * Top Tier: WBTDH 0 ~ 5 F-hrs                           * Target: Snow Depth(inch) x K (PNW K=3, Rockies K=5)\n"
        " * Critical: WBTDH 15 ~ 20 F-hrs                         * Prime Corn: Current Day WBTDH 0 ~ 3 F-hrs\n"
        " * Isothermal (Ruined): WBTDH > 35 F-hrs                 * Sticky/Grabby Warning: Current Day WBTDH 5 ~ 8 F-hrs\n"
        "----------------------------------------------------------------------------------------------------------------------\n"
        "[Overnight Recovery & Safety]                           [Reset Protocol (Isothermal State)]\n"
        " * Freeze Failure: Night WBFDH < 10 F-hrs (Unsafe)       * False Recovery: Night WBFDH < 20 F-hrs (Breakable crust)\n"
        " * Energy Deficit: WBFDH < 0.5 * WBTDH (Deteriorating)   * Initial Stabilization: Night WBFDH 30 ~ 40 F-hrs\n"
        "                                                         * Full Reset: Night WBFDH > 50 F-hrs (Structure restored)\n"
        "----------------------------------------------------------------------------------------------------------------------\n"
        "Note: WBTDH = Melt Integral (T > 32 F)  |  WBFDH = Freeze Integral (T < 32 F)"
    )

    # 3. 贴在最底部，避开斜向下的时间标签
    fig.text(0.5, 0.01, manual_content, ha='center', va='bottom', fontsize=11,
             family='monospace', linespacing=1.6,
             bbox=dict(facecolor='ghostwhite', alpha=0.9, edgecolor='lightgray', boxstyle='round,pad=1'))

    # 4. 强制包含所有边缘
    output_filename = 'forecast_chart.png'
    plt.savefig(output_filename, dpi=150, bbox_inches='tight')
    print(f"图表已成功保存为: {output_filename}")

    # 保存数据到 CSV 
    df = pd.DataFrame({
        'Time_PT': [t.strftime('%Y-%m-%d %H:%M:%S') for t in f_times],
        'Air_Temp_F': f_temps,
        'Relative_Humidity_Pct': f_rhs,
        'Adjusted_Wet_Bulb_F': f_adjusted_wbs
    })
    df.to_csv('forecast_data.csv', index=False)
    print("数据已成功保存为: forecast_data.csv")
    
    # === 替换到这里结束 ===

    output_filename = 'forecast_chart.png'
    plt.savefig(output_filename, dpi=150)
    print(f"图表已成功保存为: {output_filename}")

    # 保存数据到 CSV
    df = pd.DataFrame({
        'Time_PT': [t.strftime('%Y-%m-%d %H:%M:%S') for t in f_times],
        'Air_Temp_F': f_temps,
        'Relative_Humidity_Pct': f_rhs,
        'Adjusted_Wet_Bulb_F': f_adjusted_wbs
    })
    df.to_csv('forecast_data.csv', index=False)
    print("数据已成功保存为: forecast_data.csv")

if __name__ == "__main__":
    main()
