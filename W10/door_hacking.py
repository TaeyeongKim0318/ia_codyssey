import zipfile
import time
import string
from multiprocessing import Process, Queue
import signal
import os


"""
유틸리티 클래스들과 크래킹 함수들을 포함한 ZIP 파일 비밀번호 크래킹 프로그램
멀티프로세싱과 딕셔너리 공격을 지원한다.
"""
class Utils:
    """
    파일 경로 찾기와 파일 저장 등의 유틸리티 기능을 제공하는 클래스
    """
    @staticmethod
    def set_file_path(file_name):
        """
        현재 스크립트 파일이 있는 디렉토리를 기반으로 대상 파일의 절대 경로를 반환한다.
        
        Args:
            file_name (str): 찾을 파일 이름 (예: 'emergency_storage_key.zip')
        
        Returns:
            str: 파일의 절대 경로
        """
        last_slash_index = __file__.rfind('\\') # Windows의 경우 '\'를 찾음
        
        if last_slash_index == -1: # Windows가 아닌 경우 (Mac, Linux)
            last_slash_index = __file__.rfind('/') # '/'를 찾음
        
        base_dir = __file__[:last_slash_index + 1] # 스크립트가 있는 디렉토리 경로 추출
        file_path = base_dir + file_name # 디렉토리 + 파일명으로 전체 경로 생성
        return file_path

    @staticmethod
    def update_file(output_file, content):
        """
        찾아낸 비밀번호를 파일로 저장한다.
        
        Args:
            output_file (str): 저장할 파일 경로 (예: 'password.txt')
            content (str): 저장할 내용 (비밀번호 문자열)
        
        Returns:
            str: 성공 시 비밀번호, 실패 시 None
        
        예외 처리:
            - IOError: 파일 쓰기 권한이 없을 때
            - FileNotFoundError: 지정한 디렉토리가 없을 때
            - Exception: 예상치 못한 모든 오류
        """
        try:
            output_file_path = Utils.set_file_path(output_file)
            with open(output_file_path, 'w') as f: # 파일을 쓰기 모드('w')로 열어서 비밀번호 저장
                f.write(content)
            print(f"[저장] {output_file_path}에 비밀번호 저장 완료")

        except IOError as e: # 파일 쓰기 중 입출력 오류 발생
            print(f"[오류] 파일 저장 실패: {e}")
        
        except FileNotFoundError: # 지정한 디렉토리가 없음
            print(f"[오류] '{output_file_path}' 파일 식별 불가")
            return None
        
        except Exception as e: # 예상치 못한 다른 오류
            print(f'[오류] 알 수 없는 에러가 발생\n{e}')
            return None


