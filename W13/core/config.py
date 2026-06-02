"""프로그램 전역에서 공유하는 설정 상수 모음."""

REQUIREMENTS_FILE = 'requirements.txt'
RECORDS_DIR = 'records'
CHUNK = 1024        # 녹음 스트림에서 한 번에 읽는 프레임 수
CHANNELS = 1        # 모노(채널 1개)로 녹음
RATE = 44100        # 샘플레이트(Hz)
SAMPLE_WIDTH = 2    # 샘플당 바이트 수, int16(16비트)에 대응
