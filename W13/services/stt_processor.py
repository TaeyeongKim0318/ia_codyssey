"""녹음 파일을 Whisper로 텍스트 변환해 CSV로 저장하는 서비스."""

import csv
import shutil
import warnings
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

from core.config import RECORDS_DIR
from core.utils import Utils


class SttProcessor:
    """녹음된 wav 파일을 Whisper로 텍스트 변환해 CSV로 저장한다."""

    MODEL_CHOICES = {
        '1': 'small',
        '2': 'medium',
        '3': 'large-v3',
    }
    CSV_HEADER = ['시간', '인식된 텍스트']

    def __init__(self, whisper_loader: Callable[[str], ModuleType], records_dir: str = RECORDS_DIR) -> None:
        """STT 처리기를 초기화한다."""
        self.whisper_loader = whisper_loader
        self.records_dir = Utils.set_file_path(records_dir)
        self._whisper = None   # whisper 모듈(최초 사용 시 로드)
        self._model = None     # 로드된 Whisper 모델
        self._model_name = None

    def process_all(self) -> None:
        """records/ 안의 모든 wav 파일을 STT 변환해 CSV로 저장한다.

        이미 같은 모델로 변환된 CSV가 있으면 건너뛰고,
        한 파일에서 오류가 나도 나머지 파일은 계속 처리한다.
        """
        if not self.records_dir.exists():
            Utils.print_log('STT', 'records 폴더가 없습니다. 먼저 녹음을 진행해 주세요.')
            return

        files = self._list_wav_files()
        if not files:
            Utils.print_log('STT', '처리할 wav 파일이 없습니다.')
            return

        # Whisper는 내부적으로 ffmpeg로 오디오를 디코딩하므로 미리 존재를 확인한다.
        if shutil.which('ffmpeg') is None:
            Utils.print_log('STT', 'ffmpeg가 설치되어 있지 않습니다. 설치 후 다시 시도해 주세요.')
            return

        Utils.print_log('STT', '발견된 wav 파일: ' + str(len(files)) + '개')
        self._select_model()
        Utils.print_divider()

        for wav in files:
            target = self._csv_path(wav)
            if target.exists():  # 같은 모델로 이미 변환한 결과가 있으면 재처리하지 않음
                Utils.print_log('STT', '건너뜀 (이미 변환됨): ' + target.name)
                continue

            Utils.print_log('STT', '변환 중: ' + wav.name)
            # 파일 하나가 실패해도 전체 배치가 멈추지 않도록 개별적으로 감싼다.
            try:
                rows = self._transcribe_file(wav)
            except Exception as e:
                Utils.print_log('오류', wav.name + ' 변환 실패: ' + str(e))
                continue

            if not rows:
                Utils.print_log('경고', wav.name + ' 에서 인식된 음성이 없습니다.')
            self._save_csv(wav, rows)

        Utils.print_divider()
        Utils.print_log('STT', '모든 파일 처리 완료')

    def _list_wav_files(self) -> list[Path]:
        """records/ 안의 wav 파일 경로를 정렬해 반환한다."""
        return sorted(
            p for p in self.records_dir.iterdir()
            if p.suffix.lower() == '.wav'
        )

    def _select_model(self) -> None:
        """사용자에게 Whisper 모델 크기를 선택받아 로드한다.

        선택한 모델 이름은 self._model_name에 저장되어 CSV 파일명에 쓰인다.
        """
        Utils.print_log('STT', '사용할 Whisper 모델을 선택하세요.')
        print('  [1] small    (가벼움, 정확도 낮음)')
        print('  [2] medium   (중간)')
        print('  [3] large-v3 (정확도 높음, 무거움)')
        while True:
            choice = Utils.input_with_log('입력', '1 / 2 / 3 >> ')
            if choice in self.MODEL_CHOICES:
                break
            Utils.print_log('오류', '1, 2, 3 중에서 입력해 주세요.')

        model_name = self.MODEL_CHOICES[choice]
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            if self._whisper is None:  # 최초 1회만 무거운 whisper 모듈을 로드
                Utils.print_log('STT', 'Whisper 라이브러리를 불러옵니다...')
                self._whisper = self.whisper_loader('whisper')
            Utils.print_log('STT', model_name + ' 모델 로드 중... (최초 1회 다운로드 시 시간이 소요됩니다)')
            self._model = self._whisper.load_model(model_name)
        self._model_name = model_name
        Utils.print_log('STT', model_name + ' 모델 로드 완료')

    def _csv_path(self, wav_path: Path) -> Path:
        """wav 경로를 '원본이름_모델명.csv' 경로로 변환한다."""
        # 모델명을 파일명에 붙여 모델별 결과가 서로 덮어쓰지 않게 한다.
        return wav_path.with_name(wav_path.stem + '_' + self._model_name + '.csv')

    def _format_time(self, seconds: float) -> str:
        """초 단위 값을 'HH:MM:SS' 문자열로 변환한다."""
        total = int(seconds)
        hours = total // 3600
        minutes = (total % 3600) // 60
        secs = total % 60
        return f'{hours:02d}:{minutes:02d}:{secs:02d}'

    def _transcribe_file(self, wav_path: Path) -> list[tuple[str, str]]:
        """wav 파일을 Whisper로 인식해 (HH:MM:SS, 텍스트) 행 목록을 반환한다."""
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            result = self._model.transcribe(str(wav_path))

        rows = []
        # Whisper는 결과를 구간(segment) 단위로 나눠 주며 각 구간에 시작 시각이 있다.
        for seg in result.get('segments', []):
            text = seg.get('text', '').strip()
            if not text:  # 빈 구간은 기록하지 않음
                continue
            rows.append((self._format_time(seg['start']), text))
        return rows

    def _save_csv(self, wav_path: Path, rows: list[tuple[str, str]]) -> None:
        """인식 결과 행들을 CSV 파일로 저장한다."""
        path = self._csv_path(wav_path)
        # utf-8-sig(BOM)로 저장해야 Excel에서 한글이 깨지지 않는다.
        with open(path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(self.CSV_HEADER)
            writer.writerows(rows)
        Utils.print_log('STT', '저장 완료: ' + path.name)
