'''
random 함수 관련 배경 지식 정리

random 함수는 의사 난수 생성기(Pseudo Random Number Generator: PRNG)를 사용

PRNG란?
    시드(seed)라고 불리는 초기값을 기반으로 어떤 알고리즘을 이용해 난수처럼 보이는 숫자열을 생성하는 프로그램

PRNG의 난수 생성 과정
    1. 시드 설정 -> 2. 내부 상태 유지 -> 3. 상태 전이 -> 4. 출력 변환
        1. 시드 설정
        난수를 생성하는 초기값을 설정
        2. 내부 상태 유지
        현재 숫자와 다음 숫자를 만들기 위한 데이터를 저장
        3. 상태 전이
        현재 상태를 꼬아서 다음 상태로 변환
        4. 출력 변환
        사용자가 원하는 형태로 가공
'''
import time
import threading
import platform
import os
import subprocess
import ctypes

#########################################################################
lock = threading.Lock()
#########################################################################

def screan_the_5s_interval_data_and_average_of_5min(json_formatter, RunComputer, config_data):
    # 변수 초기화
    global collect_sensor_data, count_num
    collect_sensor_data = {}    # 데이터 합산용 딕셔너리
    count_num = 0               # 5분 측정용 변수
    # 합산용 딕셔너리 0으로 초기화
    for name_of_sensor_data in config_data['name']:
        collect_sensor_data[name_of_sensor_data] = 0
    # 쓰래딩으로 병렬처리
    try:
        thread_of_screen_data = threading.Thread(
            target=screen_data_by_5s_interval,              # 쓰레딩할 함수 설정
            args=(json_formatter, RunComputer, config_data) # 함수에 전할 인자 설정
            )
        thread_of_calculate_average = threading.Thread(
            target=calculate_average_5min,
            args=(json_formatter, config_data)
            )
        # 쓰래딩 실행
        thread_of_screen_data.start()
        thread_of_calculate_average.start()

    # 인터럽트 발생 시 쓰레드 종료
    except KeyboardInterrupt:
        thread_of_screen_data.join()
        thread_of_calculate_average.join()
        print('Sytem stoped….')

def calculate_average_5min(json_formatter, config_data):
    global collect_sensor_data, count_num
    while True:
        if(count_num == 5):
            with lock:
                for name_of_sensor_data in config_data['name']:
                    collect_sensor_data[name_of_sensor_data] = round(collect_sensor_data[name_of_sensor_data] / count_num, 3)
                time.sleep(1)
                print(f'{count_num*5/60}분간 수집된 데이터들의 평균값:')
                print(f'{json_formatter.print_dicdata_to_jsontype(collect_sensor_data)}\n')
                for name_of_sensor_data in config_data['name']:
                    collect_sensor_data[name_of_sensor_data] = 0
                count_num = 0

def screen_data_by_5s_interval(json_formatter, RunComputer, config_data):
    global collect_sensor_data, count_num
    while True:
        sensor_data = RunComputer.get_sensor_data()
        for name_of_sensor_data in config_data['name']:

            collect_sensor_data[name_of_sensor_data] += sensor_data[name_of_sensor_data]
        count_num += 1
        print(f'{count_num*5}초에 측정된 데이터들의 값:')
        print(f'{json_formatter.print_dicdata_to_jsontype(sensor_data)}\n')
        time.sleep(5)


class random:
    def __init__(self):
        self.seed = hash('김태영') & 0xFFFFFFFF # 1. 시드 설정(시드를 hash함수로 설정한 이유는 맨 밑 주석 참고)
        self.generate_number()

    def generate_number(self):
        x = self.seed # 2. 내부 상태 유지
        # 3. 상태 전이
        x ^= (x << 13) & 0xFFFFFFFF
        x ^= (x >> 17) & 0xFFFFFFFF
        x ^= (x << 5) & 0xFFFFFFFF
        self.seed = x
        # 4. 출력 변환
        return x / 0xFFFFFFFF
    
    def uniform(self, min, max):
        return min + (max - min) * self.generate_number()
    
