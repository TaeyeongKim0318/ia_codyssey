import importlib
import importlib.metadata
import re
import subprocess
import sys
import wave
from datetime import datetime
from utils import utils


REQUIREMENTS_FILE = 'requirements.txt'
RECORDS_DIR = 'records'
CHUNK = 1024
CHANNELS = 1
RATE = 44100


class LibraryManager:
    """requirements.txt 기반 의존성 확인/설치/임포트를 담당한다."""

    def __init__(self, requirements_file):
        self.requirements_file = requirements_file
        self.req_path = utils.set_file_path(requirements_file)

    def parse_requirements(self):
        """requirements.txt를 파싱해 패키지 이름 목록을 반환한다."""
        packages = []
        with open(self.req_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                name = re.split(r'[<>=!~;\s]', line, maxsplit=1)[0].strip()
                if name:
                    packages.append(name)
        return packages

    def find_missing(self, packages):
        """설치되지 않은 패키지 목록을 반환한다."""
        missing = []
        for pkg in packages:
            try:
                importlib.metadata.distribution(pkg)
            except importlib.metadata.PackageNotFoundError:
                missing.append(pkg)
        return missing

    def install_all(self):
        """requirements.txt에 명시된 라이브러리를 pip으로 설치한다."""
        utils.print_log('설치', self.requirements_file + ' 에서 라이브러리 설치를 시작합니다...')
        utils.print_divider()
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-r', str(self.req_path)]
        )
        utils.print_divider()
        if result.returncode != 0:
            utils.print_log('오류', '설치에 실패했습니다.')
            sys.exit(1)

    def ensure(self):
        """필요한 라이브러리가 모두 설치되어 있는지 확인하고 없으면 설치 여부를 묻는다."""
        if not self.req_path.exists():
            utils.print_log('오류', self.requirements_file + ' 파일을 찾을 수 없습니다.')
            sys.exit(1)

        packages = self.parse_requirements()
        if not packages:
            utils.print_log('라이브러리', self.requirements_file + ' 에 명시된 라이브러리가 없습니다.')
            return

        missing = self.find_missing(packages)
        if not missing:
            utils.print_log('라이브러리', '필요한 라이브러리 확인 완료 (' + ', '.join(packages) + ')')
            return

        utils.print_log('경고', '설치되지 않은 라이브러리: ' + ', '.join(missing))
        while True:
            answer = utils.input_with_log('입력', '지금 설치하시겠습니까? (y/n) >> ')
            if answer.lower() == 'y':
                self.install_all()
                still_missing = self.find_missing(packages)
                if still_missing:
                    utils.print_log('오류', '설치 후에도 다음 라이브러리를 찾을 수 없습니다: ' + ', '.join(still_missing))
                    sys.exit(1)
                utils.print_log('설치', '모든 라이브러리 설치 완료')
                return
            elif answer.lower() == 'n':
                utils.print_log('종료', '라이브러리 없이는 실행할 수 없습니다. 프로그램을 종료합니다.')
                sys.exit(0)
            else:
                utils.print_log('오류', 'y 또는 n을 입력해 주세요.')

    def load(self, name):
        """이름으로 모듈을 임포트해 반환한다."""
        return importlib.import_module(name)


