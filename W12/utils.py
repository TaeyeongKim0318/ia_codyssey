from pathlib import Path
import time

class utils:
    @staticmethod
    def set_file_path(file_name) -> Path:
        return Path(__file__).parent/file_name
    
    @staticmethod
    def start_timer() -> float:
        start_time = time.time()
        print(f"[시작] {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}")
        return start_time

    @staticmethod
    def stop_timer(start_time):
        end_time = time.time()
        elapsed_time = end_time - start_time
        hours = int(elapsed_time // 3600)
        minutes = int((elapsed_time % 3600) // 60)
        seconds = elapsed_time % 60
        print(f"[종료] {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))}")
        print(f"[경과 시간] {hours}시간 {minutes}분 {seconds:.2f}초")
        
    @staticmethod
    def get_timestamp():
        """현재 시각을 '[HH:MM:SS]' 형식의 문자열로 반환한다."""
        return time.strftime('[%H:%M:%S]')

    @staticmethod
    def print_log(tag, message):
        """타임스탬프와 태그를 포함한 로그 메시지를 출력한다."""
        print(utils.get_timestamp() + ' [' + tag + '] ' + message)

    @staticmethod
    def input_with_log(tag, prompt):
        """타임스탬프와 태그를 포함한 입력 프롬프트를 출력하고 입력값을 반환한다."""
        return input(utils.get_timestamp() + ' [' + tag + '] ' + prompt).strip()

    @staticmethod
    def print_divider(char='-', length=50):
        """구분선을 출력한다."""
        print(char * length)