class file_reader:
    '''--- 절대값 경로 반환 메소드 ---'''
    def __find_file_path(self, file_name):
        # 1. __file__ 을 통해, __main__의 경로 받아오고, rfind를 통해 뒤에서부터 \가 몇 번째에 있는지 반환
        last_slash_index = __file__.rfind('\\')
        # 2. 윈도우 환경이 아닐 경우, /을 찾아 반환
        if last_slash_index == -1:
            last_slash_index = __file__.rfind('/') 
        # 3. 반환 받은 위치(\ 혹은 /의 위치)의 바로 한 칸 뒤에 파일명 더해 절대값 경로 반환
        base_dir = __file__[:last_slash_index + 1] 
        file_name = base_dir + file_name
        return file_name
    
    '''--- 설정 데이터 추출 메소드 ---'''
    # [1 단계] 설정 파일 호출
    def open_file(self, file_name):
        file_path = self.__find_file_path(file_name)
        with open(file_path, 'r', encoding='utf-8') as file:
            # 1-1. 설정 파일을 호출하여 json_loader 메소드에 인자로 넘기기
            if '.' in file_name:
                file_type = file_name.strip().split('.')[1]
            else:
                print("파일명을 확장자를 포함하여 설정해주세요.")
                return None
            if file_type == "json":
                return self.json_loader(file)
            elif file_type == "txt":
                return self.txt_loader(file)
            else:
                return None

    def json_loader(self, file_obj):
        # [2 단계] 글자 공급기
        def get_chars():
            while True:
                # 2-1 파일 객체에서 한 글자만 읽기(한 글자만 읽은 이유는 메모리 보호)
                char = file_obj.read(1)
                # 2-2 만약, 파일의 끝에 도달했다면(EOF) 종료
                if not char:
                    break
                yield char
        # 2-3 Generator 함수 변수 설정(그래야만 상태를 유지하며 다음 글자 읽기 가능, 해깔리면 제너레이터 함수의 정의에 대해 잘 생각해보기)
        char_gen = get_chars()
        # 2-4 next 함수를 이용해 다음 글자 저장
        current_char = next(char_gen, None)

        # [3 단계] 의미 단위 추출기(토큰화)
        def get_token():
            # 3-1 해당 변수가 로컬 변수가 아닌 외부 변수임을 지정함으로써, 외부 변수 current_char의 값의 수정이 가능하도록 설정
            nonlocal current_char

            # 3-2 쓸데없는 공백 처리 : 글자가 있고, 줄바꿈, 공백이 있을 경우 다음 글자 넘어가기
            while current_char and current_char.isspace():
                current_char = next(char_gen, None)
            # 3-3 EOF 처리 : None return
            if not current_char: 
                return None
            # 3-4 구분자 처리 : ('{', '}', '[', ']', ':', ',') 가 나올 경우, 다음 글자 넘어가고, 구분자 반환
            if current_char in '{}[]:,':
                token = current_char
                current_char = next(char_gen, None)
                return token
            # 3-5 문자열 처리 : 따옴표가 나올 경우, 다음 따옴표가 나올 때까지 글자 모으기
            if current_char == '"':
                res = []
                # 3-5-1 따옴표 하나 건너뛰기
                current_char = next(char_gen, None)
                # 3-5-2 만약, 글자가 있고, 따옴표가 아니라면, 뒤에 글자 계속 합치기
                while current_char and current_char != '"':
                    res.append(current_char)
                    current_char = next(char_gen, None)
                # 3-5-3 반복문 후 나온 따옴표 건너뛰기
                current_char = next(char_gen, None)
                # 3-5-4 리스트에 담긴 글자들을 하나의 문자열로 합쳐서 반환
                return "".join(res)
            
            # 3-6. 일반 값 처리: 숫자(int, float)나 null, true, false 등을 처리
            res = []
            # 3-6-1 '{}[]:, \n\t\r' 구분자 만나기 전까지 글자 합치기
            while current_char and current_char not in '{}[]:, \n\t\r':
                res.append(current_char)
                current_char = next(char_gen, None)
            # 3-6-2 리스트에 리스트에 담긴 글자들을 하나의 문자열로 합치기
            word = "".join(res)
            # 3-6-3 문자열로 된 숫자를 실제 파이썬 숫자로 변환 시도
            try:
                # 3-6-4 소수점이 있다면 실수형으로 없으면 정수형으로 숫자가 아니면 문자열로 반환
                if '.' in word: 
                    return float(word)
                return int(word)
            except ValueError:
                return word
            
        # [4 단계] 구조 조립기(파싱)
        def parse(first_token):
            # 4-1 딕셔너리로 시작하는 구조일 경우
            if first_token == '{':
                res_dict = {}
                while True:
                    # 4-1-1 계속 글자를 가져오기
                    token = get_token()
                    # 4-1-2 빈 중괄호일 경우
                    if token == '}':
                        break
                    # 4-1-3 키 값을 따로 저장 후, get_token()을 실행해서 : 버림
                    key = token
                    get_token()
                    # 4-1-4 값 부분에 리스트 혹은 딕셔너리가 또 있을 수 있기에 재귀함수로 값 저장
                    res_dict[key] = parse(get_token())
                    # 4-1-5 딕셔너리가 끝날 경우, 반복문 종료 후 조립된 딕셔너리 반환
                    next_t = get_token()
                    if next_t == '}': 
                        break
                return res_dict
                
            # 4-2 리스트로 시작하는 구조일 경우
            elif first_token == '[':
                res_list = []
                while True:
                    token = get_token()
                    if token == ']':
                        break
                    # 4-2-1 딕셔너리 떄와 같이 가져온 값을 token에 저장 후 리스트에 추가
                    res_list.append(parse(token))
                    # 4-1-5 리스트가 끝날 경우, 반복문 종료 후 조립된 리스트 반환
                    next_t = get_token()
                    if next_t == ']':
                        break
                return res_list
            # 4-3 단일 값(숫자, 문자열)일 경우
            else:   
                return first_token
        # 1-2 get_token함수가 실행 후, 그 반환 값을 parse 함수의 인자로 전달(토큰화 후 파싱)
        return parse(get_token())

    def txt_loader(self, file_obj):
        settings = {}
        for line in file_obj:
            if not line or line.startswith('#'):# startswith를 이용해 #으로 처리된 주석은 넘어감
                continue
            if '=' in line:
                key, value = line.strip().split('=')
                settings[key] = (value.strip().upper() == 'TRUE')
        return settings

