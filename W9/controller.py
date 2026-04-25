from view import view
from model import model

from decimal import Decimal
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent




class controller():
    def __init__(self):
        self.model = model()
        self.view = view()
        self.view.set_handler(
            on_clear=self.on_clear,
            on_negate=self.on_negate,
            on_percent=self.on_percent,
            on_operator=self.on_operator,
            on_digit=self.on_digit,
            on_decimal=self.on_decimal,
            on_equals=self.on_equals
        )
        self.view._key_handler = self.handle_key
        self._refresh()

    def check_value(self):
        print(f'self.model.current_input : {self.model.current_input}')
        print(f'self.model.expression: {self.model.expression}')
        print(f'self.model.last_was_operator: {self.model.last_was_operator}')
        print(f'self.model.last_was_equals: {self.model.last_was_equals}')
        print(f'self.model.has_decimal: {self.model.has_decimal}')
        print(f'self.model.error_state: {self.model.error_state}')
        print('\n')

    # ==============================================================================
    # 공통 유틸리티 메소드
    # ==============================================================================

    # --- 출력창, 수식창을 현재 상태에 맞게 업데이트하는 메소드 ---
    def _refresh(self):
        # 에러 상태이면, 출력창에 "Error" 표시, 폰트 크기 56으로 설정, 수식창 비우기
        if self.model.error_state:
            self.view.display.setText("Error")
            self.view._set_display_font(56)
            self.view.expr_label.setText("")
            return
        
        text = self.model._format_number(self.model.current_input) if self.model.current_input else "0" # current_input이 비어있으면 "0"으로 표시
        self.view.display.setText(text)
        self.view._adjust_display_font(text)

        # 수식창
        self.view.expr_label.setText(self.model._format_expression(self.model.expression))

    # --- 에러 상태에서 숫자/연산자 입력 시 출력창 초기화 메소드 ---
    def _reset_if_error(self):
        if self.model.error_state:
            self.on_clear()

    # --- 계산 결과가 에러 상태일 경우 처리 ---
    def _show_error(self):
        self.model.current_input = ""
        self.model.expression = ""
        self.model.has_decimal = False
        self.model.last_was_operator = False
        self.model.last_was_equals = False
        self.model.error_state = True
        self._refresh() # 출력창, 수식창 업데이트
    
    # ==============================================================================
    # 버튼 핸들러 메소드들
    # ==============================================================================
    # --- 숫자 입력 처리 ---
    def on_digit(self, digit: str):
        self._reset_if_error() # 에러 상태에서 숫자/연산자 입력 시 출력창 초기화

        # = 직후에 숫자를 누른 경우 → 완전히 새 계산을 시작한다.
        if self.model.last_was_equals:
            self.model.current_input = ""
            self.model.expression = ""
            self.model.last_was_equals = False
            self.model.has_decimal = False
        
        if self.model.last_was_operator:
            self.model.current_input = ""
            self.model.has_decimal = False


        # (-5) 처럼 감싸진 상태에서 숫자를 누르면, 그 값을 덮어쓰는 새 숫자 입력
        if self.model.current_input.startswith("(") and self.model.current_input.endswith(")"):
            self.model.current_input = ""
            self.model.has_decimal = False

        # 부호(-), 괄호, 소수점을 제외한 실제 숫자 자릿수만 센다.
        current_input_clean_version = (self.model.current_input
                 .lstrip("-") # 제일 왼쪽 문자 제거
                 .replace(".", "") # . 제거
                 .replace("(", "") # ( 제거
                 .replace(")", "")) # ) 제거
        if len(current_input_clean_version) >= self.model.MAX_DIGITS:
            return

        # 0 상태에서 0 또 누를 경우 무시
        if self.model.current_input == "0" and digit == "0":
            return
        
        # 0 상태에서 다른 숫자 누를 경우 교체, 그 외에는 그냥 뒤에 붙인다.
        if self.model.current_input == "0" and digit != "0":
            self.model.current_input = digit
        else:
            self.model.current_input += digit

        # 새로운 숫자가 입력되었으므로 = 직후 상태도 False로 설정
        self.model.last_was_operator = False

        # 숫자 입력 시 에러 상태일 경우
        self._refresh() # 출력창, 수식창 업데이트

    # --- 연산자 입력 처리 ---
    def on_operator(self, op: str):
        self._reset_if_error() # 에러 상태에서 숫자/연산자 입력 시 출력창 초기화 메소드 호출

        # 출력창 마지막이 . 일 경우
        if self.model.current_input.endswith("."):
            self.model.current_input = self.model.current_input[:-1]
            self.model.has_decimal = False

        # = 직후 나온 결과를 피연산자로
        if self.model.last_was_equals:
            self.model.expression = self.model.current_input + op
            self.model.current_input = ""
            self.model.has_decimal = False
            self.model.last_was_equals = False
            self.model.last_was_operator = True
            self._refresh() # 출력창, 수식창 업데이트
            return
        
        # 수식창에 이미 수식이 있고, 출력창에도 숫자가 있으며, 마지막 입력이 연산자가 아닌 경우
        if self.model.expression and self.model.current_input and not self.model.last_was_operator:
            try:
                full = self.model.expression + self.model.current_input # 수식창과 출력창을 합쳐 온전한 수식으로 저장
                result = self.model._evaluate(full) # 수식 계산 메소드 호출해서 결과 얻기
                self.model.current_input = result # 출력창에 계산 결과 표시
                self.model.expression = result + op # 수식창에 계산결과와 새 연산자 표시
                self.model.has_decimal = "." in result # 결과에 소수점이 포함되어 있는지 여부 업데이트
                self.model.last_was_operator = True # 연산자 입력이 이어진 상태로 설정
                self._refresh() # 출력창, 수식창 업데이트
            except Exception:
                self._show_error() # 계산 중 에러가 발생하면 에러 상태로 설정
            return

        # 수식창에 이미 수식이 있고, 출력창에도 숫자가 있으며, 연산자 바로 다음에 다른 연산자가 나오는 경우
        if self.model.last_was_operator and self.model.expression and self.model.expression[-1] in "+-*/":
            self.model.expression = self.model.expression[:-1] + op # 수식창의 마지막 연산자를 새 연산자로 교체
            self._refresh() # 출력창, 수식창 업데이트
            return

        # 숫자 입력 없이 연산자만 계속 누르는 경우
        if not self.model.current_input:
            self.model.expression = "0" + op # 수식창에 "0"과 연산자 표시
            self.model.last_was_operator = True # 연산자 입력이 이어진 상태로 설정
            self._refresh() # 출력창, 수식창 업데이트
            return
        
        # 그 외의 경우, 수식창에 출력창의 값과 연산자 이어진 상태로 표시
        self.model.expression = self.model.current_input + op
        self.model.current_input = "" # 출력창 비우기
        self.model.has_decimal = False # 새 숫자 입력이 시작되므로 소수점 포함 여부 초기화
        self.model.last_was_operator = True # 연산자 입력이 이어진 상태로 설정
        self._refresh() # 출력창, 수식창 업데이트

    # --- = 입력 처리 ---
    def on_equals(self):
        self._reset_if_error() # 에러 상태에서 숫자/연산자 입력 시 출력창 초기화 메소드 호출

        # 수식창 혹은 출력창이 비어있으면 = 입력 무시
        if not self.model.expression or not self.model.current_input:
            return

        # 출력창이 '.' 으로 끝나면 떼고 계산.
        if self.model.current_input.endswith("."):
            self.model.current_input = self.model.current_input[:-1]
            self.model.has_decimal = False

        try:
            full_expression = self.model.expression + self.model.current_input # 수식창과 출력창을 합쳐 온전한 수식으로 저장
            result = self.model._evaluate(full_expression) # 수식 계산 메소드 호출해서 결과 얻기
            self.model.current_input = result       # 계산 결과를 출력창에 표시하기 위해 current_input에 저장
            self.model.expression = ""              # 수식장 비우기
            self.model.has_decimal = "." in result  # 결과에 소수점이 포함되어 있는지 여부 업데이트
            self.model.last_was_equals = True       # = 입력으로 결과가 표시된 상태로 설정
            self.model.last_was_operator = False    # 결과가 표시된 상태이므로 연산자 입력이 바로 이어질 때, 현재 결과값을 피연산자로 사용하기 위해 last_was_operator는 False로 설정
            # 계산 결과가 에러 상태일 경우
            self._refresh() # 출력창, 수식창 업데이트
        except Exception:
            self._show_error() # 계산 중 에러가 발생하면 에러 상태로 설정

    # --- AC 버튼 / Esc / Delete 키 입력 처리 ---
    def on_clear(self):
        self.model.current_input = ""
        self.model.expression = ""
        self.model.last_was_operator = False
        self.model.last_was_equals = False
        self.model.has_decimal = False
        self.model.error_state = False
        self._refresh() # 출력창, 수식창 업데이트

    # --- . 입력 처리 ---
    def on_decimal(self):
            self._reset_if_error() # 에러 상태에서 숫자/연산자 입력 시 출력창 초기화

            # = 직후라면 새 계산을 시작해야 하므로 상태 리셋
            if self.model.last_was_equals:
                self.model.current_input = ""
                self.model.expression = ""
                self.model.last_was_equals = False
                self.model.has_decimal = False
                self.check_value()

            # 이미 소수점이 포함된 상태에서 반복해서 . 입력 시 무시
            if self.model.has_decimal:
                return

            # 출력창이 비어있거나, (-x) 처럼 괄호로 감싸진 상태에서 . 입력 시, current_input을 "0"으로 초기화
            if not self.model.current_input or (
                self.model.current_input.startswith("(") and self.model.current_input.endswith(")")
            ):
                self.model.current_input = "0"

            self.model.current_input += "." # current_input 뒤에 '.' 추가
            self.model.has_decimal = True # 소수점이 포함된 상태로 설정
            self.model.last_was_operator = False # 소수점 입력은 연산자 입력이 아니므로 last_was_operator는 False로 설정
            self._refresh() # 출력창, 수식창 업데이트

    # --- +/− 입력 처리 ---
    def on_negate(self):
        self._reset_if_error() # 에러 상태에서 부호 전환 입력 시 출력창 초기화

        # 출력창이 비어있거나, 0일 경우 무시
        if not self.model.current_input or self.model.current_input == "0":
            return

        number_str = self.model.current_input
        # 출력창이 (-x) 형태일 경우, (- 과 ) 제거해서 x로 변경
        if number_str.startswith("(-") and number_str.endswith(")"):
            self.model.current_input = number_str[2:-1] 
        # 계산 결과로 인해 출력창이 -x 형태일 경우, - 제거
        elif number_str.startswith("-"):
            self.model.current_input = number_str[1:]
        # 양수인 경우, (- 과 ) 로 감싸, 음수로 변경
        else:
            self.model.current_input = "(-" + number_str + ")"
        self._refresh() # 출력창, 수식창 업데이트

    # --- % 입력 처리 ---
    def on_percent(self):
        self._reset_if_error() # 에러 상태에서 퍼센트 입력 시 출력창 초기화

        # 출력창이 비어있거나, 0일 경우 무시
        if not self.model.current_input or self.model.current_input == "0":
            return
        try:
            number_str = self.model.current_input
            # 출력창이 (-x) 형태일 경우, 괄호 제거해서 -x로 변경
            if number_str.startswith("(") and number_str.endswith(")"):
                number_str = number_str[1:-1]

            val = Decimal(number_str) # Decimal로 변환
            result = val / Decimal(100) # 100으로 나눠서 백분율 계산
            self.model.current_input = self.model._format_result(result) # 계산 결과를 문자열로 포맷팅해서 current_input에 저장
            self.model.has_decimal = "." in self.model.current_input # 결과에 소수점이 포함되어 있는지 여부 업데이트
            self.model.last_was_operator = False # 퍼센트 입력은 연산자 입력이 아니므로 last_was_operator는 False로 설정
            self._refresh() # 출력창, 수식창 업데이트
        except Exception:
            self._show_error() # 계산 중 에러가 발생하면 에러 상태로 설정

    
    # ==============================================================================
    # 키보드 입력 메소드들
    # ==============================================================================
    def on_backspace(self):
        # 에러 상태에서 백스페이스 입력 시 무시
        if self.model.error_state:
            return
        # = 직후에 백스페이스를 누른 경우 무시
        if self.model.last_was_equals:
            return
        # 출력창이 비어있으면 무시
        if not self.model.current_input:
            return

        number_str = self.model.current_input
        # 출력창이 (-x) 형태일 경우, (-x) 전체 제거
        if number_str.startswith("(") and number_str.endswith(")"):
            self.model.current_input = ""
            self.model.has_decimal = False
            self.model.last_was_operator = False
            self._refresh() # 출력창, 수식창 업데이트
            return

        # 일반적인 경우, 마지막 글자 하나만 제거 후 업데이트
        removed = number_str[-1]
        self.model.current_input = number_str[:-1]

        # 방금 지운 게 '.' 이면, has_decimal을 False로 업데이트
        if removed == ".":
            self.model.has_decimal = False

        # 음수에서 숫자만 지워서 -만 남은 경우, current_input 초기화
        if self.model.current_input == "-":
            self.model.current_input = ""

        self.model.last_was_operator = False
        self._refresh()

    def handle_key(self, event: QKeyEvent):
        """
        키 매핑:
          0~9               → 숫자
          .                 → 소수점
          + - * /           → 연산자
          Enter / Return    → 계산
          %                 → 퍼센트
          F9 / +/-          → +/-
          Backspace         → 한 글자 제거
          Esc, Delete       → 전체 초기화
        """
        event_key = event.key()
        event_txt = event.text()
        # 숫자가 입력된 경우, on_digit 호출
        if event_txt and event_txt in "0123456789":
            self.on_digit(event_txt); return
        #  . 가 일력 될 경우, on_decimal 호출
        if event_txt == ".":
            self.on_decimal(); return
        # 연산자가 입력된 경우, on_operator 호출
        if event_txt in ("+", "-", "*", "/"):
            self.on_operator(event_txt); return
        # 숫자 키보드 엔터(Enter) 혹은 메인 키보드 엔터(Return) 혹은 = 가 입력된 경우, on_equals 호출
        if event_key in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Equal) or event_txt == "=":
            self.on_equals(); return
        # % 가 입력된 경우, on_percent 호출
        if event_txt == "%":
            self.on_percent(); return
        # F9 혹은 +/- 가 입력된 경우, on_negate 호출
        if event_key == Qt.Key.Key_F9:
            self.on_negate(); return
        # 백스페이스가 입력된 경우, on_backspace 호출
        if event_key == Qt.Key.Key_Backspace:
            self.on_backspace(); return
        # Esc 혹은 Delete 가 입력된 경우, on_clear 호출
        if event_key in (Qt.Key.Key_Escape, Qt.Key.Key_Delete):
            self.on_clear(); return
