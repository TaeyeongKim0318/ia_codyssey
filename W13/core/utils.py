"""파일 경로, 시간 측정, 로그 출력 등 공통 헬퍼 모음."""

from pathlib import Path
import time


class Utils:
    """프로젝트 전반에서 쓰이는 정적 헬퍼 메서드 모음."""

    @staticmethod
    def set_file_path(file_name: str) -> Path:
        """파일 이름을 프로젝트 루트 기준의 절대 경로로 변환한다."""
        # 이 파일은 core/ 하위에 있으므로 두 단계 상위가 프로젝트 루트다.
        return Path(__file__).resolve().parent.parent / file_name

    @staticmethod
    def start_timer() -> float:
        """시작 시각을 출력하고 그 값(epoch 초)을 반환한다."""
        start_time = time.time()
        print(f'[시작] {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time))}')
        return start_time

    @staticmethod
    def stop_timer(start_time: float) -> None:
        """종료 시각과 시작 이후 경과 시간을 출력한다."""
        end_time = time.time()
        elapsed_time = end_time - start_time
        hours = int(elapsed_time // 3600)
        minutes = int((elapsed_time % 3600) // 60)
        seconds = elapsed_time % 60
        print(f'[종료] {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(end_time))}')
        print(f'[경과 시간] {hours}시간 {minutes}분 {seconds:.2f}초')

    @staticmethod
    def get_timestamp() -> str:
        """현재 시각을 '[HH:MM:SS]' 형식 문자열로 반환한다."""
        return time.strftime('[%H:%M:%S]')

    @staticmethod
    def print_log(tag: str, message: str) -> None:
        """타임스탬프와 태그를 붙인 로그 한 줄을 출력한다."""
        print(Utils.get_timestamp() + ' [' + tag + '] ' + message)

    @staticmethod
    def input_with_log(tag: str, prompt: str) -> str:
        """타임스탬프와 태그를 붙인 입력 프롬프트를 띄우고 입력값(양끝 공백 제거)을 반환한다."""
        return input(Utils.get_timestamp() + ' [' + tag + '] ' + prompt).strip()

    @staticmethod
    def print_divider(char: str = '-', length: int = 50) -> None:
        """구분선을 출력한다."""
        print(char * length)