class JSONFormatter:
    def print_dicdata_to_jsontype(self, data):
        # 파이썬 객체를 JSON 문자열로 변환
        json_string = self.json_dumper(data)
        return json_string

    def __escape_string(self, s):
        # JSON에서 특별한 의미를 갖는 문자들을 처리
        substitutions = {
            '\\': '\\\\', #역슬레시
            '"': '\\"', # 큰따움표
            '\b': '\\b', # 백스페이스(커서를 왼쪽으로 한칸 이동)
            '\f': '\\f', # 다음 페이지(용지) 넘김
            '\n': '\\n', # 줄바꿈
            '\r': '\\r', # 캐리지 리턴(커서를 맨 앞으로 이동)
            '\t': '\\t', # 탭
        }
        for char, sub in substitutions.items():
            s = s.replace(char, sub)
        return f'"{s}"'

    '''--- 데이터 직렬화(JSON 변환) 메소드 ---'''
    def json_dumper(self, data, indent=4, level=0):
        # 들여쓰기를 위한 공백 계산
        space = " " * (indent * level)
        next_space = " " * (indent * (level + 1))
        
        # 1. 딕셔너리 처리
        if isinstance(data, dict):
            if not data: return "{}"
            items = []
            for key, value in data.items():
                # 키도 문자열이므로 이스케이프 처리
                escaped_key = self.__escape_string(str(key))
                # 값은 재귀적으로 처리 (level + 1)
                transformed_value = self.json_dumper(value, indent, level + 1)
                items.append(f"{next_space}{escaped_key}: {transformed_value}")
            return "{\n" + ",\n".join(items) + "\n" + space + "}"
        
        # 2. 리스트 처리
        elif isinstance(data, list):
            if not data: return "[]"
            items = [f"{next_space}{self.json_dumper(item, indent, level + 1)}" for item in data]
            return "[\n" + ",\n".join(items) + "\n" + space + "]"
        
        # 3. 문자열 처리 (이스케이프 적용)
        elif isinstance(data, str):
            return self.__escape_string(data)
        
        # 4. 기타 기본 타입 처리
        elif isinstance(data, bool):
            return "true" if data else "false"
        elif data is None:
            return "null"
        else:
            # 숫자(int, float) 등은 그대로 반환
            return str(data)
        
