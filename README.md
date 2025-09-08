# S3 Log Analyzer - Auto Setup

S3 Access Log를 위한 Athena 테이블을 자동으로 생성하는 Streamlit 앱입니다.

## 🌟 주요 기능
- **사용자별 AWS 자격 증명 입력**: 각 사용자가 자신의 AWS 계정으로 접속
- **S3 버킷 및 폴더 자동 탐색**: 실시간으로 S3 구조 확인
- **Athena 테이블 자동 생성**: 복잡한 DDL 없이 원클릭 생성
- **S3 Access Log 최적화**: 정확한 RegEx 패턴으로 로그 파싱
- **실시간 검증**: 로그 파일 존재 및 데이터 확인
- **샘플 쿼리 제공**: 바로 사용할 수 있는 분석 쿼리

## 🚀 사용 방법

### 1. AWS 자격 증명 준비
- AWS Console → IAM → Users → Security credentials
- Create access key (CLI 용도로 생성)
- 필요 권한: S3ReadOnly, AthenaFull, GlueConsole

### 2. 앱 사용
1. **AWS 자격 증명 입력**: Access Key ID와 Secret Access Key
2. **리전 선택**: S3 버킷이 있는 AWS 리전
3. **S3 위치 선택**: 로그가 저장된 버킷과 폴더
4. **테이블 생성**: 원클릭으로 Athena 테이블 생성

### 3. 결과 확인
- Athena Console에서 생성된 테이블 확인
- 제공된 샘플 쿼리로 로그 분석 시작

## 🔒 보안
- 자격 증명은 세션 중에만 사용되며 저장되지 않음
- HTTPS 연결로 데이터 전송 보호
- 최소 권한 원칙 권장

## 🌐 배포
이 앱은 Streamlit Community Cloud에서 실행되며, 누구나 자신의 AWS 계정으로 접속하여 사용할 수 있습니다.