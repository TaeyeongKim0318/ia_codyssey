"""데이터베이스에 적재된 화성 날씨 데이터를 그래프로 그려 PNG로 저장하는 서비스."""

from collections.abc import Callable
from datetime import datetime
from types import ModuleType

from core.config import CHART_IMAGE, STORM_THRESHOLD, TABLE_NAME
from core.utils import Utils
from services.database_helper import DatabaseHelper


class WeatherVisualizer:
    """mars_weather 테이블을 읽어 기온/모래 폭풍 그래프를 PNG로 저장한다."""

    DATE_FORMAT = '%Y-%m-%d'

    def __init__(
        self,
        db: DatabaseHelper,
        module_loader: Callable[[str], ModuleType],
        output_image: str = CHART_IMAGE,
    ) -> None:
        """시각화기를 초기화한다."""
        self.db = db
        # matplotlib 임포트를 실제 사용 시점까지 미루기 위한 로더(LibraryManager.load).
        self.loader = module_loader
        self.output_path = Utils.set_file_path(output_image)

    def run(self) -> None:
        """DB에서 데이터를 읽어 그래프를 그리고 PNG로 저장한다."""
        rows = self.db.select(TABLE_NAME, order_by='mars_date')
        if not rows:
            Utils.print_log('시각화', '그릴 데이터가 없습니다.')
            return

        dates = [datetime.strptime(row['mars_date'], self.DATE_FORMAT) for row in rows]
        temps = [float(row['temp']) for row in rows]   # 저장된 정확 문자열을 그래프용 실수로 변환
        storms = [int(row['storm']) for row in rows]

        self._plot(dates, temps, storms)

    def _plot(self, dates: list, temps: list, storms: list) -> None:
        """기온 선그래프와 모래 폭풍 강도를 한 그림에 그려 저장한다.

        matplotlib 기본 폰트는 한글 글리프가 없어 경고가 발생하므로 라벨은 영문으로 쓴다.
        """
        plt = self._load_pyplot()

        fig, ax_temp = plt.subplots(figsize=(14, 6))

        # 1) 기온: 왼쪽 축에 선그래프
        ax_temp.plot(dates, temps, color='#d9480f', linewidth=1.0, label='Temperature')
        ax_temp.set_xlabel('Mars date')
        ax_temp.set_ylabel('Temperature', color='#d9480f')
        ax_temp.tick_params(axis='y', labelcolor='#d9480f')

        # 2) 모래 폭풍 강도: 오른쪽 축에 영역(area)으로 표현
        ax_storm = ax_temp.twinx()
        ax_storm.fill_between(dates, storms, color='#4263eb', alpha=0.15, label='Storm intensity')
        ax_storm.set_ylabel('Storm intensity', color='#4263eb')
        ax_storm.tick_params(axis='y', labelcolor='#4263eb')
        ax_storm.axhline(STORM_THRESHOLD, color='#4263eb', linestyle='--', linewidth=0.8)

        # 3) 임계값 이상의 위험한 모래 폭풍이 분 날의 기온을 빨간 점으로 강조
        danger_dates = [d for d, s in zip(dates, storms) if s >= STORM_THRESHOLD]
        danger_temps = [t for t, s in zip(temps, storms) if s >= STORM_THRESHOLD]
        if danger_dates:
            ax_temp.scatter(
                danger_dates, danger_temps,
                color='#e03131', s=12, zorder=5,
                label='Storm >= ' + str(STORM_THRESHOLD),
            )

        ax_temp.set_title('Mars Weather Summary (temperature & sand storm)')
        ax_temp.grid(True, alpha=0.2)
        fig.autofmt_xdate()  # 날짜 라벨이 겹치지 않도록 기울인다
        self._merge_legends(ax_temp, ax_storm)

        fig.tight_layout()
        fig.savefig(str(self.output_path), dpi=150)
        plt.close(fig)  # 그림 객체를 닫아 메모리를 정리한다
        Utils.print_log('시각화', '그래프 저장 완료: ' + str(self.output_path))

    def _load_pyplot(self) -> ModuleType:
        """화면 없이 파일로만 저장하도록 백엔드를 설정한 뒤 pyplot을 반환한다."""
        matplotlib = self.loader('matplotlib')
        matplotlib.use('Agg')  # GUI 없이 PNG 저장만 하는 백엔드
        return self.loader('matplotlib.pyplot')

    @staticmethod
    def _merge_legends(ax_left, ax_right) -> None:
        """좌우 두 축의 범례 항목을 모아 하나의 범례로 그린다."""
        handles_left, labels_left = ax_left.get_legend_handles_labels()
        handles_right, labels_right = ax_right.get_legend_handles_labels()
        ax_left.legend(
            handles_left + handles_right,
            labels_left + labels_right,
            loc='upper right',
        )
