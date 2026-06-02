"""Javis 음성 녹음 / STT 프로그램의 진입점."""

from core.config import REQUIREMENTS_FILE
from core.utils import Utils
from services.keyword_searcher import KeywordSearcher
from services.library_manager import LibraryManager
from services.recorder import Recorder
from services.stt_processor import SttProcessor


def main():
    """의존성을 확인하고 서비스를 초기화한 뒤, 종료 전까지 메뉴 입력을 반복 처리한다."""
    Utils.print_divider('=')
    print('  Javis - 음성 녹음 / STT 프로그램')
    Utils.print_divider('=')
    start_time = Utils.start_timer()
    Utils.print_divider()

    lib_manager = LibraryManager(REQUIREMENTS_FILE)
    lib_manager.ensure()
    sd = lib_manager.load('sounddevice')

    recorder = Recorder(sd)
    # STT는 마이크가 필요 없으므로, 마이크가 없어도 종료하지 않고 경고만 한다.
    if recorder.has_microphone():
        recorder.print_input_devices()
    else:
        Utils.print_log('경고', '마이크를 찾을 수 없습니다. 녹음은 불가하지만 STT 변환은 가능합니다.')
    Utils.print_divider()

    # whisper 로더를 주입해, 실제 STT를 쓸 때까지 무거운 import를 미룬다.
    stt = SttProcessor(lib_manager.load)
    searcher = KeywordSearcher()

    while True:
        print('\n  [1] 녹음')
        print('  [2] 날짜별 파일 조회')
        print('  [3] STT 변환')
        print('  [4] 키워드 검색')
        print('  [5] 종료')
        choice = Utils.input_with_log('입력', '메뉴를 선택하세요 (1 / 2 / 3 / 4 / 5) >> ')

        if choice == '1':
            if not recorder.has_microphone():  # 실행 중 마이크가 빠졌을 수 있어 다시 확인
                Utils.print_log('오류', '마이크가 없어 녹음할 수 없습니다.')
                continue
            frames = recorder.record()
            if frames:
                recorder.save(frames)
            else:
                Utils.print_log('경고', '녹음된 내용이 없습니다.')

        elif choice == '2':
            start = Utils.input_with_log('입력', '시작 날짜를 입력하세요 (YYYYMMDD) >> ')
            end = Utils.input_with_log('입력', '종료 날짜를 입력하세요 (YYYYMMDD) >> ')
            recorder.list_by_date(start, end)

        elif choice == '3':
            stt.process_all()

        elif choice == '4':
            keyword = Utils.input_with_log('입력', '검색할 키워드를 입력하세요 >> ')
            searcher.search(keyword)

        elif choice == '5':
            break

        else:
            Utils.print_log('오류', '1, 2, 3, 4, 5 중에서 입력해 주세요.')

    Utils.print_divider()
    Utils.stop_timer(start_time)
    Utils.print_divider('=')


if __name__ == '__main__':
    main()
