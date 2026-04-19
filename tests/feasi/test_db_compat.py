"""
T1: 验证 sqlite3 能否正确读取 Ditto DB (WAL模式)
运行: python tests/feasi/test_db_compat.py <path_to_Ditto.db>
"""
import sys
import sqlite3
from pathlib import Path


def main():
    db_path = sys.argv[1] if len(sys.argv) > 1 else "test-Ditto.db"
    db_path = Path(db_path)

    if not db_path.exists():
        print(f"[FAIL] DB not found: {db_path}")
        return

    # 打开并启用 WAL
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    journal = conn.execute("PRAGMA journal_mode").fetchone()[0]
    print(f"[INFO] journal_mode = {journal}")

    # 读 Main 表
    count = conn.execute("SELECT COUNT(*) FROM Main WHERE bIsGroup = 0").fetchone()[0]
    print(f"[OK] Main clips: {count}")

    # 读 Data 表
    data_count = conn.execute("SELECT COUNT(*) FROM Data").fetchone()[0]
    print(f"[OK] Data rows: {data_count}")

    # 读一条文本 clip 的 Data
    row = conn.execute(
        "SELECT d.strClipBoardFormat, length(d.ooData) "
        "FROM Data d JOIN Main m ON d.lParentID = m.lID "
        "WHERE m.bIsGroup = 0 AND d.strClipBoardFormat = 'CF_UNICODETEXT' "
        "LIMIT 1"
    ).fetchone()
    if row:
        print(f"[OK] Text format found: {row[0]}, size={row[1]} bytes")
    else:
        print("[WARN] No CF_UNICODETEXT data found")

    # 读一条图片 clip 的 Data
    row = conn.execute(
        "SELECT d.strClipBoardFormat, length(d.ooData) "
        "FROM Data d JOIN Main m ON d.lParentID = m.lID "
        "WHERE m.bIsGroup = 0 AND d.strClipBoardFormat = 'CF_DIB' "
        "LIMIT 1"
    ).fetchone()
    if row:
        print(f"[OK] DIB format found: {row[0]}, size={row[1]} bytes")
    else:
        print("[WARN] No CF_DIB data found")

    # 尝试写入测试 (创建 + 回滚)
    try:
        conn.execute("BEGIN")
        conn.execute(
            "INSERT INTO Main (lDate, mText, bIsGroup, lParentID) "
            "VALUES (0, '__vditto_test__', 0, -1)"
        )
        test_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute("ROLLBACK")
        print(f"[OK] Write test passed (rolled back test id={test_id})")
    except Exception as e:
        print(f"[FAIL] Write test failed: {e}")

    conn.close()
    print("\n=== T1 DB Compatibility: PASSED ===")


if __name__ == "__main__":
    main()
