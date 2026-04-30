#!/bin/bash

if [ -z "$1" ] || [ -z "$2" ]; then
    echo "错误: 缺少参数。"
    echo "用法: ./scripts/run.sh <数据源类型> <URL或文件路径> [预测天数]"
    echo "示例: ./scripts/run.sh nws \"https://forecast.weather.gov/...\" 3"
    exit 1
fi

TYPE="$1"
SOURCE="$2"
DAYS="${3:-3}"
JSON_FILE="weather_data.json"

echo "========================================"
echo "  大山滑雪 WBT 分析自动化工具"
echo "========================================"
echo "正在导入数据 (类型: $TYPE)..."

python -m wetbulb_calc.import_data "$TYPE" "$SOURCE" -o "$JSON_FILE"
if [ $? -ne 0 ]; then
    echo "数据导入失败。"
    exit 1
fi

echo "正在计算湿球温度并生成图表..."
python -m wetbulb_calc.plot "$JSON_FILE" --days "$DAYS"

echo "执行完成！请查看生成的图表和 CSV 文件。"
