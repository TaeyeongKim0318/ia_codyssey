import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QPushButton,
    QVBoxLayout, QGridLayout, QLabel, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QFontMetrics, QKeyEvent

class view(QMainWindow):
        DISPLAY_FONT_CANDIDATES = [64, 56, 48, 42, 36, 32, 28, 24, 20, 18] # 메인 출력창 폰트 크기 후보 (크기 큰 순서)
        DISPLAY_TEXT_WIDTH = 320 # 실제 글자가 그려지는 영역의 폭 (픽셀 단위)
        
        # --- 버튼 스타일 정의(A/C, +/-, %) ---
        STYLE_GRAY = """
            QPushButton {
                background-color: #a5a5a5; color: black; border: none;
                border-radius: 35px; font-size: 22px; font-weight: 500;
            }
            QPushButton:pressed { background-color: #d4d4d4; }
        """
        # --- 버튼 스타일 정의(숫자) ---
        STYLE_DARK = """
            QPushButton {
                background-color: #333333; color: white; border: none;
                border-radius: 35px; font-size: 28px; font-weight: 400;
            }
            QPushButton:pressed { background-color: #737373; }
        """
        # --- 버튼 스타일 정의(÷, ×, −, +, =) ---
        STYLE_ORANGE = """
            QPushButton {
                background-color: #ff9500; color: white; border: none;
                border-radius: 35px; font-size: 32px; font-weight: 400;
            }
            QPushButton:pressed { background-color: #ffbd66; }
        """
        # --- 버튼 스타일 정의(0, 가로로 2칸) ---
        STYLE_ZERO = """
            QPushButton {
                background-color: #333333; color: white; border: none;
                border-radius: 35px; font-size: 28px; font-weight: 400;
                padding-left: 28px; text-align: left;
            }
            QPushButton:pressed { background-color: #737373; }
        """

        def __init__(self):
            super().__init__()
            self._key_handler = None # 키 입력 값 저장
            self.func_btns = {} # AC, +/-, %, ., ÷, ×, −, +, = 연산자 및 기능 버튼
            self.digit_btns = {} # 0~9 숫자 버튼
            self.setWindowTitle("계산기") # 창 제목 설정
            self.setFixedSize(360, 640)  # 창 크기 고정 (너비 360, 높이 640)
            self.setStyleSheet("background-color: #000000;") # 창 배경색을 검은색으로 설정
            self._build_ui() # UI 구성 메소드 호출


        # --- UI 구성 메소드 ---
        def _build_ui(self):
            # --- 위젯 배치 ---
            central = QWidget() # QMainWindow은 중앙에 하나의 위젯만 배치할 수 있는데, QWidget은 빈 컨테이너 역할을 함
            self.setCentralWidget(central) # central 위젯을 QMainWindow의 중앙 위젯으로 설정
            root = QVBoxLayout(central) # central 위젯에 수직 레이아웃 적용
            root.setContentsMargins(12, 12, 12, 12) # 전체 여백 (좌, 상, 우, 하)
            root.setSpacing(6) # 위젯 사이 간격 (수식창, 출력창, 버튼 그리드 사이)

            # --- 수식창 (위쪽, 작은 회색 글자) ---
            self.expr_label = QLabel("") # QWidget이 아닌 QLabel을 씀으로써 setText()와 같은 메소드가 가능함
            self.expr_label.setAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter # 수평 기준, 오른쪽 정렬/ 수직 기준, 가운데 정렬
            )
            self.expr_label.setStyleSheet("color: #888888; padding-right: 12px;") # 수식창 글자색을 회색으로 설정하고, 오른쪽 여백 12px 추가
            self.expr_label.setFont(QFont("Helvetica", 16)) # 수식창 글꼴과 크기 설정 (Helvetica, 16pt)
            self.expr_label.setFixedHeight(28) # 수식창 높이 고정 (28px)
            root.addWidget(self.expr_label) # 수식창을 레이아웃에 추가

            # --- 출력창 (아래쪽, 큰 흰색 글자) ---
            self.display = QLabel("0") # 초기값 "0"으로 출력창 생성
            self.display.setAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter # 수평 기준, 오른쪽 정렬 / 수직 기준, 가운데 정렬
            )
            self.display.setStyleSheet("color: white; padding-right: 12px;") # 출력창 글자색을 흰색으로 설정하고, 오른쪽 여백 12px 추가
            self._set_display_font(64) # 출력창 글꼴 크기 설정 (64pt)
            self.display.setFixedHeight(100) # 출력창 높이 고정 (100px)
            root.addWidget(self.display) # 출력창을 레이아웃에 추가

            # --- 버튼 그리드 (가운데) ---
            grid = QGridLayout() # 버튼들을 5x4 형태로 배치할 그리드 레이아웃 생성
            grid.setSpacing(8) # 버튼 사이 간격 (8px)

            # --- 버튼 추가 내부 헬퍼 함수 ---
            # label: 버튼에 표기될 이름
            # row: 버튼이 위치할 행 번호
            # col: 버튼이 위치할 열 번호
            # style: 버튼의 스타일
            # colspan: 버튼이 가로로 차지할 칸 수 (기본값 1)
            def add_btn(label, row, col, style, colspan=1):
                btn = QPushButton(label) # 버튼 생성 및 표기될 이름 설정
                btn.setStyleSheet(style) # 버튼 스타일 적용
                btn.setFocusPolicy(Qt.FocusPolicy.NoFocus) # 버튼 클릭 후, Focus가 활성화되지 않도록 설정 (엔터키로 버튼이 다시 클릭되는 것을 방지)
                # 버튼 크기 설정: colspan이 1이면 정사각형 버튼, 그렇지 않으면 가로로 확장되는 버튼
                if colspan == 1:
                    btn.setFixedSize(70, 70)
                else:
                    btn.setFixedHeight(70)
                    btn.setSizePolicy(
                        QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed # 가로로 확장 가능, 세로는 고정
                    )
                grid.addWidget(btn, row, col, 1, colspan) # 버튼을 그리드 레이아웃에 추가 (row, col 위치에 rowSpan=1, colSpan=colspan으로 배치)
                return btn

            # --- 버튼 추가(행 0: AC, +/−, %, ÷) ---
            self.func_btns['AC'] = add_btn("AC",  0, 0, self.STYLE_GRAY)
            self.func_btns['+/−'] = add_btn("+/−", 0, 1, self.STYLE_GRAY)
            self.func_btns['%'] = add_btn("%",   0, 2, self.STYLE_GRAY)
            self.func_btns['÷'] = add_btn("÷",   0, 3, self.STYLE_ORANGE)

            # --- 버튼 추가(행 1: 7, 8, 9, ×) ---
            self.digit_btns['7'] = add_btn("7", 1, 0, self.STYLE_DARK)
            self.digit_btns['8'] = add_btn("8", 1, 1, self.STYLE_DARK)
            self.digit_btns['9'] = add_btn("9", 1, 2, self.STYLE_DARK)
            self.func_btns['×'] = add_btn("×", 1, 3, self.STYLE_ORANGE)

            # --- 버튼 추가(행 2: 4, 5, 6, −) ---
            self.digit_btns['4'] = add_btn("4", 2, 0, self.STYLE_DARK)
            self.digit_btns['5'] = add_btn("5", 2, 1, self.STYLE_DARK)
            self.digit_btns['6'] = add_btn("6", 2, 2, self.STYLE_DARK)
            self.func_btns['−'] = add_btn("−", 2, 3, self.STYLE_ORANGE)

            # --- 버튼 추가(행 3: 1, 2, 3, +) ---
            self.digit_btns['1'] = add_btn("1", 3, 0, self.STYLE_DARK)
            self.digit_btns['2'] = add_btn("2", 3, 1, self.STYLE_DARK)
            self.digit_btns['3'] = add_btn("3", 3, 2, self.STYLE_DARK)
            self.func_btns['+'] = add_btn("+", 3, 3, self.STYLE_ORANGE)

            # --- 버튼 추가(행 4: 0(가로 2칸), ., =) ---
            self.digit_btns['0'] = add_btn("0", 4, 0, self.STYLE_ZERO, colspan=2)
            self.func_btns['.'] = add_btn(".", 4, 2, self.STYLE_DARK)
            self.func_btns['='] = add_btn("=", 4, 3, self.STYLE_ORANGE)

            root.addLayout(grid) # 버튼 그리드 레이아웃 추가       
    
        # --- 핸들러 연결 메소드 ---
        def set_handler(self, on_clear, on_negate, on_percent, on_operator, on_digit, on_decimal, on_equals):
            # 숫자 버튼들(0~9)에 클릭 핸들러 연결
            for d in range(10):
                self.digit_btns[str(d)].clicked.connect(lambda _=None, x=str(d): on_digit(x))

            # 연산자 버튼들(+, −, ×, ÷)에 클릭 핸들러 연결
            self.func_btns['+'].clicked.connect(lambda _=None, x='+':  on_operator(x))
            self.func_btns['−'].clicked.connect(lambda _=None, x='-':  on_operator(x))
            self.func_btns['×'].clicked.connect(lambda _=None, x='*':  on_operator(x))
            self.func_btns['÷'].clicked.connect(lambda _=None, x='/':  on_operator(x))

            # 기타 기능 버튼들(AC, +/−, %, ., =)에 클릭 핸들러 연결
            self.func_btns['AC'].clicked.connect(on_clear)
            self.func_btns['+/−'].clicked.connect(on_negate)
            self.func_btns['%'].clicked.connect(on_percent)
            self.func_btns['.'].clicked.connect(on_decimal)
            self.func_btns['='].clicked.connect(on_equals)

        # --- 키보드 연결 메소드 ---
        def keyPressEvent(self, event: QKeyEvent):
            # 키 입력 값이 있다면, _key_handler 에 담기
            if self._key_handler is not None:
                self._key_handler(event)
            else:
                super().keyPressEvent(event)


        
        # ==============================================================================
        # 폰트 조절 메소드
        # ==============================================================================
        # --- 출력창 폰트 크기 설정 메소드 ---
        def _set_display_font(self, size: int):
            # 출력창 폰트를 지정된 크기로 바꾼다 (Thin 굵기)
            self.display.setFont(QFont("Helvetica", size, QFont.Weight.Thin))

        # --- 출력창 폰트 크기 조절 메소드 ---
        def _adjust_display_font(self, text: str):
            # 폰트 크기 후보들 큰 순서대로 반환
            for size in self.DISPLAY_FONT_CANDIDATES:
                # 글꼴, 크기, 굵기 설정
                font = QFont("Helvetica", size, QFont.Weight.Thin)
                # horizontalAdvance로 수평으로 차지하는 픽셀 수 계산, DISPLAY_TEXT_WIDTH보다 작거나 같으면 그 폰트로 설정하고 반환
                if QFontMetrics(font).horizontalAdvance(text) <= self.DISPLAY_TEXT_WIDTH:
                    self.display.setFont(font)
                    return
            # 후보 중 어느 것도 안 들어가면 가장 작은 폰트로 설정
            self.display.setFont(QFont("Helvetica", 16, QFont.Weight.Thin))
        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    view_c = view()
    view_c.show()
    sys.exit(app.exec())
