"""requirements.txt 기반 의존성 관리 서비스."""

import importlib
import importlib.metadata
import subprocess
import sys
from types import ModuleType

from core.utils import Utils


class LibraryManager:
    """requirements.txt 기반 의존성 확인/설치/임포트를 담당한다."""

    def __init__(self, requirements_file: str) -> None:
        """의존성 관리자를 초기화한다."""
        self.requirements_file = requirements_file
        self.req_path = Utils.set_file_path(requirements_file)

    def ensure(self) -> None:
        """필요한 라이브러리가 모두 설치됐는지 확인하고, 없으면 설치 여부를 묻는다.

        설치를 거부하거나 설치 후에도 누락된 패키지가 있으면 프로그램을 종료한다.
        """
        if not self.req_path.exists():
            Utils.print_log('오류', self.requirements_file + ' 파일을 찾을 수 없습니다.')
            sys.exit(1)

        packages = self._parse_requirements()
        if not packages:
            Utils.print_log('라이브러리', self.requirements_file + ' 에 명시된 라이브러리가 없습니다.')
            return

        missing = self._find_missing(packages)
        if not missing:
            Utils.print_log('라이브러리', '필요한 라이브러리 확인 완료 (' + ', '.join(packages) + ')')
            return

        Utils.print_log('경고', '설치되지 않은 라이브러리: ' + ', '.join(missing))
        while True:
            answer = Utils.input_with_log('입력', '지금 설치하시겠습니까? (y/n) >> ')
            if answer.lower() == 'y':
                self._install_all()
                still_missing = self._find_missing(packages)
                if still_missing:
                    Utils.print_log('오류', '설치 후에도 다음 라이브러리를 찾을 수 없습니다: ' + ', '.join(still_missing))
                    sys.exit(1)
                Utils.print_log('설치', '모든 라이브러리 설치 완료')
                return
            elif answer.lower() == 'n':
                Utils.print_log('종료', '라이브러리 없이는 실행할 수 없습니다. 프로그램을 종료합니다.')
                sys.exit(0)
            else:
                Utils.print_log('오류', 'y 또는 n을 입력해 주세요.')

    def load(self, name: str) -> ModuleType:
        """이름으로 모듈을 임포트해 반환한다."""
        return importlib.import_module(name)

    def _parse_requirements(self) -> list[str]:
        """requirements.txt를 파싱해 버전 지정자를 제외한 패키지 이름 목록을 반환한다."""
        packages = []
        with open(self.req_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                name = line.split('==')[0].strip()  # 버전 지정자(==) 앞의 이름만 취함
                if name:
                    packages.append(name)
        return packages

    def _find_missing(self, packages: list[str]) -> list[str]:
        """설치되지 않은 패키지 목록을 반환한다."""
        missing = []
        for pkg in packages:
            try:
                importlib.metadata.distribution(pkg)
            except importlib.metadata.PackageNotFoundError:
                missing.append(pkg)
        return missing

    def _install_all(self) -> None:
        """requirements.txt에 명시된 라이브러리를 pip으로 설치한다.

        설치에 실패하면 프로그램을 종료한다.
        """
        Utils.print_log('설치', self.requirements_file + ' 에서 라이브러리 설치를 시작합니다...')
        Utils.print_divider()
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-r', str(self.req_path)]
        )
        Utils.print_divider()
        if result.returncode != 0:
            Utils.print_log('오류', '설치에 실패했습니다.')
            sys.exit(1)
