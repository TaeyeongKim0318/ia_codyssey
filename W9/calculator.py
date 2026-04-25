"""
iPhone 스타일 계산기 (PyQt6)
================================

[요구사항 요약]
 1. 출력창은 ''으로 초기화 (화면에는 "0" 으로 보이게 처리)
 2. AC 버튼 클릭 / Esc / Delete 키 → All Clear (수식창까지 초기화)
 3. 숫자 버튼·키 → 출력창에 숫자 표시
 4. 출력 숫자는 3자리마다 ',' 로 구분
 5. 숫자가 길어지면 폰트 자동 축소 (잘리지 않도록 실제 픽셀 폭 측정)
 6. 숫자 후 연산자 → "숫자+연산자" 가 수식창으로 이동, 출력창은 비움
 7. 숫자 없이 연산자 → "0+연산자" 로 수식창에 기록
 8. 연산자를 연속으로 누르면 수식창의 마지막 연산자만 교체
 9. 수식과 숫자가 모두 있을 때 연산자 → 먼저 계산 후 결과 + 새 연산자
10. +/- → 부호 전환, 음수는 괄호로 묶음
11. %  → 출력창 값을 100 으로 나눈 소수값
12. '.' → 출력창 숫자 뒤에 소수점 추가
13. '.' 뒤 숫자 입력 → 소수 이어쓰기
14. '.' 뒤에 연산자 입력 → '.' 을 제거 후 처리
15. '=' → 수식 + 숫자로 계산, 결과를 출력창에 표시, 수식창 비움

[보완 1]
1. eval() 대신 ast 모듈로 수식을 안전하게 파싱해서 계산
2. decimal 모듈로 10진수 기반 계산 (0.1 + 0.2 문제 해결)
3. 0으로 나누기 등 잘못된 연산 → "Error" 표시, 다음 입력 시 자동 초기화
4. 초기 출력창 값 '' → "0" 으로 보이게 처리 (UX 개선)
5. +/- 키의 괄호 중첩 문제 보완
6. 소수점 중복 입력 방지
7. 선행 0 방지 (현재 입력이 "0" 일 때 '0' 또 누르면 무시, 다른 숫자 누르면 교체)
8. 최대 자릿수 제한
9. 수식 창의 표시 개선 (연산자 기호 변환, 숫자에 콤마 추가)
10. '=' 직후 숫자 입력 시, 이어서 계산 시작

[보완 2]
 - Backspace 키: 출력창 숫자의 마지막 글자 하나만 삭제 (수식창은 유지)
 - AC 버튼 / Esc / Delete 키: 전체 초기화 (AC 와 동일)

"""
import sys
import ast
from decimal import Decimal, getcontext, InvalidOperation

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QPushButton,
    QVBoxLayout, QGridLayout, QLabel, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QFontMetrics, QKeyEvent

'''
getcontext().prec = 30에 대해(Decimal 모듈 정밀도 설정)
Python float 를 그대로 쓰면 0.1 + 0.2 == 0.30000000000000004 같은 오차가 생긴다.
Decimal 을 쓰면 십진수 기반으로 계산되어 일상적인 계산에서 오차가 사라진다.
prec 은 '유효 자릿수' 로, 30 정도면 보통 계산에 차고 넘친다.
'''
getcontext().prec = 30

