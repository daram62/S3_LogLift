# S3 Log Analyzer - Auto Setup

S3 Access Log를 위한 Athena 테이블을 자동으로 생성하는 Streamlit 앱입니다.

## 기능
- S3 버킷 및 폴더 자동 탐색
- Athena 데이터베이스 및 테이블 자동 생성
- S3 Access Log 파싱을 위한 최적화된 RegEx 패턴
- 실시간 로그 파일 검증
- 샘플 쿼리 제공

## 사용 방법
1. AWS 자격 증명 설정 필요
2. S3 버킷에서 로그 위치 선택
3. 데이터베이스 및 테이블 이름 설정
4. "Create Database & Table" 버튼 클릭

## 배포
이 앱은 Streamlit Community Cloud에서 실행됩니다.