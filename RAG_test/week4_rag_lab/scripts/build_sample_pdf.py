"""从讲义 PDF 抽取若干页生成 `data/sample.pdf`（需已安装 pymupdf）。"""

from __future__ import annotations

from pathlib import Path

import fitz  # PyMuPDF

# 与 `data/` 目录下的文件名一致
SOURCE_PDF = "磁阻效应实验讲义(第3版)-邹斌.pdf"
# 整本较大，只取前几页作为最小 Pipeline 的示例输入，减小索引时间与体积
MAX_PAGES = 5


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    data = root / "data"
    src = data / SOURCE_PDF
    out = data / "sample.pdf"
    data.mkdir(parents=True, exist_ok=True)

    if not src.is_file():
        raise SystemExit(
            f"未找到源 PDF：{src}\n"
            f"请将《{SOURCE_PDF}》放在 data 目录下后再运行本脚本。"
        )

    src_doc = fitz.open(str(src))
    try:
        n = min(MAX_PAGES, len(src_doc))
        out_doc = fitz.open()
        try:
            out_doc.insert_pdf(src_doc, from_page=0, to_page=n - 1)
            out_doc.save(str(out))
        finally:
            out_doc.close()
    finally:
        src_doc.close()

    print(f"已从「{SOURCE_PDF}」抽取前 {n} 页 → {out}")


if __name__ == "__main__":
    main()
