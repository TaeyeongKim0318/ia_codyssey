import time

class Utils:
    @staticmethod
    def set_file_path(file_name):
        last_slash_index = __file__.rfind('\\')
        if last_slash_index == -1:
            last_slash_index = __file__.rfind('/')
        base_dir = __file__[:last_slash_index + 1]
        file_path = base_dir + file_name
        return file_path

    @staticmethod
    def update_file(file_name, content):
        try:
            file_path = Utils.set_file_path(file_name)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"[저장] {file_path}에 저장 완료")
        except IOError as e:
            print(f"[오류] 파일 저장 실패: {e}")
        except FileNotFoundError:
            print(f"[오류] '{file_path}' 파일 식별 불가")
            return None
        except Exception as e:
            print(f'[오류] 알 수 없는 에러가 발생\n{e}')
            return None

    @staticmethod
    def read_file(file_name) -> str:
        try:
            file_path = Utils.set_file_path(file_name)
            with open(file_path, 'r', encoding="utf-8") as f:
                content = ""
                line = f.readline()         # 첫 줄 읽기
                while line:                 # 줄이 있는 동안 반복
                    content += line
                    line = f.readline()     # 다음 줄 읽기
            print(f"[읽기] {file_path}의 파일 읽기 완료")
            return content
        except IOError as e:
            print(f"[오류] 파일 읽기 실패: {e}")
        except FileNotFoundError:
            print(f"[오류] '{file_path}' 파일 식별 불가")
            return None
        except Exception as e:
            print(f'[오류] 알 수 없는 에러가 발생\n{e}')
            return None
    
    @staticmethod
    def start() -> float:
        print("-" * 50)
        start_time = time.time()
        print(f"[시작] {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}")
        print("-" * 50)
        return start_time

    @staticmethod
    def stop(start_time):
        end_time = time.time()
        elapsed_time = end_time - start_time
        hours = int(elapsed_time // 3600)
        minutes = int((elapsed_time % 3600) // 60)
        seconds = elapsed_time % 60
        print(f"[종료] {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))}")
        print(f"[경과 시간] {hours}시간 {minutes}분 {seconds:.2f}초")


class caesar_chipher_decoder:
    @staticmethod
    def caesar_cipher_decode(target_text):
        start_time = Utils.start()
        results = []
        for shift in range(1, 27):
            decoded = []
            for char in target_text:
                if char.isalpha():
                    base = ord('A') if char.isupper() else ord('a')
                    decoded_char = chr((ord(char) - base - shift) % 26 + base)
                    decoded.append(decoded_char)
                else:
                    decoded.append(char)
            decoded_text = ''.join(decoded)
            print(f"자리수 {shift:2d}: {decoded_text}")
            results.append((shift, decoded_text))
        Utils.stop(start_time)
        return results
    
    @staticmethod
    def caesar_cipher_decode_auto(target_text, word_dict):
        start_time = Utils.start()
        for shift in range(1, 27):
            decoded = []
            for char in target_text:
                if char.isalpha():
                    base = ord('A') if char.isupper() else ord('a')
                    decoded_char = chr((ord(char) - base - shift) % 26 + base)
                    decoded.append(decoded_char)
                else:
                    decoded.append(char)
            decoded_text = ''.join(decoded)

            words = decoded_text.lower().split()
            matched = [w for w in words if w in word_dict]
            match_ratio = len(matched) / len(words) if words else 0

            if match_ratio >= 0.5:
                print(f"[시도] 자리수 {shift:2d} : {decoded_text}  ({len(matched)}/{len(words)}개 단어 일치) → 반복 중단!")
                print(f"[종료] 단어 일치로 반복 중단")
                return shift, decoded_text
            else:
                print(f"[시도] 자리수 {shift:2d}: {decoded_text}  ({len(matched)}/{len(words)}개 단어 일치)")
        Utils.stop(start_time)
        return None, None
    
def save_result(shift, decoded_text, decoder_mode):
        template = Utils.read_file('result_template.md')
        content = template.format(shift=shift, decoded_text=decoded_text, mode = decoder_mode)
        Utils.update_file('result.txt', content)

if __name__ == '__main__':
    print("=" * 50)
    print("카이사르 암호 해독기")
    print("=" * 50)
    print()

    # 사전 로드
    word_dict = set(Utils.read_file('words.txt').splitlines())

    # 암호 파일 읽기
    cipher_text = Utils.read_file('password.txt').strip()
    print(f"[사전] {len(cipher_text)}개 단어 로드 완료")
    
    while True:
        print("\n[입력] 디코더 모드를 선택해주세요")
        decoder_mode = int(input("수동: 1, 자동: 2 >> "))
        if decoder_mode in (1, 2):
            break
        print("[오류] 1 또는 2만 입력 가능합니다.")


    if decoder_mode == 1:
        # 전체 결과 출력
        all_results = caesar_chipher_decoder.caesar_cipher_decode(cipher_text)
    elif decoder_mode == 2:
        # 보너스: 자동 탐지
        auto_shift, auto_text = caesar_chipher_decoder.caesar_cipher_decode_auto(cipher_text, word_dict)

    # 눈으로 확인 후 저장
    if decoder_mode == 1:
        while True:
            chosen_shift = int(input("\n[입력] 몇 번째 자리수가 정답인가요? "))
            if chosen_shift in range(1, 27):
                break
            print("[오류] 1~26 만 입력 가능합니다.")
        chosen_text = all_results[chosen_shift - 1][1]
        decoder_mode = "수동 디코더로 해독"
        save_result(chosen_shift, chosen_text, decoder_mode)
    elif decoder_mode == 2:
        decoder_mode = "자동 디코더로 해독"
        save_result(auto_shift, auto_text, decoder_mode)