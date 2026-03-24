# 파일 경로를 찾는 함수
def find_file_path(file_name):
    last_slash_index = __file__.rfind('\\') # rfind를 통해서 경로 찾기
    if last_slash_index == -1:
        last_slash_index = __file__.rfind('/') # 맥과 같은 os 대비
    base_dir = __file__[:last_slash_index + 1] # dir 파일 경로 저장
    file_path = base_dir + file_name
    return file_path

# 설정 파일을 읽어내는 함수
def read_config_file(config_file_path, key):
    found_value='' # 미리 초기화를 함으로써 오류 줄임
    try:
        with open(config_file_path, 'r', encoding='utf-8') as config:
            for line in config:
                line = line.strip()
                if not line or line.startswith(';') or line.startswith('#'):#startswith를 이용해 ;, #으로 처리된 주석은 넘어감
                    continue
                if key in line and '=' in line: # key 값과 '='값이 line에 포함할 경우
                    found_value = line.split('=')[1].strip() # split을 이용해 '=' 을 기준으로 나누고 1번째 원소(value)를 저장
                    break
        if not found_value: #키 값이 없을 경우 오류 처리
            print(f"경고: '{key}' 항목이 설정 파일에 없습니다.")
    except FileNotFoundError:
        print(f"오류: 설정 파일({config_file_path})을 찾을 수 없습니다.")
    except PermissionError:
        print(f"오류: 파일 읽기 권한이 없습니다.")
    except UnicodeDecodeError:
        print(f"오류: 파일 인코딩 형식이 잘못되었습니다. UTF-8로 저장해 주세요.")
    except Exception as e:
        print(f"예상치 못한 시스템 오류 발생: {e}")        
    
    return found_value

def print_file_data(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                print(line, end='')
    except FileNotFoundError:
        print(f"오류: 파일({file_path})을 찾을 수 없습니다.")
    except PermissionError:
        print(f"오류: 파일 읽기 권한이 없습니다.")
    except UnicodeDecodeError:
        print(f"오류: 파일 인코딩 형식이 잘못되었습니다. UTF-8로 저장해 주세요.")
    except Exception as e:
        print(f"예상치 못한 시스템 오류 발생: {e}")

def sort_data(file_path, sort_key, is_reverse):
    data_list = []
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            header = file.readline().strip().split(',') # 헤더만 따로 분리하여 list에 저장 (읽을 파일이 너무 클 경우를 대비한 readline)
            for line in file:
                line = line.strip()
                if not line: continue # 파일 끝까지 다 읽었다면, 넘어가기
                values = line.split(',') # csv 한 줄을 ,를 기준으로 나누고 리스트로 저장
                row_dict = {}
                for i in range(len(header)): # 헤더 리스트의 갯수를 이용해서 반복문 사용
                    val = values[i].strip()
                    # csv 파일을 읽으면 숫자든 단어든 모두 string으로 처리하는 문제를 해결하기 위해
                    try:
                        val = float(val) # 값이 숫자일 경우 정상처리, 값이 단어일 경우 오류 발생
                    except ValueError:
                        pass # 값이 단어일 경우 오류로 처리해서 pass 함으로써 string으로 처리
                    row_dict[header[i]] = val
                data_list.append(row_dict)
        print(data_list) # 읽어 드린 csv를 출력하는 테스트 코드
        # 딕셔너리를 원소로 가지는 리스트를 정렬할 때, lambda식을 이용해서 특정 컬럼을 키로하는 값을 가져와서 정렬
        # 특정 컬럼명을 키로 하는 원소가 없을 경우를 대비하여  get 안에 0 설정
        data_list.sort(key=lambda x: x.get(sort_key, 0), reverse=is_reverse) 
        return data_list
    except FileNotFoundError:
        print(f"오류: 파일({file_path})을 찾을 수 없습니다.")
    except PermissionError:
        print(f"오류: 파일 읽기 권한이 없습니다.")
    except UnicodeDecodeError:
        print(f"오류: 파일 인코딩 형식이 잘못되었습니다. UTF-8로 저장해 주세요.")
    except Exception as e:
        print(f"데이터 처리 중 오류 발생: {e}")


def save_to_csv(data_list, header, file_path):
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(','.join(header) + '\n') # header 리스트의 원소들 사이에 ,를 넣어서 결합, 마지막은 줄바꿈
            for row in data_list:
                row_values = []
                for h in header:
                    row_values.append(str(row.get(h, ''))) # 받은 리스트의 딕셔너리의 값들을 꺼내 string으로 형 변환 후, row_values 리스트로 저장
                file.write(','.join(row_values) + '\n') # row_values 리스트의 원소들 사이에 ,를 넣어서 결합. 그 후 파일에 write
    except PermissionError:
        print(f"오류: 파일 읽기 권한이 없습니다.")
    except Exception as e:
        print(f"저장 중 예상치 못한 오류 발생: {e}")


def search_data(file_path, target_column, target_value):
    data_list = []
    filtered_results = []
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            header = file.readline().strip().split(',')
            for line in file:
                line = line.strip()
                if not line: continue
                values = line.split(',')
                row_dict = {}
                for i in range(len(header)):
                    val = values[i].strip()
                    try:
                        val = float(val)
                    except ValueError:
                        pass
                    row_dict[header[i]] = val
                data_list.append(row_dict)
                # 이 위는 sort_data 함수와 동일
                ########################################
            for row in data_list:
                    val = row.get(target_column)
                    if isinstance(val, (int, float)): # isinstance를 이용해 데이터 타입을 비교해서 숫자만 비교
                        if val >= target_value:
                            print(f"- {row.get('Substance', 'Unknown'):<20}: {val}") #:<20을 이용해 Substance 값을 출력하는 부분의 사이즈 제한(그냥 이쁘게 나오게 하려고)
                            filtered_results.append(row) #
                    else:
                        continue # 단어는 비교 불가능하므로 넘어감
        save_choice = input("검색 결과를 CSV 파일로 저장하시겠습니까? (y/n): ")
        if save_choice.lower() == 'y':
            output_file_name = "Mars_Base_Inventory_danger.csv"
            output_path = find_file_path(output_file_name)
            csv_header = list(filtered_results[0].keys()) # Mars_Base_Inventory_danger 파일도 Mars_Base_Inventory_List.csv와 같이 맨 위에 header를 만들기 위해 헤더값만 리스트 형식으로 저장
            save_to_csv(filtered_results, csv_header, output_path)
        else:
            print("저장을 취소했습니다.")
    except Exception as e:
        print(e)


if __name__ == "__main__":
    config_file_name = 'config.ini'
    key_of_inventory_file = 'inventory_file'
    key_of_sort_target = 'sort_target'
    key_of_search_target= 'search_target'
    key_of_sort_type = 'sort_descending'
    key_of_search_baseline_value = 'search_baseline_value'


    config_file_path = find_file_path(config_file_name)

    inventory_file_name = read_config_file(config_file_path, key_of_inventory_file)
    inventory_file_path = find_file_path(inventory_file_name)

    sort_target = read_config_file(config_file_path, key_of_sort_target)
    sort_descending_str = read_config_file(config_file_path, key_of_sort_type)
    search_target = read_config_file(config_file_path, key_of_search_target)
    search_baseline_value = float(read_config_file(config_file_path, key_of_search_baseline_value))

    is_descending = sort_descending_str.lower() == 'true'


    print_file_data(inventory_file_path)

    edit_file_set = sort_data(inventory_file_path, sort_target, is_descending)
    for row in edit_file_set:
        print(row[sort_target])

    print(search_data(inventory_file_path, search_target, search_baseline_value))