class Calculator(QMainWindow):
    '''
    상수 정의(숫자 최대 자릿수, 출력창 폭, 폰트 크기 후보, 버튼 스타일)
    '''
    MAX_DIGITS = 16  # 한 숫자에 넣을 수 있는 최대 유효 자릿수 (오버플로 방지)

    # 메인 출력창이 실제로 글자를 그릴 수 있는 폭 (픽셀).
    # 창 너비 360 − 좌우 마진 12*2 − 오른쪽 padding 12 정도를 감안.
    DISPLAY_TEXT_WIDTH = 320

    # 메인 출력창 폰트 크기 후보 (크기 큰 순서).
    # 실제 텍스트를 그려봤을 때 DISPLAY_TEXT_WIDTH 안에 들어오는 첫 크기를 고른다.
    DISPLAY_FONT_CANDIDATES = [64, 56, 48, 42, 36, 32, 28, 24, 20, 18]

    # 버튼 스타일 — 세 종류: 회색(기능), 어두운 회색(숫자), 주황(연산)
    # 1. A/C, +/-, % 같은 기능 버튼
    STYLE_GRAY = """
        QPushButton {
            background-color: #a5a5a5; color: black; border: none;
            border-radius: 35px; font-size: 22px; font-weight: 500;
        }
        QPushButton:pressed { background-color: #d4d4d4; }
    """
    # 2. 숫자 버튼
    STYLE_DARK = """
        QPushButton {
            background-color: #333333; color: white; border: none;
            border-radius: 35px; font-size: 28px; font-weight: 400;
        }
        QPushButton:pressed { background-color: #737373; }
    """
    # 3. 연산자 버튼
    STYLE_ORANGE = """
        QPushButton {
            background-color: #ff9500; color: white; border: none;
            border-radius: 35px; font-size: 32px; font-weight: 400;
        }
        QPushButton:pressed { background-color: #ffbd66; }
    """
    # 4. '0' 버튼
    STYLE_ZERO = """
        QPushButton {
            background-color: #333333; color: white; border: none;
            border-radius: 35px; font-size: 28px; font-weight: 400;
            padding-left: 28px; text-align: left;
        }
        QPushButton:pressed { background-color: #737373; }
    """

    ''' 
    생성자: 창 제목, 크기, 배경색 설정, 상태 변수 초기화, UI 구성 및 초기 화면 갱신
    '''
    def __init__(self):
        super().__init__()
        # 창 제목, 크기, 배경색 설정
        self.setWindowTitle("계산기")
        self.setFixedSize(360, 640) 
        self.setStyleSheet("background-color: #000000;")    # 전체 배경은 검정

        # 현재 출력창(아래쪽 큰 글자)에 입력 중인 숫자 문자열
        self.current_input = ""
        # 수식창(위쪽 작은 글자)의 수식 문자열
        self.expression = ""
        # 방금 누른 입력이 연산자였는지
        self.last_was_operator = False
        # 방금 '=' 를 눌러 결과가 표시된 상태인지
        self.last_was_equals = False
        # 현재 입력 숫자에 '.' 이 이미 들어있는지
        self.has_decimal = False
        # "5/0=" 처럼 잘못된 연산으로 에러 상태인지 (에러 후 다음 입력 시 자동 초기화)
        self.error_state = False

        self._build_ui()     # 화면 구성
        self._refresh()      # 현재 상태를 화면에 반영 (처음엔 "0" 표시)
    '''
     UI 구성 (QMainWindow 중앙에 QWidget 을 넣고, 그 QWidget 에 QVBoxLayout 을 적용하여 수식창, 출력창, 버튼 그리드를 수직으로 배치한다.)
    '''
    def _build_ui(self):
        """
        QMainWindow 는 중앙에 하나의 위젯만 놓을 수 있는데, 
        여러 위젯을 배치하기 위해 그 안에 QWidget 을 하나 더 넣고, 그 QWidget 에 레이아웃을 적용한다.
        이로써 창 안에 위젯들을 배치 시 위→아래, 수직으로 쌓이게 된다(순서:수식창 / 출력창 / 버튼 그리드)
        """
        central = QWidget() # 빈 컨테이너 생성
        self.setCentralWidget(central) # central(빈 컨테이너)를 QMainWindow의 중앙 위젯으로 설정
        root = QVBoxLayout(central) # central 위젯에 수직 레이아웃 적용
        root.setContentsMargins(12, 12, 12, 12) # 전체 여백 (좌, 상, 우, 하)
        root.setSpacing(6) # 위젯 사이 간격 (수식창, 출력창, 버튼 그리드 사이)

        #  수식창 
        self.expr_label = QLabel("") # QWidget이 아닌 QLabel을 씀으로써 setText()와 같은 메소드가 가능함
        # 
        self.expr_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter #수평 기준, 오른쪽 정렬/ 수직 기준, 가운데 정렬
        )
        self.expr_label.setStyleSheet("color: #888888; padding-right: 12px;")
        self.expr_label.setFont(QFont("Helvetica", 16))
        self.expr_label.setFixedHeight(28)
        root.addWidget(self.expr_label)

        # 출력창 (아래쪽, 큰 흰색 글자)
        self.display = QLabel("0")
        self.display.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter # 수평 기준, 오른쪽 정렬 / 수직 기준, 가운데 정렬
        )
        self.display.setStyleSheet("color: white; padding-right: 12px;")
        self._set_display_font(64) 
        self.display.setFixedHeight(100)
        root.addWidget(self.display)

        # 버튼 그리드 (5행 × 4열)
        grid = QGridLayout()
        grid.setSpacing(8)

        # 버튼 하나를 그리드에 추가하는 내부 헬퍼 함수
        # colspan=2 를 주면 '0' 버튼처럼 가로로 두 칸을 차지한다.(0번 버튼 처리를 위해)
        def add_btn(label, row, col, style, handler, colspan=1):
            btn = QPushButton(label) # 버튼 생성 및 표기될 이름 설정
            btn.setStyleSheet(style) # 버튼 색상, 크기 등 css 설정
            # Focus란, 버튼 클릭 후, GUI 내부에서 포커스라는 일종의 커서를 버튼에 올려둠
            # 만약, 특정 버튼에 Focus가 활성화된 상태에서 엔터를 누르면 해당 버튼이 다시 클릭됨
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            if colspan == 1:
                btn.setFixedSize(70, 70)
            else:
                btn.setFixedHeight(70)
                btn.setSizePolicy(
                    QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed # 수평 기준, 크기에 맞게 확장/ 수직 기준, 크기 고정
                )
            btn.clicked.connect(handler) # 버튼에 기능 메소드 연결
            grid.addWidget(btn, row, col, 1, colspan)
            return btn

        # 행 0: AC, +/−, %, ÷
        add_btn("AC",  0, 0, self.STYLE_GRAY,   self.on_clear)
        add_btn("+/−", 0, 1, self.STYLE_GRAY,   self.on_negate)
        add_btn("%",   0, 2, self.STYLE_GRAY,   self.on_percent)
        add_btn("÷",   0, 3, self.STYLE_ORANGE, lambda: self.on_operator("/"))

        # 행 1: 7, 8, 9, ×
        for i, d in enumerate(["7", "8", "9"]):
            # 람다식을 사용하지 않으면 반복문이 끝난 후, d의 값이 9로 고정되어
            # 7, 8, 9 버튼 모두 9가 할당되는 버그 생김
            add_btn(d, 1, i, self.STYLE_DARK, lambda _=None, x=d: self.on_digit(x))
        add_btn("×", 1, 3, self.STYLE_ORANGE, lambda: self.on_operator("*"))

        # 행 2: 4, 5, 6, −
        for i, d in enumerate(["4", "5", "6"]):
            add_btn(d, 2, i, self.STYLE_DARK,
                    lambda _=None, x=d: self.on_digit(x))
        add_btn("−", 2, 3, self.STYLE_ORANGE, lambda: self.on_operator("-"))

        # 행 3: 1, 2, 3, +
        for i, d in enumerate(["1", "2", "3"]):
            add_btn(d, 3, i, self.STYLE_DARK,
                    lambda _=None, x=d: self.on_digit(x))
        add_btn("+", 3, 3, self.STYLE_ORANGE, lambda: self.on_operator("+"))

        # 행 4: 0(가로 2칸), ., =
        add_btn("0", 4, 0, self.STYLE_ZERO,
                lambda: self.on_digit("0"), colspan=2)
        add_btn(".", 4, 2, self.STYLE_DARK,   self.on_decimal)
        add_btn("=", 4, 3, self.STYLE_ORANGE, self.on_equals)

        root.addLayout(grid)

    # ==================================================================
    # 폰트 / 포매팅 관련
    # ==================================================================
    def _set_display_font(self, size: int):
        # 출력창 폰트를 지정된 크기로 바꾼다 (Thin 굵기)
        self.display.setFont(QFont("Helvetica", size, QFont.Weight.Thin))

    def _adjust_display_font(self, text: str):
        for size in self.DISPLAY_FONT_CANDIDATES:
            font = QFont("Helvetica", size, QFont.Weight.Thin)
            if QFontMetrics(font).horizontalAdvance(text) <= self.DISPLAY_TEXT_WIDTH:
                self.display.setFont(font)
                return
        # 후보 중 어느 것도 안 들어가면 가장 작은 폰트로.
        self.display.setFont(QFont("Helvetica", 16, QFont.Weight.Thin))

    def _format_number(self, s: str) -> str:
        """
        숫자 문자열에 3자리 콤마를 찍는다.
        - 괄호 음수 "(-1234.5)"  → "(-1,234.5)"
        - 음수 "-1234"           → "-1,234"
        - 소수 "1234.5678"       → "1,234.5678" (소수점 이하엔 콤마 안 찍음)
        """
        if not s:
            return "0"

        # 괄호 음수: 겉껍질을 벗긴 뒤 재귀로 내부를 포맷하고 다시 감싼다.
        if s.startswith("(") and s.endswith(")"):
            return "(" + self._format_number(s[1:-1]) + ")"

        # 부호 분리 (음수면 잠시 빼놨다가 마지막에 붙인다)
        neg = s.startswith("-")
        if neg:
            s = s[1:]

        if "." in s:
            int_part, dec_part = s.split(".", 1)
            int_part = int_part or "0"          # "123" 없이 ".5" 만 있는 경우 대비
            try:
                formatted = f"{int(int_part):,}" + "." + dec_part
            except ValueError:
                formatted = s
        else:
            try:
                formatted = f"{int(s):,}"
            except ValueError:
                formatted = s

        return ("-" + formatted) if neg else formatted

    def _format_expression(self, expr: str) -> str:
        """
        수식창에 표시할 문자열을 보기 좋게 변환.
        - 내부적으로는 연산자가 '*', '/', '-' 이지만, 화면엔 '×', '÷', '−'.
        - 숫자마다 3자리 콤마 적용.
        """
        if not expr:
            return ""

        out = []
        num = ""
        for ch in expr:
            # 숫자 또는 소수점은 "현재 모으는 숫자" 로 계속 이어붙인다.
            if ch.isdigit() or ch == ".":
                num += ch
                continue
            # 숫자가 아닌 문자를 만났으면, 쌓아뒀던 숫자를 먼저 포맷해서 flush.
            if num:
                out.append(self._format_number(num))
                num = ""
            # 연산자/괄호 변환
            if   ch == "*": out.append("×")
            elif ch == "/": out.append("÷")
            elif ch == "-": out.append("−")
            else:           out.append(ch)      # '(', ')', '+'
        if num:
            out.append(self._format_number(num))
        return "".join(out)

    # ==================================================================
    # 전체 화면 갱신
    # ==================================================================
    def _refresh(self):
        """현재 상태(current_input, expression, error_state)를 화면에 반영한다."""
        # 에러 상태에서는 "Error" 만 표시하고 다른 것들은 신경 쓰지 않는다.
        if self.error_state:
            self.display.setText("Error")
            self._set_display_font(56)
            self.expr_label.setText("")
            return

        # 출력창: 현재 입력이 비어있으면 "0" 으로 보여준다 (요구사항 1 의 UX 보완).
        text = self._format_number(self.current_input) if self.current_input else "0"
        self.display.setText(text)
        self._adjust_display_font(text)

        # 수식창
        self.expr_label.setText(self._format_expression(self.expression))

    # ==================================================================
    # 공통 유틸
    # ==================================================================
    def _reset_if_error(self):
        """에러 상태에서 숫자/연산자가 들어오면 자동으로 전체 초기화해 이어서 쓸 수 있게."""
        if self.error_state:
            self.on_clear()

    # ==================================================================
    # 버튼 / 키 핸들러
    # ==================================================================

    # ── 숫자 (요구사항 3, 13) ─────────────────────────────────────────
    def on_digit(self, d: str):
        self._reset_if_error()

        # = 직후에 숫자를 누른 경우 → 완전히 새 계산을 시작한다.
        if self.last_was_equals:
            self.current_input = ""
            self.expression = ""
            self.last_was_equals = False
            self.has_decimal = False

        # +/- 로 "(-5)" 처럼 감싸진 상태에서 숫자를 누르면
        # 그 값을 덮어쓰는 새 숫자 입력으로 본다 → 기존 입력을 비움.
        if self.current_input.startswith("(") and self.current_input.endswith(")"):
            self.current_input = ""
            self.has_decimal = False

        # [보완] 최대 자릿수 제한.
        # 부호(-), 괄호, 소수점을 제외한 실제 숫자 자릿수만 센다.
        clean = (self.current_input
                 .lstrip("-")
                 .replace(".", "")
                 .replace("(", "")
                 .replace(")", ""))
        if len(clean) >= self.MAX_DIGITS:
            return

        # [보완] 선행 0 방지: "007" 이나 "00" 이 못 나오게.
        if self.current_input == "0" and d == "0":
            return                          # "0" 상태에서 '0' 또 누름 → 무시
        if self.current_input == "0" and d != "0":
            self.current_input = d          # "0" 상태에서 다른 숫자 → 교체
        else:
            self.current_input += d         # 일반적인 경우엔 뒤에 붙인다.

        self.last_was_operator = False
        self._refresh()

    # ── 소수점 (요구사항 12, 13) ──────────────────────────────────────
    def on_decimal(self):
        self._reset_if_error()

        # = 직후라면 새 계산을 시작해야 하므로 상태 리셋.
        if self.last_was_equals:
            self.current_input = ""
            self.expression = ""
            self.last_was_equals = False
            self.has_decimal = False

        # [보완] 이미 '.' 이 있으면 추가하지 않는다 ("1.2.3" 방지).
        if self.has_decimal:
            return

        # 숫자 없이 바로 '.' 을 누른 경우 "0." 이 되도록 앞에 "0" 을 붙인다.
        # (-x) 감싼 상태에서도 마찬가지로 새 숫자 입력으로 본다.
        if not self.current_input or (
            self.current_input.startswith("(") and self.current_input.endswith(")")
        ):
            self.current_input = "0"

        self.current_input += "."
        self.has_decimal = True
        self.last_was_operator = False
        self._refresh()

    # ── 연산자 +, −, ×, ÷ (요구사항 6, 7, 8, 9, 14) ───────────────────
    def on_operator(self, op: str):
        self._reset_if_error()

        # 마지막이 . 일 경우
        if self.current_input.endswith("."):
            self.current_input = self.current_input[:-1]
            self.has_decimal = False

        # = 직후 나온 결과를 피연산자로
        if self.last_was_equals:
            self.expression = self.current_input + op
            self.current_input = ""
            self.has_decimal = False
            self.last_was_equals = False
            self.last_was_operator = True
            self._refresh()
            return

        # 수식창에 이미 수식이 있고, 출력창에도 숫자가 있을 때
        # 먼저 계산한 결과를 출력창에 표시하고, 수식창엔 "결과 + 새 연산자".
        if self.expression and self.current_input and not self.last_was_operator:
            try:
                full = self.expression + self.current_input
                result = self._evaluate(full)
                self.current_input = result
                self.expression = result + op
                self.has_decimal = "." in result
                self.last_was_operator = True
                self._refresh()
            except Exception:
                self._show_error()
            return

        # 방금도 연산자였는데 또 연산자 → 마지막 연산자만 교체.
        if self.last_was_operator and self.expression and self.expression[-1] in "+-*/":
            self.expression = self.expression[:-1] + op
            self._refresh()
            return

        # 숫자 입력 없이 연산자 → "0+연산자" 로 시작.
        if not self.current_input:
            self.expression = "0" + op
            self.last_was_operator = True
            self._refresh()
            return

        # ⑤ 요구사항 6: 일반적인 경우. 현재 숫자 + 연산자를 수식창으로 옮기고
        #    출력창은 비운다.
        self.expression = self.current_input + op
        self.current_input = ""
        self.has_decimal = False
        self.last_was_operator = True
        self._refresh()

    # ── '=' 계산 실행 (요구사항 15) ───────────────────────────────────
    def on_equals(self):
        self._reset_if_error()

        # 수식창이나 출력창 중 하나라도 없으면 계산할 수 없다.
        if not self.expression or not self.current_input:
            return

        # '.' 으로 끝나면 떼고 계산.
        if self.current_input.endswith("."):
            self.current_input = self.current_input[:-1]
            self.has_decimal = False

        try:
            full = self.expression + self.current_input
            result = self._evaluate(full)
            self.current_input = result
            self.expression = ""                # 수식창 비움
            self.has_decimal = "." in result
            self.last_was_equals = True
            self.last_was_operator = False
            self._refresh()
        except Exception:
            # 0으로 나누기 등 → 에러 표시
            self._show_error()

    # ── +/- 부호 전환 (요구사항 10) ───────────────────────────────────
    def on_negate(self):
        self._reset_if_error()

        # [보완] 아무것도 없거나 "0" 일 때는 부호 전환 의미가 없어 무시한다.
        if not self.current_input or self.current_input == "0":
            return

        s = self.current_input
        # 케이스 A: "(-x)" 형태였던 음수 → 괄호와 '-' 제거해서 양수 "x" 로.
        if s.startswith("(-") and s.endswith(")"):
            self.current_input = s[2:-1]
        # 케이스 B: "-x" 형태의 (계산 결과로 나온) 음수 → '-' 제거해 양수 "x".
        elif s.startswith("-"):
            self.current_input = s[1:]
        # 케이스 C: 양수 → "(-x)" 로 감싼다.
        #   [보완] 요구사항 원문대로 "양수도 괄호로 감쌈" 하면 "(5)" 같은
        #   어색한 표시가 나와서, 음수일 때만 괄호로 감싸는 쪽으로 조정했다.
        else:
            self.current_input = "(-" + s + ")"

        self._refresh()

    # ── % 퍼센트 (요구사항 11) ────────────────────────────────────────
    def on_percent(self):
        self._reset_if_error()

        if not self.current_input:
            return

        try:
            # Decimal 은 "(-5)" 를 못 읽으므로 괄호를 떼고 파싱.
            s = self.current_input
            if s.startswith("(") and s.endswith(")"):
                s = s[1:-1]

            val = Decimal(s)
            result = val / Decimal(100)
            self.current_input = self._format_result(result)
            self.has_decimal = "." in self.current_input
            self.last_was_operator = False
            self._refresh()
        except Exception:
            self._show_error()

    # ── AC: 전체 초기화 (요구사항 2) ──────────────────────────────────
    def on_clear(self):
        """AC 버튼 / Esc / Delete 키. 출력창과 수식창을 모두 비운다."""
        self.current_input = ""
        self.expression = ""
        self.has_decimal = False
        self.last_was_operator = False
        self.last_was_equals = False
        self.error_state = False
        self._refresh()

    # ── Backspace: 출력창 마지막 글자만 삭제 (보완 2) ────────────────
    def on_backspace(self):
        """
        [보완 2] 백스페이스는 '출력창에서 한 글자만' 지운다.
        수식창(expression) 에는 절대 손대지 않는다.
        AC / CE 동작과 구분되는 점이 여기다.
        """
        # 에러 상태에서는 아무것도 안 함 (AC 로 빠져나가도록).
        if self.error_state:
            return

        # = 직후의 결과 숫자는 '편집 대상' 이 아니라 '결과' 이므로
        #   혼란을 피하기 위해 백스페이스를 무시한다.
        if self.last_was_equals:
            return

        # 지울 글자가 없음 (연산자 직후 current_input 이 빈 상태 포함).
        if not self.current_input:
            return

        s = self.current_input

        # "(-x)" 같은 괄호 음수는 한 글자가 아니라 '하나의 덩어리' 로 보는 게
        # 직관적이므로, 통째로 비운다.
        if s.startswith("(") and s.endswith(")"):
            self.current_input = ""
            self.has_decimal = False
            self.last_was_operator = False
            self._refresh()
            return

        # 일반적인 경우: 마지막 글자 하나만 제거.
        removed = s[-1]
        self.current_input = s[:-1]

        # 방금 지운 게 '.' 이었다면 소수점 플래그도 풀어준다.
        if removed == ".":
            self.has_decimal = False

        # "-5" 에서 '5' 를 지우면 "-" 만 남아 이상하므로 깔끔히 비운다.
        if self.current_input == "-":
            self.current_input = ""

        self.last_was_operator = False
        self._refresh()

    # ==================================================================
    # 안전한 수식 평가
    # ==================================================================
    # Python 내장 eval() 을 쓰면 수식 문자열에 예기치 않은 코드가 섞였을 때
    # 실행될 위험이 있다. 여기서는 ast 모듈로 '파싱' 만 한 뒤,
    # 내가 허용한 노드(숫자, 사칙연산, 단항 +/-) 만 직접 계산한다.
    # 즉 함수 호출, 변수, 속성 접근 같은 건 아예 실행될 수 없다.
    # ------------------------------------------------------------------
    def _evaluate(self, expr: str) -> str:
        tree = ast.parse(expr, mode="eval")
        value = self._eval_ast(tree.body)
        return self._format_result(value)

    def _eval_ast(self, node):
        """AST 를 재귀적으로 내려가며 Decimal 로 계산한다."""
        if isinstance(node, ast.Expression):
            return self._eval_ast(node.body)

        # 숫자 리터럴 (정수 또는 부동소수).
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                # str() 로 한 번 감싸는 이유:
                #   Decimal(0.1) 은 float 의 이진 표현까지 정밀하게 가져와
                #   Decimal('0.1000000000000000055511151231257827021181...')
                #   이 되지만, Decimal(str(0.1)) 은 정확히 '0.1' 이 된다.
                return Decimal(str(node.value))
            raise ValueError("Unsupported constant")

        # 이항 연산 (좌 [연산자] 우).
        if isinstance(node, ast.BinOp):
            l = self._eval_ast(node.left)
            r = self._eval_ast(node.right)
            if isinstance(node.op, ast.Add):  return l + r
            if isinstance(node.op, ast.Sub):  return l - r
            if isinstance(node.op, ast.Mult): return l * r
            if isinstance(node.op, ast.Div):
                if r == 0:
                    # 0으로 나누기 → 예외를 던져서 상위에서 _show_error() 로.
                    raise ZeroDivisionError()
                return l / r
            raise ValueError("Unsupported operator")

        # 단항 연산 (부호 +, -). "(-5)" 의 -5 처리에 쓰인다.
        if isinstance(node, ast.UnaryOp):
            v = self._eval_ast(node.operand)
            if isinstance(node.op, ast.USub): return -v
            if isinstance(node.op, ast.UAdd): return v
            raise ValueError("Unsupported unary")

        # 그 외 (함수 호출, 변수명 등) 는 모두 거부.
        raise ValueError("Unsupported expression")

    def _format_result(self, value: Decimal) -> str:
        """
        계산 결과 Decimal 을 화면에 적합한 문자열로 만든다.

        - 정수 값이면 정수 형태로 ("5.0" → "5").
        - 너무 큰 값은 과학 표기 ("1.234568E+18").
        - 소수는 너무 긴 꼬리 자릿수를 피하려고 12자리에서 반올림 후
          뒤쪽 0 과 '.' 을 제거 ("0.500000000000" → "0.5").
        """
        # 정수로 딱 떨어지는지 확인.
        if value == value.to_integral_value():
            try:
                i = int(value)
                # 표시 자릿수 한계를 넘으면 과학표기 형태로.
                if abs(i) >= 10 ** 16:
                    return f"{value:.6E}"
                return str(i)
            except Exception:
                return str(value)

        # 소수점이 있는 값 — 12자리로 양자화(반올림)한다.
        try:
            if abs(value) < Decimal("1E+16"):
                q = value.quantize(Decimal("1E-12"))
            else:
                q = value
        except InvalidOperation:
            q = value

        # normalize() 로 불필요한 0 을 제거, format 'f' 로 과학표기 방지.
        s = format(q.normalize(), "f")
        if "." in s:
            s = s.rstrip("0").rstrip(".")
        return s if s else "0"

    # ==================================================================
    # 에러 표시
    # ==================================================================
    def _show_error(self):
        """'Error' 를 띄우고 상태를 '에러' 로 표시. 다음 입력이 오면 자동 클리어."""
        self.current_input = ""
        self.expression = ""
        self.has_decimal = False
        self.last_was_operator = False
        self.last_was_equals = False
        self.error_state = True
        self._refresh()

    # ==================================================================
    # 키보드 입력
    # ==================================================================
    def keyPressEvent(self, event: QKeyEvent):
        print(event.key(), event.text())
        """
        키 매핑:
          0~9              → 숫자
          . (마침표)       → 소수점
          + - * /          → 연산자
          Enter / Return / = → 계산 (=)
          %                → 퍼센트
          F9               → +/- (Windows 계산기 관례)
          Backspace        → [보완] 출력창 마지막 글자만 삭제
          Esc, Delete      → AC (전체 초기화)
        """
        key = event.key()
        txt = event.text()

        if txt and txt in "0123456789":
            self.on_digit(txt); return
        if txt == ".":
            self.on_decimal(); return
        if txt in ("+", "-", "*", "/"):
            self.on_operator(txt); return
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Equal) or txt == "=":
            self.on_equals(); return
        if txt == "%":
            self.on_percent(); return
        if key == Qt.Key.Key_F9:
            self.on_negate(); return

        # [보완 2] 백스페이스: 한 글자만 지운다.
        if key == Qt.Key.Key_Backspace:
            self.on_backspace(); return

        # AC 역할: Esc, Delete 는 전체 초기화.
        # (키보드에 AC/CE 라는 물리키가 없으므로 이 두 개를 대체로 사용)
        if key in (Qt.Key.Key_Escape, Qt.Key.Key_Delete):
            self.on_clear(); return

        super().keyPressEvent(event)


# ----------------------------------------------------------------------
# 엔트리 포인트
# ----------------------------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    calc = Calculator()
    calc.show()
    sys.exit(app.exec())
