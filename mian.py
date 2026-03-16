
def read_log_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            log_data=file.readlines()
        return log_data
    except FileNotFoundError:
        print(f"에러: '{file_path}'를 찾을 수 없습니다.")
        return None
    except Exception as e:
        print(f'알 수 없는 에러가 발생했습니다: {e}')
        return None
    
def save_to_md(log_lines, start_num, end_num, output_path='extracted_log.md'):
    try:
        selected_lines=log_lines[start_num-1:end_num]
        with open(output_path, 'w', encoding='utf-8') as md_file:
            md_file.write(f'# 로그 추출 리포트 ({start_num}번 ~ {end_num}번 줄)\n\n')
            for line in selected_lines:
                md_file.write(line)
            md_file.write('\n')
        print(f"\n성공: '{output_path}' 에 저장되었습니다.")
    except Exception as e:
        print(f'저장 중 오류 발생: {e}')


if __name__=="__main__":
    file_path='mission_computer_main.log'
    log_lines=read_log_file(file_path)

    if log_lines:
        print('--- mission computer main log ---')
        for i, line in enumerate(log_lines, start=1):
            print(f'{i}: {line}\n', end='')
        print('\n---------------------------------')

        try:
            start_num=int(input('\n추출을 시작할 줄 번호 입력하세요: '))
            end_num=int(input('추출을 끝낼 줄 번호를 입력하세요: '))
            save_to_md(log_lines, start_num, end_num)
        except ValueError:
            print('숫자만 입력해주세요.')