import ast
from decimal import Decimal, getcontext, InvalidOperation

getcontext().prec = 30

class model:
    MAX_DIGITS = 16  # 한 숫자에 넣을 수 있는 최대 유효 자릿수 (오버플로 방지)
    MAX_DECIMAL_PLACES = 5  # 소수점 이하 최대 자릿수 (오버플로 방지)

    def __init__(self):
        # --- 계산기 상태를 나타내는 변수들 ---
        self.current_input = "" # 현재 출력창에 입력 중인 숫자 문자열
        self.expression = "" # 수식창의 수식 문자열
        self.last_was_operator = False # 연산자 버튼을 눌러 결과값을 표시된 상태인지 여부 (초기값 False)
        self.last_was_equals = False # '='를 눌러 결과가 표시된 상태인지 여부 (초기값 False)
        self.has_decimal = False # 현재 입력 중인 숫자에 소수점이 포함되어 있는지 여부 (초기값 False)
        self.error_state = False # 연산 결과가 에러 상태인지 여부 (초기값 False)

    '''
    --- eval 대신 AST로 수식 계산한 이유 ---
    eval() 함수는 편리하지만, 보안상 위험할 수 있음
    ex) 사용자가 악의적으로 "import os; os.system('rm -rf /')" (rm (removed): 삭제하라, -r (recursive): 폴더 안의 모든 하위 항목까지, -f (force): 강제로)
        같은 코드를 입력해 시스템 명령 실행 가능
    AST(추상 구문 트리)를 사용하면, 입력된 수식을 안전하게 파싱하고 허용된 연산자와 숫자만 처리하도록 제어함 수 있음
    즉, 잠재적인 보안 위험을 방지하면서도 필요한 계산 기능만 제공 가능
    '''
    # --- AST로 수식 계산 ---
    def _evaluate(self, expr: str) -> str:
        tree = ast.parse(expr, mode="eval") # 단일식을 AST로 파싱
        value = self._eval_ast(tree.body) # AST를 재귀적으로 내려가며 계산
        return self._format_result(value) # 계산 결과를 문자열로 포맷팅(형식화)해서 반환
    
    # --- AST 노드 평가 메소드 ---
    def _eval_ast(self, node):
        # ast.Expression(껍데기) 타입이면 body(실제 수식 노드)를 꺼내 재귀 호출
        if isinstance(node, ast.Expression):
            return self._eval_ast(node.body)

        # ast.Constant(Literal 타입) 노드에서 value 속성이 int, float 타입을 담고 있으면, Decimal로 변환해서 반환
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return Decimal(str(node.value)) # str()이 아닌 float()로 감싸면, float의 이진수 오차가 Decimal에도 전달 됨
            raise ValueError("지원하지 않는 리터럴 상수 입니다.")

        # ast.BinOp(이항 연산 타입) 노드이면, left, right 서브노드를 재귀적으로 평가해서 op 타입에 따라 사칙연산 수행
        if isinstance(node, ast.BinOp):
            left_node = self._eval_ast(node.left)
            right_node = self._eval_ast(node.right)
            if isinstance(node.op, ast.Add):  return left_node + right_node
            if isinstance(node.op, ast.Sub):  return left_node - right_node
            if isinstance(node.op, ast.Mult): return left_node * right_node
            # ast.Div(나눗셈 연산자 타입)이면, right_node가 0이면, ZeroDivisionError 처리
            if isinstance(node.op, ast.Div):
                if right_node == 0:
                    raise ZeroDivisionError("0으로 나눌 수 없습니다.")
                return left_node / right_node
            raise ValueError("지원하지 않는 연산자입니다.")

        # ast.UnaryOp(단항 연산 타입) 노드면, operand(피연산자) 서브노드를 재귀적으로 평가
        if isinstance(node, ast.UnaryOp):
            value = self._eval_ast(node.operand)
            if isinstance(node.op, ast.USub): return -value # node.op(연산자)가 ast.USub(단항 마이너스)타입이면, value에 음수 부호 붙여서 반환
            if isinstance(node.op, ast.UAdd): return value # node.op(연산자)가 ast.UAdd(단항 플러스)타입이면, value를 반환
            raise ValueError("지원하지 않는 단항 연산자입니다.")

        # 그 외 (함수 호출, 변수명 등) 는 모두 거부.
        raise ValueError("지원하지 않는 표현식입니다.")

    # ==============================================================================
    # 포맷팅 메소드들
    # ==============================================================================

    # --- 계산 결과 포맷팅(형식화) 메소드 ---
    def _format_result(self, value: Decimal) -> str:
        # intger 값이면, 
        if value == value.to_integral_value():
            # 절대값(abs(integer_value))이 10^MAX_DIGITS 이상이면, 지수(과학) 표기법으로 6자리 유효숫자 표현, 그 미만이면 일반 정수 문자열 반환
            try:
                integer_value = int(value)
                if abs(integer_value) >= 10 ** self.MAX_DIGITS : 
                    return f"{value:.6E}"
                return str(integer_value)
            except Exception:
                return str(value)

        # 절대값이 MAX_DIGITS 자릿수 이내이면, 소수점 아래 MAX_DECIMAL_PLACES 자릿수로 quantize(반올림)
        try:
            if abs(value) < Decimal(f'1E+{self.MAX_DIGITS}'):
                quantized_value = value.quantize(Decimal(f'1E-{self.MAX_DECIMAL_PLACES}'))
            else:
                quantized_value = value
        except InvalidOperation:
            quantized_value = value

        formatted_value = format(quantized_value.normalize(), "f") # 지수 표기법이 아닌 일반 소수점 표기로 변환, normalize로 불필요한 0 제거
        # 소수점이 포함된 경우, 끝의 불필요한 0과 소수점 제거
        if "." in formatted_value:
            formatted_value = formatted_value.rstrip("0").rstrip(".")
        # 삼항 연산자: if formatted_value 이면, formatted_value 반환, 아니면 "0" 반환 (예: 0.00000 일 경우, 0 으로 표시하기 위해)
        return formatted_value if formatted_value else "0"
    
    # --- 출력창 숫자 포맷팅 메소드 ---
    def _format_number(self, number_str: str) -> str:
        if not number_str:
            return "0"

        # (-x) 형태일 경우, 괄호 안의 숫자 부분만 포맷팅하고, 다시 괄호로 감싸서 반환
        if number_str.startswith("(") and number_str.endswith(")"):
            return "(" + self._format_number(number_str[1:-1]) + ")"

        # 음수일 경우, '-' 제거
        is_negative = number_str.startswith("-")
        if is_negative:
            number_str = number_str[1:]

        # 소수일 경우
        if "." in number_str:
            int_part, dec_part = number_str.split(".", 1) # 정수와 소수 부분 분리
            int_part = int_part or "0" # 정수 부분이 비어있으면(ex: .5), 0으로 간주
            # 정수 부분에 3자리마다 콤마 추가
            try:
                formatted = f"{int(int_part):,}" + "." + dec_part
            except ValueError:
                formatted = number_str
        # 정수일 경우, 3자리마다 콤마 추가
        else:
            try:
                formatted = f"{int(number_str):,}"
            except ValueError:
                formatted = number_str

        return ("-" + formatted) if is_negative else formatted
    
    # --- 수식창 수식 포맷팅 메소드 ---
    def _format_expression(self, expr: str) -> str:
        # 수식이 비어있으면 빈 문자열 반환
        if not expr:
            return ""
        out = []
        num = ""
        # expr 문자열을 한 글자씩 반복
        for ch in expr:
            # ch가 숫자 혹은 . 일 경우, num뒤에 추가
            if ch.isdigit() or ch == ".":
                num += ch
                continue
            # num이 비어있지 않으면, num을 포맷팅해서 out에 추가, num 초기화
            if num:
                out.append(self._format_number(num))
                num = ""
            # 연산자/괄호 변환
            if   ch == "*": out.append("×")
            elif ch == "/": out.append("÷")
            elif ch == "-": out.append("−")
            else:           out.append(ch)
        # 마지막에 num이 남아있으면, 포맷팅해서 out에 추가
        if num:
            out.append(self._format_number(num))
        return "".join(out)

