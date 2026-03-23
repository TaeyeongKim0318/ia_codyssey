def find_file_path(file_name):
    last_slash_index = __file__.rfind('\\')
    if last_slash_index == -1:
        last_slash_index = __file__.rfind('/')
    base_dir = __file__[:last_slash_index + 1]
    file_path = base_dir + file_name
    return file_path

def read_config_file(config_file_path, key):
    found_value=''
    try:
        with open(config_file_path, 'r', encoding='utf-8') as config:
            for line in config:
                line = line.strip()
                if not line or line.startswith(';') or line.startswith('#'):
                    continue
                if key in line and '=' in line:
                    found_value = line.split('=')[1].strip()
                    break
        if not found_value:
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
            file.write(','.join(header) + '\n')
            for row in data_list:
                row_values = []
                for h in header:
                    row_values.append(str(row.get(h, '')))
                file.write(','.join(row_values) + '\n')
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
            for row in data_list:
                    val = row.get(target_column)
                    if isinstance(val, (int, float)):
                        if val >= target_value:
                            print(f"- {row.get('Substance', 'Unknown'):<20}: {val}")
                            filtered_results.append(row)
                    else:
                        continue
        save_choice = input("검색 결과를 CSV 파일로 저장하시겠습니까? (y/n): ")
        if save_choice.lower() == 'y':
            output_file_name = "search_result.csv"
            output_path = find_file_path(output_file_name)
            csv_header = list(filtered_results[0].keys())
            save_to_csv(filtered_results, csv_header, output_path)
        else:
            print("저장을 취소했습니다.")
            return filtered_results
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


    # print_file_data(inventory_file_path)

    # edit_file_set = sort_data(inventory_file_path, sort_target, is_descending)
    # for row in edit_file_set:
    #     print(row[sort_target])

    result_data = search_data(inventory_file_path, search_target, search_baseline_value)
    print(result_data[0])