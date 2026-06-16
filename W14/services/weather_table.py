"""데이터베이스에 적재된 화성 날씨 데이터를 표(요약 통계 + 월별 집계)로 그려 PNG로 저장하는 서비스."""

from collections.abc import Callable
from types import ModuleType

from core.config import STORM_THRESHOLD, TABLE_IMAGE, TABLE_NAME
from core.utils import Utils
from services.database_helper import DatabaseHelper


class WeatherTable:
    """mars_weather 테이블을 읽어 요약/월별 통계 표를 하나의 PNG로 저장한다."""

    MONTHLY_HEADER = ['Month', 'Avg temp', 'Max storm', 'Storm days']

    def __init__(
        self,
        db: DatabaseHelper,
        module_loader: Callable[[str], ModuleType],
        output_image: str = TABLE_IMAGE,
    ) -> None:
        """표 생성기를 초기화한다."""
        self.db = db
        # matplotlib 임포트를 실제 사용 시점까지 미루기 위한 로더(LibraryManager.load).
        self.loader = module_loader
        self.output_path = Utils.set_file_path(output_image)

    def run(self) -> None:
        """DB에서 데이터를 읽어 요약/월별 표를 그리고 PNG로 저장한다."""
        rows = self.db.select(TABLE_NAME, order_by='mars_date')
        if not rows:
            Utils.print_log('표', '표로 만들 데이터가 없습니다.')
            return

        dates = [row['mars_date'] for row in rows]
        temps = [float(row['temp']) for row in rows]   # 저장된 정확 문자열을 계산용 실수로 변환
        storms = [int(row['storm']) for row in rows]

        summary = self._build_summary(dates, temps, storms)
        monthly = self._build_monthly(dates, temps, storms)
        self._render(summary, monthly)

    def _build_summary(self, dates: list, temps: list, storms: list) -> list[list[str]]:
        """전체 데이터를 한눈에 보는 요약 통계표(행: [항목, 값])를 만든다."""
        danger_days = sum(1 for s in storms if s >= STORM_THRESHOLD)
        return [
            ['Period', dates[0] + ' ~ ' + dates[-1]],
            ['Rows', str(len(dates))],
            ['Temp (min / avg / max)',
             self._fmt(min(temps)) + ' / ' + self._fmt(self._mean(temps)) + ' / ' + self._fmt(max(temps))],
            ['Storm (min / avg / max)',
             str(min(storms)) + ' / ' + self._fmt(self._mean(storms)) + ' / ' + str(max(storms))],
            ['Storm days (>= ' + str(STORM_THRESHOLD) + ')', str(danger_days)],
        ]

    def _build_monthly(self, dates: list, temps: list, storms: list) -> list[list[str]]:
        """'YYYY-MM' 단위로 묶어 월별 집계표(평균기온/최대폭풍/위험일수)를 만든다."""
        groups: dict[str, list[tuple[float, int]]] = {}
        for date, temp, storm in zip(dates, temps, storms):
            groups.setdefault(date[:7], []).append((temp, storm))  # 'YYYY-MM'로 그룹화

        rows = []
        for month in sorted(groups):
            items = groups[month]
            month_temps = [t for t, _ in items]
            month_storms = [s for _, s in items]
            danger = sum(1 for s in month_storms if s >= STORM_THRESHOLD)
            rows.append([
                month,
                self._fmt(self._mean(month_temps)),
                str(max(month_storms)),
                str(danger),
            ])
        return rows

    def _render(self, summary: list[list[str]], monthly: list[list[str]]) -> None:
        """요약 표와 월별 표를 위아래로 배치해 하나의 PNG로 저장한다.

        matplotlib 기본 폰트는 한글 글리프가 없어 경고가 나므로 라벨은 영문으로 쓴다.
        """
        plt = self._load_pyplot()

        # 행 수에 비례해 그림 높이를 정한다(월별 표가 길어질 수 있으므로).
        total_rows = len(summary) + len(monthly) + 2
        fig = plt.figure(figsize=(9, max(4.0, total_rows * 0.35)))
        grid = fig.add_gridspec(
            2, 1,
            height_ratios=[len(summary) + 1, len(monthly) + 1],
            hspace=0.1,
        )

        ax_summary = fig.add_subplot(grid[0])
        ax_summary.set_title('Mars Weather - Summary', fontweight='bold')
        self._draw_table(ax_summary, summary, col_labels=None)

        ax_monthly = fig.add_subplot(grid[1])
        ax_monthly.set_title('Monthly aggregation', fontweight='bold')
        self._draw_table(ax_monthly, monthly, col_labels=self.MONTHLY_HEADER)

        fig.savefig(str(self.output_path), dpi=150, bbox_inches='tight')
        plt.close(fig)  # 그림 객체를 닫아 메모리를 정리한다
        Utils.print_log('표', '표 저장 완료: ' + str(self.output_path))

    @staticmethod
    def _draw_table(ax, cell_text: list[list[str]], col_labels: list[str] | None) -> None:
        """한 축(ax)에 표 하나를 그린다."""
        ax.axis('off')
        table = ax.table(
            cellText=cell_text,
            colLabels=col_labels,
            cellLoc='center',
            loc='center',
        )
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1.0, 1.4)  # 셀 세로 여백을 넓혀 가독성을 높인다
        if cell_text:
            table.auto_set_column_width(col=list(range(len(cell_text[0]))))

        if col_labels is not None:
            # 헤더 행(0행)을 굵게/음영 처리한다.
            for col in range(len(col_labels)):
                header_cell = table[0, col]
                header_cell.set_text_props(fontweight='bold')
                header_cell.set_facecolor('#dee2e6')
        else:
            # 헤더가 없는 요약 표는 첫 열(항목명)을 굵게 처리한다.
            for row in range(len(cell_text)):
                table[row, 0].set_text_props(fontweight='bold')

    def _load_pyplot(self) -> ModuleType:
        """화면 없이 파일로만 저장하도록 백엔드를 설정한 뒤 pyplot을 반환한다."""
        matplotlib = self.loader('matplotlib')
        matplotlib.use('Agg')  # GUI 없이 PNG 저장만 하는 백엔드
        return self.loader('matplotlib.pyplot')

    @staticmethod
    def _mean(values: list) -> float:
        """값들의 산술 평균을 반환한다."""
        return sum(values) / len(values)

    @staticmethod
    def _fmt(value: float) -> str:
        """실수를 소수점 2자리 문자열로 변환한다."""
        return f'{value:.2f}'
