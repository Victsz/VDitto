"""
T5: 验证 Pillow 能处理 Ditto DB 中的 DIB 图片数据
运行: python tests/feasi/test_dib_image.py <path_to_Ditto.db>
操作: 从 Ditto DB 读取一条 CF_DIB 记录，转为 PNG 并保存
"""
import sys
import struct
import sqlite3
from pathlib import Path


def dib_to_png(dib_data: bytes) -> bytes:
    """将 DIB (BITMAPINFOHEADER + pixels) 转为 PNG bytes"""
    from PIL import Image
    import io

    # 解析 BITMAPINFOHEADER (40 bytes)
    biSize, biWidth, biHeight, biPlanes, biBitCount = struct.unpack_from("<iiiHH", dib_data, 0)
    biCompression = struct.unpack_from("<I", dib_data, 16)[0]

    print(f"  DIB header: {biWidth}x{biHeight}, {biBitCount}bit, compression={biCompression}")

    # DIB 数据不含 BM 文件头，需要构造 BMP
    # BMP = BM header(14) + DIB data
    dib_offset = 14  # BMP file header size
    image_data = dib_data

    # 构造 BMP 文件头
    bmp_header = struct.pack(
        "<2sIHHI",
        b"BM",
        dib_offset + len(image_data),  # file size
        0,  # reserved1
        0,  # reserved2
        dib_offset,  # pixel data offset = 14 + BITMAPINFOHEADER size
    )

    bmp_data = bmp_header + image_data
    img = Image.open(io.BytesIO(bmp_data))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def main():
    db_path = sys.argv[1] if len(sys.argv) > 1 else "test-Ditto.db"
    db_path = Path(db_path)

    if not db_path.exists():
        print(f"[FAIL] DB not found: {db_path}")
        return

    conn = sqlite3.connect(str(db_path))

    # 找一条含 CF_DIB 的记录
    row = conn.execute(
        "SELECT d.lParentID, d.ooData "
        "FROM Data d "
        "WHERE d.strClipBoardFormat = 'CF_DIB' "
        "LIMIT 1"
    ).fetchone()

    if not row:
        print("[WARN] No CF_DIB found in DB")
        conn.close()
        return

    parent_id, dib_blob = row
    print(f"[OK] Found DIB data: parent_id={parent_id}, size={len(dib_blob)} bytes")

    try:
        png_data = dib_to_png(dib_blob)
        out_path = Path(__file__).parent / "test_output_dib.png"
        out_path.write_bytes(png_data)
        print(f"[OK] DIB → PNG converted: {len(png_data)} bytes")
        print(f"[OK] Saved to: {out_path}")
    except Exception as e:
        print(f"[FAIL] DIB conversion failed: {e}")
        import traceback
        traceback.print_exc()

    conn.close()
    print("\n=== T5 DIB Image: DONE ===")


if __name__ == "__main__":
    main()