class DummySensor:
    def __init__(self, config_data):
        self.config_data = config_data
        self.env_values = {}
        self.set_env()

    def set_env(self):
        for name_of_key in config_data['name']:
            range_min, range_max = self.config_data['data_ranges'][name_of_key]
            self.env_values[name_of_key] = round(random.uniform(range_min, range_max), 3)

    def get_env(self):
            return self.env_values        

class MissionComputer():
    def __init__(self, ds,config_data):
        self.ds_instance = ds
        self.config_data = config_data
        self.os_type = platform.system()

    def get_sensor_data(self):
        ds.set_env()
        return ds.get_env()
    
    def get_total_memory(self):
        try:
            if self.os_type == "Windows":
                command = 'powershell "(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory"'
                output = subprocess.check_output(command, shell=True).decode('utf-8').strip()
                if output:
                    return round(int(output) / (1024**3), 2)
            elif self.os_type == "Linux":
                with open('/proc/meminfo', 'r') as f:
                    for line in f:
                        if "MemTotal" in line:
                            total_kb = int(line.split()[1])
                            return round(total_kb / (1024**2), 2)

            elif self.os_type == "Darwin":
                command = "sysctl -n hw.memsize"
                total_bytes = int(subprocess.check_output(command, shell=True).decode().strip())
                return round(total_bytes / (1024**3), 2)

        except Exception as e:
            return f"정보를 가져오는데 실패했습니다: {e}"
        
    
    def get_mission_computer_info(self, json_formatter, setting_of_choose_computer_info, computer_info_name):
        computer_info = {}
        for key, value in setting_of_choose_computer_info.items():
            if value:
                if key == computer_info_name[0]:
                    computer_info[key] = self.os_type
                elif key == computer_info_name[1]:
                    computer_info[key] = platform.release()
                elif key == computer_info_name[2]:
                    computer_info[key] = platform.machine()
                elif key == computer_info_name[3]:
                    computer_info[key] = os.cpu_count()
                elif key == computer_info_name[4]:
                    memory_size = self.get_total_memory()
                    computer_info[key] = memory_size
        print(json_formatter.print_dicdata_to_jsontype(computer_info))

    def get_windows_memory(self):
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_uint),
                ("dwMemoryLoad", ctypes.c_uint),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]
        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
        return stat.dwMemoryLoad

    def get_mission_computer_load(self, json_formatter, setting_of_choose_computer_info, computer_realtime_info_name):
        realtime_computer_info = {}
        try:
            if self.os_type == "Windows":
                for key, value in setting_of_choose_computer_info.items():
                    if value:
                        if key == computer_realtime_info_name[0]:
                            cmd = 'typeperf "\\Processor(_Total)\\% Processor Time" -sc 1'
                            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode('utf-8', errors='ignore')
                            lines = output.splitlines()
                            if len(lines) > 2:
                                val = lines[2].split(',')[1].replace('"','')
                                realtime_computer_info[key] = round(float(val), 2)
                        elif key == computer_realtime_info_name[1]:
                            realtime_computer_info[key] = self.get_windows_memory()

            elif self.os_type == "Linux":
                for key, value in setting_of_choose_computer_info.items():
                    if value:
                        if key == computer_realtime_info_name[0]:
                            cmd_cpu = r"vmstat 1 2 | tail -n 1 | awk '{print 100 - $15}'"
                            realtime_computer_info[key] = float(subprocess.check_output(cmd_cpu, shell=True).decode().strip())
                        elif key == computer_realtime_info_name[1]:
                            # 2. 메모리 사용량: free 명령어의 결과를 비율로 계산
                            cmd_mem = r"free | grep Mem | awk '{print $3/$2 * 100.0}'"
                            realtime_computer_info[key] = float(subprocess.check_output(cmd_mem, shell=True).decode().strip())

            elif self.os_type == "Darwin":
                for key, value in setting_of_choose_computer_info.items():
                    if value:
                        if key == computer_realtime_info_name[0]:
                            # 1. CPU 사용량: 로드 애버리지를 활용하거나 ps의 cpu 합계를 이용
                            # 시스템 전체 프로세스의 CPU 점유율 합산 (가장 범용적임)
                            cmd_cpu = r"ps -A -o %cpu | awk '{s+=$1} END {print s}'"
                            realtime_computer_info[key] = float(subprocess.check_output(cmd_cpu, shell=True).decode().strip())
                        elif key == computer_realtime_info_name[1]:
                            # 2. 메모리 사용량: 전체 프로세스의 메모리 점유율 합산
                            cmd_mem = r"ps -A -o %mem | awk '{s+=$1} END {print s}'"
                            realtime_computer_info[key] = float(subprocess.check_output(cmd_mem, shell=True).decode().strip())
        except Exception:
            for key in realtime_computer_info.keys():
                realtime_computer_info[key] = None
        print(json_formatter.print_dicdata_to_jsontype(realtime_computer_info))



