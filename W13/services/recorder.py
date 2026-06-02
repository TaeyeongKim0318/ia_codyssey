"""마이크 녹음 및 WAV 저장 서비스."""

import wave
from datetime import datetime
from types import ModuleType

from core.config import CHANNELS, CHUNK, RATE, RECORDS_DIR, SAMPLE_WIDTH
from core.utils import Utils


class Recorder:
    """마이크 입력을 녹음하고 WAV 파일로 저장한다."""

    def __init__(self, sd: ModuleType, records_dir: str = RECORDS_DIR) -> None:
        """녹음기를 초기화한다."""
        self.sd = sd
        self.records_dir = Utils.set_file_path(records_dir)

    def has_microphone(self) -> bool:
        """입력 채널이 있는 장치가 하나라도 있는지 확인한다."""
        return len(self._list_input_devices()) > 0

    def print_input_devices(self) -> None:
        """현재 기본 마이크와 사용 가능한 입력 장치 목록을 출력한다."""
        try:
            default = self.sd.query_devices(kind='input')
            Utils.print_log(
                '마이크',
                '현재 연결된 마이크: ' + default['name']
                + ' (채널 ' + str(default['max_input_channels']) + ')'
            )
        except (ValueError, self.sd.PortAudioError) as e:  # 기본 입력 장치가 없을 때
            Utils.print_log('마이크', '현재 연결된 마이크를 확인할 수 없습니다: ' + str(e))

        devices = self._list_input_devices()
        Utils.print_log('마이크', '사용 가능한 입력 장치 (' + str(len(devices)) + '개):')
        for info in devices:
            print('  - ' + info['name'] + ' (채널 ' + str(info['max_input_channels']) + ')')

    def record(self) -> list[bytes]:
        """Ctrl+C를 누를 때까지 마이크 음성을 녹음하고 프레임 목록을 반환한다."""
        frames = []

        def callback(indata, frame_count, time_info, status):
            # 오디오 블록이 들어올 때마다 frames에 누적한다.
            frames.append(bytes(indata))

        Utils.print_divider()
        Utils.print_log('녹음', '녹음을 시작합니다. 중지하려면 Ctrl+C 를 누르세요.')
        Utils.print_divider()

        try:
            with self.sd.RawInputStream(
                samplerate=RATE,
                channels=CHANNELS,
                dtype='int16',
                blocksize=CHUNK,
                callback=callback,
            ):
                while True:
                    self.sd.sleep(1000)
        except KeyboardInterrupt:  # Ctrl+C를 녹음 종료 신호로 사용
            print()
            Utils.print_log('녹음', '녹음이 중지되었습니다.')

        return frames

    def save(self, frames: list[bytes]) -> None:
        """녹음된 프레임을 시각 기반 이름의 WAV 파일로 저장한다."""
        self._ensure_records_dir()
        filepath = self.records_dir / self._generate_filename()
        with wave.open(str(filepath), 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(SAMPLE_WIDTH)
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
        Utils.print_log('저장', '파일 저장 완료: ' + str(filepath))

    def list_by_date(self, start_str: str, end_str: str) -> None:
        """지정한 날짜 범위('YYYYMMDD')에 해당하는 wav 파일을 출력한다."""
        if not self.records_dir.exists():
            Utils.print_log('조회', '저장된 녹음 파일이 없습니다.')
            return

        try:
            start = datetime.strptime(start_str, '%Y%m%d').date()
            end = datetime.strptime(end_str, '%Y%m%d').date()
        except ValueError:
            Utils.print_log('오류', '날짜 형식이 올바르지 않습니다. 예시: 20260101')
            return

        files = sorted(p.name for p in self.records_dir.iterdir())
        filtered = []
        for f in files:
            if not f.endswith('.wav'):
                continue
            try:
                # 파일명 앞 8자리(YYYYMMDD)를 녹음 날짜로 해석한다.
                file_date = datetime.strptime(f[:8], '%Y%m%d').date()
                if start <= file_date <= end:
                    filtered.append(f)
            except ValueError:  # 날짜 형식이 아닌 파일명은 건너뜀
                continue

        Utils.print_divider()
        if filtered:
            Utils.print_log('조회', start_str + ' ~ ' + end_str + ' 녹음 파일 목록 (' + str(len(filtered)) + '개)')
            Utils.print_divider()
            for f in filtered:
                print('  - ' + f)
        else:
            Utils.print_log('조회', '해당 기간의 녹음 파일이 없습니다.')
        Utils.print_divider()

    def _list_input_devices(self) -> list[dict]:
        """입력 채널(마이크)이 있는 장치 정보 목록을 반환한다."""
        return [info for info in self.sd.query_devices() if info['max_input_channels'] > 0]

    def _ensure_records_dir(self) -> None:
        """records 폴더가 없으면 생성한다."""
        if not self.records_dir.exists():
            self.records_dir.mkdir(parents=True)
            Utils.print_log('폴더', str(self.records_dir) + ' 폴더를 생성했습니다.')

    def _generate_filename(self) -> str:
        """현재 시각으로 'YYYYMMDD-HHMMSS.wav' 형식 파일 이름을 만든다."""
        return datetime.now().strftime('%Y%m%d-%H%M%S') + '.wav'
