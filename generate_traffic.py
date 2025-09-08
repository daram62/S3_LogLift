import boto3
import random
import time
from datetime import datetime

s3 = boto3.client('s3')
bucket = 's3log-app'

# 다양한 패턴의 트래픽 생성
operations = [
    ('GET', 'test1.txt'),
    ('GET', 'test2.txt'),
    ('GET', 'folder1/test2.txt'),
    ('HEAD', 'large.txt'),
    ('GET', 'non-existent.txt'),  # 404 에러 생성
    ('GET', 'folder2/large.txt'),
]

print(f"🚀 Starting traffic generation at {datetime.now()}")

for i in range(50):
    op, key = random.choice(operations)
    try:
        if op == 'GET':
            s3.get_object(Bucket=bucket, Key=key)
        elif op == 'HEAD':
            s3.head_object(Bucket=bucket, Key=key)
        print(f"✓ {op} {key}")
    except:
        print(f"✗ {op} {key} (expected error)")
    
    time.sleep(random.uniform(0.5, 2))

print("⏳ Wait 5-15 minutes for logs to appear...")