"""프로그램 전역에서 공유하는 설정 상수 모음."""

REQUIREMENTS_FILE = 'requirements.txt'
CSV_FILE = 'mars_weathers_data.CSV'     # 제공된 화성 날씨 백업 데이터(확장자가 대문자임에 주의)
DB_FILE = 'mars_weather.db'             # sqlite3 데이터베이스 파일
CHART_IMAGE = 'mars_weather_chart.png'  # 기온/모래 폭풍 그래프
TABLE_IMAGE = 'mars_weather_table.png'  # 요약 통계 + 월별 집계 표

TABLE_NAME = 'mars_weather'
CHUNK_SIZE = 500        # CSV 적재 시 한 번에 INSERT 할 행 수(메모리와 속도의 균형)
STORM_THRESHOLD = 90    # 이 값 이상이면 위험한 모래 폭풍으로 보고 그래프에서 강조한다
