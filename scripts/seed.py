import csv
import os
import sqlite3
from datetime import datetime
from typing import Iterable

from dotenv import load_dotenv


load_dotenv()


CSV_SOURCE_PATH = os.getenv("CSV_SOURCE_PATH")
DATABASE_PATH = os.getenv(
    "DATABASE_PATH", os.path.join(os.path.dirname(__file__), "..", "data", "onnuri.db")
)


def get_connection() -> sqlite3.Connection:
    db_path = os.path.abspath(DATABASE_PATH)
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        PRAGMA journal_mode=WAL;
        PRAGMA synchronous=NORMAL;

        CREATE TABLE IF NOT EXISTS stores (
            id INTEGER PRIMARY KEY,
            store_name TEXT NOT NULL,
            market_name TEXT,
            address TEXT,
            category TEXT,
            card_yn TEXT CHECK(card_yn IN ('Y','N')),
            paper_yn TEXT CHECK(paper_yn IN ('Y','N')),
            mobile_yn TEXT CHECK(mobile_yn IN ('Y','N')),
            year INTEGER,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_stores_market ON stores(market_name);
        CREATE INDEX IF NOT EXISTS idx_stores_address ON stores(address);
        CREATE INDEX IF NOT EXISTS idx_stores_category ON stores(category);
        CREATE INDEX IF NOT EXISTS idx_stores_year ON stores(year);
        CREATE INDEX IF NOT EXISTS idx_stores_card ON stores(card_yn);
        CREATE INDEX IF NOT EXISTS idx_stores_paper ON stores(paper_yn);
        CREATE INDEX IF NOT EXISTS idx_stores_mobile ON stores(mobile_yn);
        """
    )


def normalize_bool(value: str) -> str:
    v = (value or "").strip()
    if v in {"Y", "y", "1", "T", "t", "true", "True", "예", "가능"}:
        return "Y"
    if v in {"N", "n", "0", "F", "f", "false", "False", "아니오", "불가"}:
        return "N"
    return "N"


def read_csv_rows(path: str) -> Iterable[dict]:
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield row


def map_row(row: dict) -> dict:
    # 지원 컬럼명: 가맹점명, 소속 시장명(또는 상점가), 소재지, 취급품목, 충전식 카드 취급여부, 지류 취급여부, 모바일 취급여부, 등록년도
    return {
        "store_name": (row.get("가맹점명") or row.get("가맹점명 ") or "").strip(),
        "market_name": (row.get("소속 시장명(또는 상점가)") or "").strip(),
        "address": (row.get("소재지") or "").strip(),
        "category": (row.get("취급품목") or "").strip(),
        "card_yn": normalize_bool(row.get("충전식 카드 취급여부") or ""),
        "paper_yn": normalize_bool(row.get("지류 취급여부") or ""),
        "mobile_yn": normalize_bool(row.get("모바일 취급여부") or ""),
        "year": int(row.get("등록년도") or 0) or None,
    }


def bulk_upsert(conn: sqlite3.Connection, items: Iterable[dict]) -> int:
    now = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    cursor = conn.cursor()
    count = 0
    for item in items:
        if not item["store_name"] and not item["address"]:
            continue
        cursor.execute(
            """
            INSERT INTO stores (store_name, market_name, address, category, card_yn, paper_yn, mobile_yn, year, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?)
            """,
            [
                item["store_name"],
                item["market_name"],
                item["address"],
                item["category"],
                item["card_yn"],
                item["paper_yn"],
                item["mobile_yn"],
                item["year"],
                now,
                now,
            ],
        )
        count += 1
    conn.commit()
    return count


def main():
    if not CSV_SOURCE_PATH:
        raise SystemExit("CSV_SOURCE_PATH 환경변수를 설정하세요. (다운로드 받은 CSV 경로)")
    if not os.path.exists(CSV_SOURCE_PATH):
        raise SystemExit(f"CSV 파일을 찾을 수 없습니다: {CSV_SOURCE_PATH}")

    with get_connection() as conn:
        init_schema(conn)
        rows = (map_row(r) for r in read_csv_rows(CSV_SOURCE_PATH))
        inserted = bulk_upsert(conn, rows)
        print(f"Inserted rows: {inserted}")


if __name__ == "__main__":
    main()

