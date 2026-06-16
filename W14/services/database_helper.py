"""sqlite3 기반의 간단한 CRUD ORM 헬퍼.

테이블/컬럼 이름은 코드 안의 상수이므로 문자열로 조립하고,
파일·사용자에게서 온 값은 모두 ? 플레이스홀더로 바인딩해 SQL 인젝션을 막는다.
"""

import sqlite3
from decimal import Decimal

from core.utils import Utils

# SQLite에는 DECIMAL 타입이 없어 TEXT 컬럼에 문자열로 저장한다.
# Decimal을 그대로 넘겨도 정확한 10진 문자열로 저장되도록 어댑터를 등록한다.
sqlite3.register_adapter(Decimal, str)


class DatabaseHelper:
    """sqlite3 커넥션과 기본 CRUD 쿼리를 감싸는 헬퍼."""

    def __init__(self, db_file: str) -> None:
        """헬퍼를 초기화한다(아직 연결하지는 않는다)."""
        self.db_path = Utils.set_file_path(db_file)
        self.conn: sqlite3.Connection | None = None

    def __enter__(self) -> 'DatabaseHelper':
        """with 진입 시 연결을 연다."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """with 종료 시 연결을 닫는다."""
        self.close()

    def connect(self) -> None:
        """데이터베이스에 연결한다."""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row  # 컬럼명으로 값에 접근할 수 있게 한다
        Utils.print_log('DB', '데이터베이스 연결: ' + str(self.db_path))

    def close(self) -> None:
        """연결을 닫는다."""
        if self.conn is not None:
            self.conn.close()
            self.conn = None
            Utils.print_log('DB', '데이터베이스 연결을 종료했습니다.')

    def create_table(self, table: str, columns: dict[str, str], drop_if_exists: bool = False) -> None:
        """컬럼 정의(dict)로 테이블을 생성한다.

        columns 예시: {'id': 'INTEGER PRIMARY KEY', 'name': 'TEXT NOT NULL'}
        drop_if_exists가 True면 기존 테이블을 먼저 삭제한다.
        """
        if drop_if_exists:
            self.conn.execute('DROP TABLE IF EXISTS ' + table)
        column_ddl = ', '.join(name + ' ' + ddl for name, ddl in columns.items())
        self.conn.execute('CREATE TABLE IF NOT EXISTS ' + table + ' (' + column_ddl + ')')
        self.conn.commit()

    def insert(self, table: str, data: dict) -> int:
        """dict 한 건을 INSERT 하고 새 행의 기본키(rowid)를 반환한다."""
        columns = list(data.keys())
        placeholders = ', '.join('?' for _ in columns)
        query = ('INSERT INTO ' + table + ' (' + ', '.join(columns) + ') '
                 + 'VALUES (' + placeholders + ')')
        cursor = self.conn.execute(query, tuple(data.values()))
        self.conn.commit()
        return cursor.lastrowid

    def insert_many(self, table: str, columns: tuple, rows: list[tuple]) -> None:
        """여러 행을 한 번에 INSERT 한다(대량 적재용)."""
        placeholders = ', '.join('?' for _ in columns)
        query = ('INSERT INTO ' + table + ' (' + ', '.join(columns) + ') '
                 + 'VALUES (' + placeholders + ')')
        self.conn.executemany(query, rows)
        self.conn.commit()

    def select(self, table: str, columns: str = '*', where: str | None = None,
               params: tuple = (), order_by: str | None = None) -> list[sqlite3.Row]:
        """조건에 맞는 행들을 조회해 리스트로 반환한다."""
        query = 'SELECT ' + columns + ' FROM ' + table
        if where is not None:
            query += ' WHERE ' + where
        if order_by is not None:
            query += ' ORDER BY ' + order_by
        cursor = self.conn.execute(query, params)
        return cursor.fetchall()

    def update(self, table: str, data: dict, where: str, params: tuple = ()) -> int:
        """조건에 맞는 행을 수정하고 변경된 행 수를 반환한다."""
        set_clause = ', '.join(column + ' = ?' for column in data)
        query = 'UPDATE ' + table + ' SET ' + set_clause + ' WHERE ' + where
        cursor = self.conn.execute(query, tuple(data.values()) + tuple(params))
        self.conn.commit()
        return cursor.rowcount

    def delete(self, table: str, where: str | None = None, params: tuple = ()) -> int:
        """조건에 맞는 행을 삭제하고 삭제된 행 수를 반환한다(where 없으면 전체 삭제)."""
        query = 'DELETE FROM ' + table
        if where is not None:
            query += ' WHERE ' + where
        cursor = self.conn.execute(query, params)
        self.conn.commit()
        return cursor.rowcount

    def count(self, table: str) -> int:
        """테이블의 전체 행 수를 반환한다."""
        cursor = self.conn.execute('SELECT COUNT(*) FROM ' + table)
        return cursor.fetchone()[0]
