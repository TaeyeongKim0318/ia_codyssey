"""화성 날씨 백업 CSV를 SQLite DB에 적재하고 요약 그래프를 PNG로 저장하는 진입점."""

from core.config import CHART_IMAGE, CSV_FILE, DB_FILE, REQUIREMENTS_FILE, TABLE_IMAGE
from core.utils import Utils
from services.csv_importer import CsvImporter
from services.database_helper import DatabaseHelper
from services.library_manager import LibraryManager
from services.weather_table import WeatherTable
from services.weather_visualizer import WeatherVisualizer


def main() -> None:
    """의존성을 확인하고, CSV를 DB에 적재한 뒤 요약 그래프를 저장한다."""
    Utils.print_divider('=')
    print('  Mars Weather Summary - 화성 날씨 데이터 적재 / 시각화')
    Utils.print_divider('=')
    start_time = Utils.start_timer()
    Utils.print_divider()

    # 외부 라이브러리는 matplotlib 하나뿐이다(sqlite3 / csv / decimal은 표준 내장).
    lib_manager = LibraryManager(REQUIREMENTS_FILE)
    lib_manager.ensure()
    Utils.print_divider()

    # with 구문으로 커넥션을 열고, 작업이 끝나면(예외가 나도) 자동으로 닫는다.
    with DatabaseHelper(DB_FILE) as db:
        importer = CsvImporter(db, CSV_FILE)
        importer.run()
        Utils.print_divider()

        # 1) 그래프 PNG
        visualizer = WeatherVisualizer(db, lib_manager.load, CHART_IMAGE)
        visualizer.run()
        Utils.print_divider()

        # 2) 표 PNG (요약 통계 + 월별 집계)
        table = WeatherTable(db, lib_manager.load, TABLE_IMAGE)
        table.run()

    Utils.print_divider()
    Utils.stop_timer(start_time)
    Utils.print_divider('=')


if __name__ == '__main__':
    main()