class Recorder:
    """마이크 입력을 녹음하고 WAV 파일로 저장한다."""

    SAMPLE_WIDTH = 2

    def __init__(self, sd, records_dir=RECORDS_DIR):
        self.sd = sd
        self.records_dir = utils.set_file_path(records_dir)

    def list_input_devices(self):
        """입력 채널이 있는 장치 정보 목록을 반환한다."""
        return [info for info in self.sd.query_devices() if info['max_input_channels'] > 0]

    def has_microphone(self):
        """입력 채널이 있는 장치가 하나라도 있는지 확인한다."""
        return len(self.list_input_devices()) > 0

    def print_input_devices(self):
        """현재 연결된 마이크와 사용 가능한 입력 장치를 출력한다."""
        try:
            default = self.sd.query_devices(kind='input')
            utils.print_log(
                '마이크',
                '현재 연결된 마이크: ' + default['name']
                + ' (채널 ' + str(default['max_input_channels']) + ')'
            )
        except (ValueError, self.sd.PortAudioError) as e:
            utils.print_log('마이크', '현재 연결된 마이크를 확인할 수 없습니다: ' + str(e))

        devices = self.list_input_devices()
        utils.print_log('마이크', '사용 가능한 입력 장치 (' + str(len(devices)) + '개):')
        for info in devices:
            print('  - ' + info['name'] + ' (채널 ' + str(info['max_input_channels']) + ')')

    def ensure_records_dir(self):
        """records 폴더가 없으면 생성한다."""
        if not self.records_dir.exists():
            self.records_dir.mkdir(parents=True)
            utils.print_log('폴더', str(self.records_dir) + ' 폴더를 생성했습니다.')

    def generate_filename(self):
        """현재 시각으로 wav 파일명을 생성한다."""
        return datetime.now().strftime('%Y%m%d-%H%M%S') + '.wav'

    def record(self):
        """마이크에서 음성을 녹음하고 프레임 데이터를 반환한다."""
        frames = []

        def callback(indata, frame_count, time_info, status):
            frames.append(bytes(indata))

        utils.print_divider()
        utils.print_log('녹음', '녹음을 시작합니다. 중지하려면 Ctrl+C 를 누르세요.')
        utils.print_divider()

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
        except KeyboardInterrupt:
            print()
            utils.print_log('녹음', '녹음이 중지되었습니다.')

        return frames

    def save(self, frames):
        """녹음된 프레임을 WAV 파일로 저장한다."""
        self.ensure_records_dir()
        filepath = self.records_dir / self.generate_filename()
        with wave.open(str(filepath), 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(self.SAMPLE_WIDTH)
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
        utils.print_log('저장', '파일 저장 완료: ' + str(filepath))

    def list_by_date(self, start_str, end_str):
        """지정한 범위의 wav 파일을 출력한다."""
        if not self.records_dir.exists():
            utils.print_log('조회', '저장된 녹음 파일이 없습니다.')
            return

        try:
            start = datetime.strptime(start_str, '%Y%m%d').date()
            end = datetime.strptime(end_str, '%Y%m%d').date()
        except ValueError:
            utils.print_log('오류', '날짜 형식이 올바르지 않습니다. 예시: 20260101')
            return

        files = sorted(p.name for p in self.records_dir.iterdir())
        filtered = []
        for f in files:
            if not f.endswith('.wav'):
                continue
            try:
                file_date = datetime.strptime(f[:8], '%Y%m%d').date()
                if start <= file_date <= end:
                    filtered.append(f)
            except ValueError:
                continue

        utils.print_divider()
        if filtered:
            utils.print_log('조회', start_str + ' ~ ' + end_str + ' 녹음 파일 목록 (' + str(len(filtered)) + '개)')
            utils.print_divider()
            for f in filtered:
                print('  - ' + f)
        else:
            utils.print_log('조회', '해당 기간의 녹음 파일이 없습니다.')
        utils.print_divider()

def main():
    """프로그램 메인 실행 함수."""
    utils.print_divider('=')
    print('  Javis - 음성 녹음 프로그램')
    utils.print_divider('=')
    start_time = utils.start_timer()
    utils.print_divider()

    lib_manager = LibraryManager(REQUIREMENTS_FILE)
    lib_manager.ensure()
    sd = lib_manager.load('sounddevice')

    recorder = Recorder(sd)
    if not recorder.has_microphone():
        utils.print_log('오류', '마이크를 찾을 수 없습니다. 마이크 연결 후 다시 실행해 주세요.')
        sys.exit(1)

    recorder.print_input_devices()
    utils.print_divider()

    while True:
        print('\n  [1] 녹음')
        print('  [2] 날짜별 파일 조회')
        print('  [3] 종료')
        choice = utils.input_with_log('입력', '메뉴를 선택하세요 (1 / 2 / 3) >> ')

        if choice == '1':
            frames = recorder.record()
            if frames:
                recorder.save(frames)
            else:
                utils.print_log('경고', '녹음된 내용이 없습니다.')

        elif choice == '2':
            start = utils.input_with_log('입력', '시작 날짜를 입력하세요 (YYYYMMDD) >> ')
            end = utils.input_with_log('입력', '종료 날짜를 입력하세요 (YYYYMMDD) >> ')
            recorder.list_by_date(start, end)

        elif choice == '3':
            break

        else:
            utils.print_log('오류', '1, 2, 3 중에서 입력해 주세요.')

    utils.print_divider()
    utils.stop_timer(start_time)
    utils.print_divider('=')


if __name__ == '__main__':
    main()
