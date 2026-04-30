"""CLI entry point for importing weather data into standard JSON format."""

import argparse
import json
import sys

from .importers import get_importer, list_importers


def main():
    parser = argparse.ArgumentParser(
        description="将天气数据导入为标准 JSON 格式。"
    )
    parser.add_argument("importer", choices=list_importers(),
                        help="数据源类型 (e.g. nws)")
    parser.add_argument("source", help="数据源 (URL 或本地文件路径)")
    parser.add_argument("-o", "--output", default="weather_data.json",
                        help="输出 JSON 文件 (默认: weather_data.json)")
    args = parser.parse_args()

    importer = get_importer(args.importer)
    data = importer(args.source)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    n = len(data.get("observations", []))
    print(f"已导入 {n} 条观测数据 → {args.output}")


if __name__ == "__main__":
    main()
