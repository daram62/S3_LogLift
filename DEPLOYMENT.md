# 🚀 배포 가이드

## Streamlit Community Cloud 배포 (추천)

### 1. GitHub 리포지토리 준비
```bash
git init
git add .
git commit -m "Initial commit: S3 Log Analyzer"
git branch -M main
git remote add origin https://github.com/yourusername/s3-log-analyzer.git
git push -u origin main
```

### 2. Streamlit Community Cloud 배포
1. https://share.streamlit.io 접속
2. GitHub 계정으로 로그인
3. "New app" 클릭
4. GitHub 리포지토리 선택
5. Main file path: `app.py`
6. Deploy 클릭

### 3. 사용자 안내
배포된 앱 URL을 사용자들에게 공유하면, 각자 자신의 AWS 자격 증명으로 접속할 수 있습니다.

**사용자에게 안내할 내용:**
- AWS 자격 증명 (Access Key ID, Secret Access Key) 준비
- 필요한 AWS 권한: S3ReadOnly, AthenaFull, GlueConsole
- 자격 증명은 앱에서만 사용되며 저장되지 않음

## 다른 배포 옵션들

### Railway
1. https://railway.app 접속
2. GitHub 리포지토리 연결
3. 자동 배포

### Heroku
```bash
# Procfile 생성
echo "web: streamlit run app.py --server.port=\$PORT --server.address=0.0.0.0" > Procfile

# 배포
git add Procfile
git commit -m "Add Procfile for Heroku"
heroku create your-app-name
git push heroku main
```

### AWS EC2 (직접 관리)
```bash
# EC2 인스턴스에서
sudo apt update
sudo apt install python3-pip
pip3 install streamlit boto3

# 앱 실행
streamlit run app.py --server.port=8501 --server.address=0.0.0.0
```

## 보안 고려사항

### 1. 사용자 교육
- AWS 자격 증명 보안 관리 방법
- 최소 권한 원칙 적용
- 정기적인 키 로테이션

### 2. 앱 보안
- HTTPS 사용 (Streamlit Cloud는 기본 제공)
- 자격 증명 메모리에서만 사용
- 세션 종료 시 자동 삭제

### 3. AWS 권한 최소화
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket",
                "s3:GetObject",
                "s3:ListAllMyBuckets"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "athena:*",
                "glue:GetDatabase",
                "glue:GetTable",
                "glue:CreateDatabase",
                "glue:CreateTable"
            ],
            "Resource": "*"
        }
    ]
}
```

## 사용자 가이드 예시

배포 후 사용자들에게 제공할 수 있는 간단한 가이드:

```
🎯 S3 Log Analyzer 사용법

1. 앱 접속: [배포된 URL]
2. AWS 자격 증명 입력:
   - Access Key ID
   - Secret Access Key
3. 리전 선택 후 S3 버킷 선택
4. "Create Database & Table" 클릭
5. Athena Console에서 결과 확인

⚠️ 주의: 자격 증명은 안전하게 관리하세요!
```