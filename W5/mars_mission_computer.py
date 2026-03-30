import random

class config_reader:
    def __init__(self, file_name):
        # attribute로 config 파일명 설정
        self.file_name = file_name
        # config 파일의 절대 경로 찾기(보안을 위해 private으로 설정)
        self.__file_path = self.__find_file_path()

    '''--- 절대값 경로 반환 메소드 ---'''
    def __find_file_path(self):
        # 1. __file__ 을 통해, __main__의 경로 받아오고, rfind를 통해 뒤에서부터 \가 몇 번째에 있는지 반환
        last_slash_index = __file__.rfind('\\')
        # 2. 윈도우 환경이 아닐 경우, /을 찾아 반환
        if last_slash_index == -1:
            last_slash_index = __file__.rfind('/') 
        # 3. 반환 받은 위치(\ 혹은 /의 위치)의 바로 한 칸 뒤에 파일명 더해 절대값 경로 반환
        base_dir = __file__[:last_slash_index + 1] 
        file_name = base_dir + self.file_name
        return file_name
    
    '''--- 설정 데이터 추출 메소드 ---'''
    # [1 단계] 설정 파일 호출
    def open_file(self):
        with open(self.__file_path, 'r', encoding='utf-8') as file:
            # 1-1. 설정 파일을 호출하여 json_loader 메소드에 인자로 넘기기
            return self.json_loader(file)

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

class DummySensor:
    def __init__(self, config_data):
        self.config_data = config_data
        self.internal_temperature = self.config_data['name'][0]
        self.external_temperature = self.config_data['name'][1]
        self.internal_humidity = self.config_data['name'][2]
        self.external_illuminance = self.config_data['name'][3]
        self.internal_co2 = self.config_data['name'][4]
        self.internal_oxygen = self.config_data['name'][5]

        self.env_values = {
            self.internal_temperature: 0,
            self.external_temperature : 0,
            self.internal_humidity : 0,
            self.external_illuminance : 0,
            self.internal_co2 : 0,
            self.internal_oxygen : 0
        }

    def set_env(self):
        for name_of_key in config_data['name']:
            range_min, range_max = self.config_data['data_ranges'][name_of_key]
            self.env_values[name_of_key] = round(random.uniform(range_min, range_max), 3)

    def get_env(self):
            return self.env_values

'''
if __name__=='__main__': 의 의미
__name__은 현재 실행 중인 파일을 담는 특수 변수
만약 이 파일이 실행된다면, 이 파일은 __main__으로 지정된다.
'''
if __name__=='__main__':
    # 설정 파일
    config_file_name = 'config.json'
    # 설정 파일 읽기 전용 class의 인스턴스 생성
    config_reader = config_reader(config_file_name)
    # 설정 파일 내부 데이터 읽기
    config_data = config_reader.open_file()

    ds = DummySensor(config_data)
    ds.set_env()
    ds.get_env()
