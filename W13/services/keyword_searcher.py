"""저장된 CSV에서 키워드를 검색하는 서비스."""

import csv

from core.config import RECORDS_DIR
from core.utils import Utils


class KeywordSearcher:
    """저장된 CSV 파일에서 키워드를 검색해 결과를 출력한다."""

    def __init__(self, records_dir=RECORDS_DIR):
        """검색기를 초기화한다.

        Args:
            records_dir (str): CSV가 위치한 폴더 이름
        """
        self.records_dir = Utils.set_file_path(records_dir)

    def search(self, keyword):
        """모든 CSV에서 키워드를 검색해 매칭 행을 파일별로 출력한다.

        Args:
            keyword (str): 검색할 단어(부분 일치, 대소문자 무시)
        """
        keyword = keyword.strip()
        if not keyword:
            Utils.print_log('검색', '검색어를 입력해 주세요.')
            return

        if not self.records_dir.exists():
            Utils.print_log('검색', 'records 폴더가 없습니다.')
            return

        csv_files = self._list_csv_files()
        if not csv_files:
            Utils.print_log('검색', '검색할 CSV 파일이 없습니다. 먼저 STT 변환을 진행해 주세요.')
            return

        results = []
        for path in csv_files:
            matches = self._search_file(path, keyword)
            if matches:
                results.append((path.name, matches))

        total = sum(len(matches) for _, matches in results)
        Utils.print_divider()
        if total == 0:
            Utils.print_log('검색', "'" + keyword + "' 검색 결과가 없습니다.")
            Utils.print_divider()
            return

        Utils.print_log('검색', "'" + keyword + "' 검색 결과 (" + str(total) + '건)')
        Utils.print_divider()
        for name, matches in results:
            print('  ' + name)
            for time_str, text in matches:
                print('    ' + time_str + '  ' + text)
        Utils.print_divider()

    def _list_csv_files(self):
        """records/ 안의 csv 파일 경로를 정렬해 반환한다.

        Returns:
            list[Path]: 정렬된 csv 파일 경로 목록
        """
        return sorted(
            p for p in self.records_dir.iterdir()
            if p.suffix.lower() == '.csv'
        )

    def _search_file(self, path, keyword):
        """단일 CSV에서 키워드가 포함된 (시간, 텍스트) 행을 찾는다.

        Args:
            path (Path): 검색할 CSV 파일 경로
            keyword (str): 검색어

        Returns:
            list[tuple[str, str]]: 매칭된 (시간, 텍스트) 행 목록
        """
        keyword_lower = keyword.lower()  # 대소문자 구분 없이 비교하기 위해 소문자로
        matches = []
        try:
            with open(path, 'r', encoding='utf-8-sig', newline='') as f:
                reader = csv.reader(f)
                next(reader, None)  # 헤더 행 건너뛰기
                for row in reader:
                    if len(row) < 2:  # 형식이 깨진 행은 무시
                        continue
                    time_str, text = row[0], row[1]
                    if keyword_lower in text.lower():
                        matches.append((time_str, text))
        except (OSError, csv.Error) as e:  # 읽을 수 없는 파일은 건너뜀
            Utils.print_log('오류', path.name + ' 읽기 실패: ' + str(e))
        return matches