'''
if __name__=='__main__': 의 의미
    __name__은 현재 실행 중인 파일을 담는 특수 변수
    만약 이 파일이 실행된다면, 이 파일은 __main__으로 지정된다.
'''
if __name__=='__main__':
    # 랜덤 클래스 인스턴스 생성
    random = random()
    # 설정 파일 이름 저장
    config_file_name = 'config.json'
    setting_file_name = 'setting.txt'

    # 설정 파일 읽기 전용 class의 인스턴스 생성
    file_reader = file_reader()

    # 설정 파일 내부 데이터 읽기
    config_data = file_reader.open_file(config_file_name)
    # 인스턴스 생성
    ds = DummySensor(config_data)
    # MissionComputer 인스턴스 생성 후 ds 인스턴스를 인자로 설정
    RunComputer = MissionComputer(ds, config_data)
    # dict 데이터를 json 형식으로 변경하여 return 하는 JSONFormatter 인스턴스 생성
    json_formatter = JSONFormatter()

    ## 5초마다 데이터 json 형식으로 출력 및 5분 후 데이터들의 평균 출력
    # screan_the_5s_interval_data_and_average_of_5min(json_formatter, RunComputer, config_data)

    setting_of_choose_computer_info = file_reader.open_file(setting_file_name)
    computer_info_name = ['os_type', 'os_version', 'cpu_arch', 'cpu_cores', 'memory_size']
    computer_realtime_info_name = ['cpu_usage', 'mem_usage']
    RunComputer.get_mission_computer_info(json_formatter, setting_of_choose_computer_info, computer_info_name)
    RunComputer.get_mission_computer_load(json_formatter, setting_of_choose_computer_info, computer_realtime_info_name)

    ## random 클래스 테스트 코드
    # random = random()
    # print(f'value of hash : {random.seed}')
    # print(f'random value : {random.generate_number()}')
    # print(f'random value : {random.uniform(10, 20)}')

'''
hash 함수 배경 지식 정리
hash 함수란, 어떤 데이터를 고정된 길이의 고유한 값으로 변환하는 알고리즘
해시값(hash value)는 hash 함수로 hashing 되어 나온 고유한 값

활용 사례
1. 자료구조 (Hash Table): 데이터 검색 및 저장 시, 키(Key)를 해시 함수를 통해 인덱스로 변환하여 O(1)에 근접한 속도로 데이터를 관리
2. 암호 및 보안: 비밀번호 저장, 전자 서명 등에서 원본 내용을 숨기기 위해 사용
3. 무결성 검사 (Checksum): 데이터가 전송 중 변조되지 않았는지 확인할 때 원본 파일의 해시값과 수신된 파일의 해시값을 비교

문제점
1. 해시 충돌(Hash Collision)
    생성할 수 있는 해시의 값은 한계가 있기에 다른 값을 해싱해도 같은 값이 나오는 경우가 있음
    해시 플러딩(Hash Flooding)
        해시 함수의 알고리즘을 파악해 해시 충돌을 일으키는 더미 데이터를 서버에 던지는 공격(일종의 DoS)
    해시 플러딩을 막기 위해 python에서는 hash 함수 실행 시 내부적으로 무작위 시드값을 해시 계산에 섞어 넣음
2. 데어터 순서 파괴(No Range Search)
    빠른 검색을 위해 마구잡이로 저장을 하기 때문에 sort나 범위 검색이 불가능
3. 리해싱(Rehashing)의 부담
    배열이 꽉 차서 큰 배열로 변경 할 경우 해싱 한 데이터를 다시 해싱해서 옮겨야 함    
 '''

