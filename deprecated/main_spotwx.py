import argparse
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import timedelta
import math
from scipy.optimize import fsolve
import pytz
import sys

def es(T_c): return 6.112 * math.exp((17.67 * T_c) / (T_c + 243.5))
def psychrometric_eq(Tw_c, T_c, e, P_hpa): return es(Tw_c) - P_hpa * 6.66e-4 * (1 + 0.00115 * Tw_c) * (T_c - Tw_c) - e

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file_path", type=str, help="支持传入 .csv 或是之前下的 .tmp HTML")
    parser.add_argument("--days", type=float, default=3.0)
    parser.add_argument("--elevation_ft", type=float, default=10000.0)
    args = parser.parse_args()

    # 1. 智能解析文件：判断是直接传入了 CSV，还是网页源码
    try:
        if args.file_path.endswith('.csv'):
            df = pd.read_csv(args.file_path)
            df.columns = [str(c).strip().upper() for c in df.columns]
        else:
            dfs = pd.read_html(args.file_path)
            df = next((temp_df for temp_df in dfs if 'DATETIME' in [str(c).strip().upper() for c in temp_df.columns]), None)
            if df is not None: df.columns = [str(c).strip().upper() for c in df.columns]

        if df is None or 'TMP' not in df.columns or 'RH' not in df.columns:
            print("❌ 错误: 数据不包含必须的 'TMP' 或 'RH' 列。如果是 SpotWx，请直接在网页上点击下载 CSV 文件传入。")
            sys.exit(1)
    except ValueError:
        print("❌ 错误: 无法解析。请直接在 SpotWx 网页点击 'CSV' 下载文件，然后运行: python main_spotwx.py your_download.csv")
        sys.exit(1)

    # 后续逻辑不变 (时间过滤 -> 气压基准计算 -> 遍历计算湿球温度 -> 画图输出)
    pt_zone = pytz.timezone('America/Los_Angeles')
    df['DATETIME'] = pd.to_datetime(df['DATETIME'])
    if df['DATETIME'].dt.tz is None:
        df['DATETIME'] = df['DATETIME'].dt.tz_localize(pt_zone, ambiguous='NaT', nonexistent='NaT')
    
    df = df[df['DATETIME'] <= df['DATETIME'].iloc[0] + timedelta(days=args.days)].copy()

    P_hpa = 1013.25 * (1 - 2.25577e-5 * (args.elevation_ft * 0.3048))**5.25588
    
    wbs_f, temps_f = [], []
    for _, row in df.iterrows():
        t_c, rh = row['TMP'], row['RH']
        temps_f.append(t_c * 9.0 / 5.0 + 32)
        try:
            wbs_f.append(fsolve(psychrometric_eq, t_c, args=(t_c, es(t_c) * (rh / 100.0), P_hpa))[0] * 9.0 / 5.0 + 32)
        except:
            wbs_f.append(None)

    df['Air_Temp_F'], df['Adjusted_Wet_Bulb_F'] = temps_f, wbs_f

    # --- 下方的 matplotlib 画图部分保持和之前完全一样 ---
    # ...
    fig, ax = plt.subplots(figsize=(20, 7))
    ax.plot(df['DATETIME'], df['Adjusted_Wet_Bulb_F'], marker='o', color='teal', label=f'Adj. Wet Bulb Temp ({args.elevation_ft} ft)')
    ax.plot(df['DATETIME'], df['Air_Temp_F'], marker='.', color='orange', alpha=0.6, label='Air Temp')
    ax.axhline(y=32, color='red', linestyle='--', linewidth=2, label='Freezing Point (32°F)')
    ax.set_title(f"SpotWx Hourly Forecast (HRRR) - Elev: {args.elevation_ft} ft", fontsize=18)
    
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=6, tz=pt_zone))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:00', tz=pt_zone))
    ax.xaxis.set_minor_locator(mdates.HourLocator(interval=1, tz=pt_zone))
    ax.grid(True, which='both', color='gray', linestyle='--', alpha=0.5)
    
    plt.xticks(rotation=45, ha='right')
    plt.legend()
    plt.tight_layout()
    plt.savefig('spotwx_wbt_chart.png', dpi=150)
    print("🎉 图表生成完成！")

if __name__ == "__main__":
    main()
