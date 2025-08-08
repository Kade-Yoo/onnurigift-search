from fastapi import FastAPI, Query
from pydantic import BaseModel
import os
import sqlite3


class HealthResponse(BaseModel):
    status: str


def get_db_path() -> str:
    return os.getenv("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "..", "data", "onnuri.db"))


def get_connection():
    db_path = os.path.abspath(get_db_path())
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


app = FastAPI(title="Onnuri Store Search API")


@app.get("/health", response_model=HealthResponse)
def health():
    return {"status": "ok"}


@app.get("/stores")
def list_stores(
    q: str | None = Query(None, description="가맹점명/주소/취급품목 통합검색"),
    market: str | None = None,
    address: str | None = None,
    category: str | None = None,
    card: bool | None = Query(None, description="충전식 카드 취급여부"),
    paper: bool | None = Query(None, description="지류 취급여부"),
    mobile: bool | None = Query(None, description="모바일 취급여부"),
    year: int | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
):
    offset = (page - 1) * size
    filters = []
    params: list[object] = []

    if q:
        filters.append("(store_name LIKE ? OR address LIKE ? OR category LIKE ?)")
        like = f"%{q.strip()}%"
        params.extend([like, like, like])
    if market:
        filters.append("market_name LIKE ?")
        params.append(f"%{market.strip()}%")
    if address:
        filters.append("address LIKE ?")
        params.append(f"%{address.strip()}%")
    if category:
        filters.append("category LIKE ?")
        params.append(f"%{category.strip()}%")
    if card is not None:
        filters.append("card_yn = ?")
        params.append("Y" if card else "N")
    if paper is not None:
        filters.append("paper_yn = ?")
        params.append("Y" if paper else "N")
    if mobile is not None:
        filters.append("mobile_yn = ?")
        params.append("Y" if mobile else "N")
    if year is not None:
        filters.append("year = ?")
        params.append(int(year))

    where_sql = f"WHERE {' AND '.join(filters)}" if filters else ""
    sql = f"""
        SELECT id, store_name, market_name, address, category, card_yn, paper_yn, mobile_yn, year
        FROM stores
        {where_sql}
        ORDER BY id
        LIMIT ? OFFSET ?
    """

    count_sql = f"SELECT COUNT(1) AS cnt FROM stores {where_sql}"
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(count_sql, params)
        total = cur.fetchone()[0]

        cur.execute(sql, [*params, size, offset])
        rows = [dict(row) for row in cur.fetchall()]

    return {
        "page": page,
        "size": size,
        "total": total,
        "items": rows,
    }

