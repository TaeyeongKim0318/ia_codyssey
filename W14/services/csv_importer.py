"""CSV 백업 데이터를 스트리밍 방식으로 읽어 데이터베이스에 적재하는 서비스."""

import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation

from core.config import CHUNK_SIZE, CSV_FILE, TABLE_NAME
from core.utils import Utils
from services.database_helper import DatabaseHelper


class CsvImporter:
    """mars_weathers_data.CSV를 읽어 mars_weather 테이블에 적재한다."""

    # 테이블 스키마. weather_id는 자동 증가 기본키라 INSERT 대상에서 제외한다.
    TABLE_SCHEMA = {
        'weather_id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
        'mars_date': 'TEXT NOT NULL',
        'temp': 'TEXT NOT NULL',       # SQLite엔 DECIMAL이 없어 정확한 값을 TEXT로 저장
        'storm': 'INTEGER NOT NULL',
    }
    INSERT_COLUMNS = ('mars_date', 'temp', 'storm')
    DATE_FORMAT = '%Y-%m-%d'

    def __init__(self, db: DatabaseHelper, csv_file: str = CSV_FILE) -> None:
        """적재기를 초기화한다."""
        self.db = db
        self.csv_path = Utils.set_file_path(csv_file)

    def run(self) -> None:
        """테이블을 새로 만들고 CSV 내용을 적재한 뒤 결과를 보고한다."""
        if not self.csv_path.exists():
            Utils.print_log('오류', self.csv_path.name + ' 파일을 찾을 수 없습니다.')
            return

        # 같은 백업을 다시 적재해도 결과가 일정하도록 테이블을 새로 만든다.
        self.db.create_table(TABLE_NAME, self.TABLE_SCHEMA, drop_if_exists=True)
        Utils.print_log('DB', TABLE_NAME + ' 테이블 생성 완료')

        inserted, skipped = self._import_rows()

        message = '총 ' + str(inserted) + '건 적재 완료'
        if skipped:
            message += ' (형식 오류로 건너뜀 ' + str(skipped) + '건)'
        Utils.print_log('적재', message)

    def _import_rows(self) -> tuple[int, int]:
        """CSV를 한 줄씩 읽어 청크 단위로 INSERT 하고 (적재 수, 건너뛴 수)를 반환한다."""
        inserted = 0
        skipped = 0
        buffer: list[tuple] = []

        # utf-8-sig: 혹시 모를 BOM을 제거해 헤더 이름이 깨지지 않게 한다.
        # DictReader는 파일을 통째로 올리지 않고 한 행씩 흘려보내므로 큰 백업에도 안전하다.
        with open(self.csv_path, 'r', encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            for line_no, raw in enumerate(reader, start=2):  # 헤더 다음 줄(2행)부터 데이터
                row = self._parse_row(raw)
                if row is None:
                    skipped += 1
                    Utils.print_log('경고', str(line_no) + '행을 건너뜁니다(형식 오류).')
                    continue

                buffer.append(row)
                if len(buffer) >= CHUNK_SIZE:  # 일정량 모이면 한 번에 INSERT 한다
                    self.db.insert_many(TABLE_NAME, self.INSERT_COLUMNS, buffer)
                    inserted += len(buffer)
                    buffer.clear()

            if buffer:  # 청크에 못 미치고 남은 행 처리
                self.db.insert_many(TABLE_NAME, self.INSERT_COLUMNS, buffer)
                inserted += len(buffer)

        return inserted, skipped

    def _parse_row(self, raw: dict) -> tuple | None:
        """CSV 한 행을 검증/변환해 (mars_date, temp, storm) 튜플로 반환한다.

        값이 비었거나 형식이 올바르지 않으면 None을 반환한다.
        """
        try:
            mars_date = raw['mars_date'].strip()
            datetime.strptime(mars_date, self.DATE_FORMAT)  # 날짜 형식이 맞는지 검증
            temp = Decimal(raw['temp'].strip())             # 정확한 10진수로 변환(검증 겸용)
            storm = int(raw['storm'].strip())
        except (AttributeError, KeyError, ValueError, InvalidOperation):
            return None
        return (mars_date, temp, storm)
