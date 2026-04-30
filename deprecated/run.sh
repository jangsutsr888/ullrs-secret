#!/bin/bash

# 1. 参数校验与说明
if [ -z "$1" ]; then
    echo "❌ 错误: 缺少网址参数。"
    echo "用法: ./run.sh <URL> [预测天数] [海拔_英尺(仅SpotWx需要)]"
    echo "提示: 请务必用双引号把 URL 括起来，防止终端截断 '&' 符号！"
    exit 1
fi

URL="$1"
DAYS="${2:-3}"
# 如果未输入第三个参数，海拔默认设为 10000 ft (Muir 营地基准)
ELEVATION="${3:-10000}" 
TEMP_FILE="downloaded_data.tmp"

echo "========================================"
echo "  🏔️  大山滑雪 WBT 分析自动化工具"
echo "========================================"
echo "正在从服务器拉取数据..."

# 2. 抓取数据 (伪装 User-Agent 防止被防火墙拦截)
curl -s -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)" "$URL" -o "$TEMP_FILE"

if [ ! -s "$TEMP_FILE" ]; then
    echo "❌ 下载失败或文件为空，请检查网络或 URL。"
    exit 1
fi

# 3. 智能判断来源，分配处理逻辑
if [[ "$URL" == *"forecast.weather.gov"* ]]; then
    echo "✅ 识别到 NWS XML 数据源"
    TARGET_SCRIPT="main_nws.py"
    EXTRA_ARGS="" # NWS 数据本身包含高程，无需外部传入
elif [[ "$URL" == *"spotwx.com"* ]]; then
    echo "✅ 识别到 SpotWx HTML 数据源 (模型: HRDPS)"
    TARGET_SCRIPT="main_spotwx.py"
    EXTRA_ARGS="--elevation_ft $ELEVATION"
else
    echo "❌ 无法识别的 URL 格式，目前仅支持 weather.gov 和 spotwx.com。"
    rm "$TEMP_FILE"
    exit 1
fi

# 4. 虚拟环境检查与包安装
if [ ! -d "venv" ]; then
    echo "正在创建 Python 虚拟环境 (venv)..."
    python3 -m venv venv
fi
source venv/bin/activate
echo "正在检查依赖包..."
pip install -r requirements.txt --quiet

# 5. 执行 Python 绘图程序
echo "🚀 开始生成图表..."
python "$TARGET_SCRIPT" "$TEMP_FILE" --days "$DAYS" $EXTRA_ARGS

deactivate
# 清理临时下载文件
rm "$TEMP_FILE"
echo "🎉 执行完成！请查看生成的图表和 CSV 文件。"
