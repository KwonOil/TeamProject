# TeamProject

간단한 Flask 웹 서버로 서비스의 기본 뼈대를 빠르게 검증할 수 있습니다. 홈 화면과 JSON 형태의 헬스체크 엔드포인트를 제공하므로 추후 API 확장 시에 기반 코드로 활용할 수 있습니다.

## 요구 사항
- Python 3.10 이상
- 가상환경(선택) 및 `pip`

## 로컬 실행 방법
1. (선택) 가상환경 생성
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
2. 의존성 설치
   ```powershell
   pip install -r requirements.txt
   ```
3. 서버 실행
   ```powershell
   python app.py
   ```
   - 기본 포트는 `5000`이며 `PORT` 환경 변수를 지정하면 덮어쓸 수 있습니다.
   - `FLASK_DEBUG=1`을 지정하면 디버그 모드가 활성화됩니다.

## 엔드포인트
- `/` : 현재 서버 시각을 렌더링하는 기본 페이지
- `/api/health` : JSON으로 서버 상태를 반환 (배포 시 헬스체크 용도)

## 다음 단계 아이디어
- `/api/health` 응답에 실제 비즈니스 서비스의 의존성 상태(데이터베이스, 외부 API 등)를 포함
- 템플릿/정적 리소스를 분리하여 UI를 확장
- Blueprint 구조로 API 버전이나 도메인 별 라우팅을 추가