class Stopwatch:
    """
    프로그램의 실행 시간을 측정하고 진행 상황을 출력하는 클래스
    """
    
    @staticmethod
    def start(file_name):
        """
        크래킹 시작 시간을 기록하고 초기 정보를 출력한다.
        
        Args:
            file_name (str): 대상 ZIP 파일 경로
        
        Returns:
            float: 시작 시간 (time.time() 반환값)
        """
        start_time = time.time()
        print(f"[시작] {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}")
        print(f"[대상] {file_name}")
        print(f"[범위] 6자리 (0-9, a-z)")
        print("-" * 50)
        return start_time
    
    @staticmethod
    def stop(start_time, password, attempt_count, success):
        """
        크래킹 종료 시간을 기록하고 최종 결과를 출력한다.
        
        Args:
            start_time (float): 시작 시간
            password (str): 찾은 비밀번호 (실패 시 None)
            attempt_count (int): 총 시도 횟수
            success (bool): 성공 여부
        
        Returns:
            None
        """
        end_time = time.time()
        elapsed_time = end_time - start_time
        hours = int(elapsed_time // 3600)
        minutes = int((elapsed_time % 3600) // 60)
        seconds = elapsed_time % 60
        if success:
            print(f"\n[성공!] 비밀번호 찾음: {password}")
        else:
            print(f"\n[실패] 비밀번호를 찾지 못했습니다.")
        print(f"[반복 회수] {attempt_count:,}회")
        print(f"[경과 시간] {hours}시간 {minutes}분 {seconds:.2f}초")
        print("-" * 50)

    @staticmethod
    def lap_time(process_num, idx, start_idx, end_idx, characters):
        password_at_checkpoint = index_to_password(idx, characters)
        progress = ((idx - start_idx) / (end_idx - start_idx)) * 100
        print(f"[프로세스{process_num}] 진행 상황: {progress:.1f}% (현재: {password_at_checkpoint})")


class DictionaryAttack:
    """
    자주 사용되는 비밀번호를 먼저 시도하는 딕셔너리 공격 클래스
    일반적으로 사용되는 약한 비밀번호들을 목록으로 관리한다.
    """
    
    # 자주 사용되는 약한 비밀번호 목록
    COMMON_PASSWORDS = [
        '000000', '111111', '222222', '333333', '444444',
        '555555', '666666', '777777', '888888', '999999',
        'aaaaaa', 'bbbbbb', 'cccccc', 'dddddd', 'eeeeee',
        'ffffff', 'gggggg', 'hhhhhh', 'iiiiii', 'jjjjjj',
        '123456', '654321', 'abcdef', 'fedcba', '000001',
        '999999', 'qwerty', 'asdfgh', 'zxcvbn', '112233',
    ]
    
    @staticmethod
    def get_common_passwords():
        """
        자주 사용되는 비밀번호 목록을 반환한다.
        
        Returns:
            list: 일반적으로 사용되는 6자리 비밀번호 목록
        """
        return DictionaryAttack.COMMON_PASSWORDS
    
    @staticmethod
    def try_common_passwords(zip_path, output_file):
        """
        자주 사용되는 비밀번호 목록으로 ZIP 파일을 열려고 시도한다.
        
        Args:
            zip_path (str): ZIP 파일 경로
            output_file (str): 비밀번호 저장 파일명
        
        Returns:
            str: 성공 시 비밀번호, 실패 시 None
        
        알고리즘:
            1. 자주 사용되는 비밀번호 목록을 가져옴
            2. 각 비밀번호로 ZIP 파일을 읽으려고 시도
            3. 성공하면 바로 반환
            4. 목록의 모든 비밀번호를 시도해도 실패하면 None 반환
        """
        start_time = Stopwatch.start(zip_path)
        attempt_count = 0
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_file:
                common_passwords = DictionaryAttack.get_common_passwords()
                for password in common_passwords:
                    attempt_count += 1
                    print(f"[시도] {password}")  # 시도하는 비밀번호 출력
                    try:
                        for file_info in zip_file.filelist:
                            zip_file.read(file_info.filename, pwd=password.encode('utf-8'))
                        
                        Stopwatch.stop(start_time, password, attempt_count, True)
                        Utils.update_file(output_file, password)
                        return password
                    
                    except Exception: # 비밀번호가 틀렸으므로 다음으로 진행
                        pass
                
                Stopwatch.stop(start_time, None, attempt_count, False)
        
        except Exception as e:
            print(f"[오류] 딕셔너리 공격 중 오류 발생: {e}")
        
        return None


def index_to_password(index, characters):
    """
    인덱스 번호를 비밀번호로 변환한다. (36진법 변환)
    
    Args:
        index (int): 변환할 인덱스 번호
        characters (str): 사용 가능한 문자 목록
    
    Returns:
        str: 변환된 비밀번호
    
    작동 원리:
        36진법으로 변환 (인라인 언롤링)
        예: 0 → '000000', 1 → '000001', 36 → '000010'
    """
    c0 = characters[index % 36]; index //= 36
    c1 = characters[index % 36]; index //= 36
    c2 = characters[index % 36]; index //= 36
    c3 = characters[index % 36]; index //= 36
    c4 = characters[index % 36]; index //= 36
    c5 = characters[index % 36]
    
    return c5 + c4 + c3 + c2 + c1 + c0


def unlock_zip(zip_path, start_idx, end_idx, characters, process_num, result_queue, attempt_queue):
    """
    프로세스 워커 함수: 할당된 범위의 비밀번호를 시도한다.
    
    Args:
        zip_path (str): ZIP 파일 경로
        start_idx (int): 시작 인덱스
        end_idx (int): 종료 인덱스
        characters (str): 사용 가능한 문자 목록
        process_num (int): 프로세스 번호 (1, 2, 3, 4)
        result_queue (Queue): 결과를 전달할 큐
    
    Returns:
        None
    
    작동 원리:
        1. start_idx부터 end_idx까지 순서대로 진행
        2. 각 인덱스를 비밀번호로 변환
        3. ZIP 파일을 그 비밀번호로 열려고 시도
        4. 성공하면 result_queue에 저장하고 종료
        5. 특정 범위마다 진행 상황 출력
    """
    attempts = 0
    def signal_handler(signum, frame):
        attempt_queue.put(attempts)  # 현재까지의 시도 횟수 저장
        exit()  # 프로세스 종료
    
    signal.signal(signal.SIGTERM, signal_handler)
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_file:
            filelist = zip_file.filelist # filelist 캐싱
            check_interval = max(1, (end_idx - start_idx) // 5) # 범위를 5등분으로 나누어 진행 상황 출력
            next_checkpoint = start_idx + check_interval
            
            for idx in range(start_idx, end_idx): # 할당된 범위를 순서대로
                attempts = idx - start_idx + 1
                # 범위 체크포인트에 도달하면 출력
                if idx >= next_checkpoint:
                    Stopwatch.lap_time(process_num, idx, start_idx, end_idx, characters)
                    next_checkpoint += check_interval
                
                password = index_to_password(idx, characters) # 인덱스를 비밀번호로 변환
                try:
                    for file_info in filelist: # ZIP 내의 모든 파일 정보 순회 (캐시된 것 사용)
                        zip_file.read(file_info.filename, pwd=password.encode('utf-8')) # 비밀번호로 읽기 시도
                    result_queue.put(password) # 성공하면 결과를 큐에 저장
                    attempt_queue.put(attempts)
                    return
                
                except Exception: # 비밀번호가 틀렸으므로 다음으로 진행
                    pass
            
            # 범위 검사 완료
            print(f"[프로세스{process_num}] 할당된 범위 검사 완료 (100.0%)")
    
    except Exception as e:
        print(f"[오류] 워커 프로세스{process_num} 오류: {e}")


class MultiProcessingCracker:
    """
    멀티프로세싱을 사용하여 비밀번호를 병렬로 크래킹하는 클래스
    여러 개의 프로세스가 동시에 다른 범위의 비밀번호를 시도한다.
    """
    
    def __init__(self):
        """
        멀티프로세싱 크래커를 초기화한다.
        
        Args:
            num_processes (int): 사용할 프로세스 개수
        """
        # 사용할 프로세스 개수
        self.cpu_count = os.cpu_count()
        self.num_processes = max(1, int(self.cpu_count)-2)
        self.found_password = None # 찾은 비밀번호 저장
        self.start_time = None # 시작 시간
    
    def crack(self, zip_path, output_file, characters):
        """
        멀티프로세싱을 사용하여 ZIP 파일의 비밀번호를 크래킹한다.
        
        Args:
            zip_path (str): ZIP 파일 경로
            output_file (str): 비밀번호를 저장할 파일명
            characters (str): 사용 가능한 문자 목록
        
        Returns:
            str: 비밀번호를 찾으면 그 비밀번호 반환
            None: 찾지 못하면 None 반환
        
        알고리즘 (4개 프로세스 기준):
            전체 범위를 4등분으로 나누어 각 프로세스에 할당
            
            범위: A → B → C → D → E
                  0   1/4  1/2  3/4  1
            
            프로세스 1: A → B (0 ~ 1/4)
            프로세스 2: B → C (1/4 ~ 1/2)
            프로세스 3: C → D (1/2 ~ 3/4)
            프로세스 4: D → E (3/4 ~ 1)
            
            → 4개 프로세스가 동시에 다른 범위를 처리!
            → GIL 우회로 진정한 병렬 처리!
        """
        
        self.start_time = Stopwatch.start(zip_path)
        total_attempts = 0
        
        try:
            
            total_combinations = len(characters) ** 6 # 전체 조합 수
            chunk_size = total_combinations // self.num_processes # 범위 분할

            result_queue = Queue() # 결과를 받을 큐 생성

            attempt_queue = Queue() # 실제 시도 횟수 받을 큐 생성
            
            processes = [] # 자식 프로세스 관리용 list
            print(f"[안내] CPU 쓰레드 수: {self.cpu_count}")
            print(f"[안내] 프로세스의 개수는 CPU 쓰레드 개수에 따라, {self.num_processes}개로 지정 되었습니다.")
            
            for i in range(self.num_processes):
                start_idx = i * chunk_size
                end_idx = total_combinations if i == self.num_processes - 1 else (i + 1) * chunk_size
                p = Process(target=unlock_zip, args=(zip_path, start_idx, end_idx, characters, i+1, result_queue, attempt_queue))
                p.start()
                processes.append(p)
            
            # 큐에서 결과를 기다림 (누군가 찾을 때까지)
            try:
                while any(p.is_alive() for p in processes):
                    if not result_queue.empty():
                        password = result_queue.get()
                        break
                # 모든 프로세스 종료
                for process in processes:
                    process.terminate()
                    process.join()
                while not attempt_queue.empty():
                    total_attempts += attempt_queue.get()
                self.found_password = password
            except:
                pass
            
            # 결과 출력
            Stopwatch.stop(self.start_time, self.found_password, total_attempts, self.found_password is not None)
            
            if self.found_password:
                Utils.update_file(output_file, self.found_password)
                return self.found_password
            
            return None
        
        except FileNotFoundError:
            print(f"[오류] ZIP 파일을 찾을 수 없습니다: {zip_path}")
            return None
        
        except zipfile.BadZipFile:
            print(f"[오류] 올바른 ZIP 파일이 아닙니다: {zip_path}")
            return None
        
        except Exception as e:
            print(f"[오류] 예상치 못한 오류 발생: {e}")
            return None


def main():
    """
    프로그램의 시작점.
    
    사용 가능한 크래킹 방법:
        1. 딕셔너리 공격 (자주 사용되는 비밀번호 먼저 시도)
        2. 멀티프로세싱 크래킹 (4개 프로세스가 병렬 처리)
    
    작동 순서:
        1. ZIP 파일 경로 설정
        2. 사용 가능한 문자 목록 생성
        3. 딕셔너리 공격 시도
        4. 멀티프로세싱 크래킹 시도
        5. 결과 출력
    """
    
    characters = string.digits + string.ascii_lowercase # 0-9, a-z 총 36개 문자
    zip_file = 'emergency_storage_key.zip' # ZIP 파일명
    password_output_file = 'password.txt' # 비밀번호를 저장할 파일명
    zip_file_path = Utils.set_file_path(zip_file) # ZIP 파일의 절대 경로 구하기
    
    print("=" * 50)
    print("화성 기지 비상 저장소 잠금 해제")
    print("=" * 50)
    print()
    
    # 1단계: 딕셔너리 공격 시도
    print("[1단계] 딕셔너리 공격 시작...")
    print("-" * 50)
    result = DictionaryAttack.try_common_passwords(zip_file_path, password_output_file)
    
    if result:
        print(f"\n[결과] 생존에 필요한 자원에 접근할 수 있습니다!")
        return
    
    print("\n[1단계 결과] 딕셔너리 공격 실패, 다음 단계로 진행")
    print()
    
    # 2단계: 멀티프로세싱 크래킹 시도
    print("[2단계] 멀티프로세싱 크래킹 시작...")
    print("-" * 50)
    cracker = MultiProcessingCracker()
    result = cracker.crack(zip_file_path, password_output_file, characters)
    
    if result:
        print(f"\n[결과] 생존에 필요한 자원에 접근할 수 있습니다!")
        return
    
    print(f"\n[결과] 비상 저장소 접근 실패...")


if __name__ == '__main__':
    main()