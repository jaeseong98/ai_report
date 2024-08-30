# 기업 보고서 생성기

이 프로젝트는 특정 기업에 대한 분석 보고서를 자동으로 생성하는 파이썬 스크립트입니다. 오디오 분석, 기업 데이터 수집, HTML 보고서 생성 등의 기능을 포함합니다.

## 기능

- 오디오 파일 분석 및 보고서 생성
- 기업 기본 정보 및 재무 정보 수집
- HTML 형식의 보고서 생성 (선택적 그래프 포함)

## 설치

1. 이 저장소를 클론합니다:

   ```
   git clone [저장소 URL]
   ```

2. 프로젝트 디렉토리로 이동합니다:

   ```
   cd [프로젝트 디렉토리]
   ```

3. 가상환경을 생성하고 활성화합니다:

   ```
   python -m venv venv
   source venv/bin/activate  # Linux 또는 macOS
   # 또는
   venv/Scripts/activate  # Windows
   ```

4. 필요한 패키지를 설치합니다:

   ```
   pip install -r requirements.txt
   ```

## 사용 방법

가상환경이 활성화된 상태에서:

기본 실행 (LG화학 데이터 사용):

```
python main.py --audio 'mp3/lg_chem.mp3' --company_code '051910' 
```

다른 회사 코드와 그래프를 포함한 보고서 생성:

```
python main.py --audio 'mp3/lg_chem.mp3' --company_code '051910'  --graph
```

### 매개변수 설명:

- `--audio`: 분석할 오디오 파일의 경로 (필수)
- `--company_code`: 분석할 회사의 코드 (선택, 기본값: 051910 - LG화학)
- `--graph`: 보고서에 그래프 포함 (선택)

## 의존성

- selenium
- webdriver_manager
- python-dotenv 
- pydub
- tenacity
- openai==0.28.0
- pandas
- jinja2
- lxml
- Pillow

## 프로젝트 구조

- `main.py`: 메인 스크립트
- `lib/`: 핵심 기능을 포함하는 라이브러리 디렉토리
  - `audio_analysis_report.py`: 오디오 분석 및 보고서 생성
  - `company_data_collector.py`: 기업 데이터 수집
  - `html_generator.py`: HTML 보고서 생성
- `output/`: 생성된 보고서 저장 디렉토리

## 참고 사항

- 프로젝트를 실행할 때마다 가상환경을 활성화해야 합니다.
- 오디오 파일 경로는 실제 파일 위치에 맞게 지정해야 합니다.

## 가상환경 비활성화

작업을 마친 후 가상환경을 비활성화하려면:

```
deactivate
```

## 라이선스

[라이선스 정보를 추가해주세요]

