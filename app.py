# app.py - 완전 수정 버전
import streamlit as st
import boto3
from datetime import datetime
import time
import os

st.set_page_config(page_title="S3 Log Analyzer Setup", page_icon="📊")

class AthenaTableCreator:
    def __init__(self, region_name='us-east-1'):
        self.region = region_name
        self.s3_client = boto3.client('s3', region_name=region_name)
        self.athena_client = boto3.client('athena', region_name=region_name)
        self.glue_client = boto3.client('glue', region_name=region_name)
        
    def list_s3_buckets(self):
        """S3 버킷 목록 가져오기"""
        try:
            response = self.s3_client.list_buckets()
            return [bucket['Name'] for bucket in response['Buckets']]
        except Exception as e:
            st.error(f"Error listing buckets: {str(e)}")
            return []
    
    def list_s3_folders(self, bucket_name, prefix=''):
        """S3 버킷 내 폴더 목록 가져오기"""
        try:
            paginator = self.s3_client.get_paginator('list_objects_v2')
            folders = set()
            
            for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix, Delimiter='/'):
                if 'CommonPrefixes' in page:
                    for prefix_info in page['CommonPrefixes']:
                        folders.add(prefix_info['Prefix'])
            
            return sorted(list(folders))
        except Exception as e:
            st.error(f"Error listing folders: {str(e)}")
            return []
    
    def verify_log_files(self, bucket_name, prefix=''):
        """로그 파일 존재 확인"""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=bucket_name,
                Prefix=prefix,
                MaxKeys=5
            )
            
            if 'Contents' in response:
                files = [obj['Key'] for obj in response['Contents']]
                return True, files
            else:
                return False, []
        except Exception as e:
            return False, [str(e)]
    
    def create_database(self, database_name, s3_output_location):
        """Athena 데이터베이스 생성"""
        query = f"CREATE DATABASE IF NOT EXISTS {database_name}"
        
        response = self.athena_client.start_query_execution(
            QueryString=query,
            ResultConfiguration={'OutputLocation': s3_output_location}
        )
        
        return response['QueryExecutionId']
    
    def create_s3_access_log_table(self, database_name, table_name, s3_location, s3_output_location):
        """S3 Access Log 테이블 자동 생성 - 올바른 RegEx 패턴"""
        
        # 올바른 이스케이프 처리
        create_table_query = f"""
        CREATE EXTERNAL TABLE IF NOT EXISTS `{database_name}.{table_name}`(
          `bucketowner` STRING, 
          `bucket_name` STRING, 
          `requestdatetime` STRING, 
          `remoteip` STRING, 
          `requester` STRING, 
          `requestid` STRING, 
          `operation` STRING, 
          `key` STRING, 
          `request_uri` STRING, 
          `httpstatus` STRING, 
          `errorcode` STRING, 
          `bytessent` BIGINT, 
          `objectsize` BIGINT, 
          `totaltime` STRING, 
          `turnaroundtime` STRING, 
          `referrer` STRING, 
          `useragent` STRING, 
          `versionid` STRING, 
          `hostid` STRING, 
          `sigv` STRING, 
          `ciphersuite` STRING, 
          `authtype` STRING, 
          `endpoint` STRING, 
          `tlsversion` STRING,
          `accesspointarn` STRING,
          `aclrequired` STRING)
        ROW FORMAT SERDE 
          'org.apache.hadoop.hive.serde2.RegexSerDe' 
        WITH SERDEPROPERTIES ( 
          'input.regex'='([^ ]*) ([^ ]*) \\\\[(.*?)\\\\] ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*) (\"[^\"]*\"|-) (-|[0-9]*) ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*) (\"[^\"]*\"|-) ([^ ]*)(?: ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*))?.*$$') 
        STORED AS INPUTFORMAT 
          'org.apache.hadoop.mapred.TextInputFormat' 
        OUTPUTFORMAT 
          'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
        LOCATION
          '{s3_location}'
        """
        
        response = self.athena_client.start_query_execution(
            QueryString=create_table_query,
            QueryExecutionContext={'Database': database_name},
            ResultConfiguration={'OutputLocation': s3_output_location}
        )
        
        return response['QueryExecutionId']
    
    def test_table_query(self, database_name, table_name, s3_output_location):
        """테이블 데이터 테스트 쿼리"""
        test_query = f"SELECT COUNT(*) as row_count FROM {database_name}.{table_name}"
        
        response = self.athena_client.start_query_execution(
            QueryString=test_query,
            QueryExecutionContext={'Database': database_name},
            ResultConfiguration={'OutputLocation': s3_output_location}
        )
        
        return response['QueryExecutionId']
    
    def get_query_result(self, query_execution_id):
        """쿼리 결과 가져오기"""
        try:
            response = self.athena_client.get_query_results(
                QueryExecutionId=query_execution_id,
                MaxResults=1
            )
            
            if response['ResultSet']['Rows']:
                if len(response['ResultSet']['Rows']) > 1:
                    return response['ResultSet']['Rows'][1]['Data'][0].get('VarCharValue', '0')
            return '0'
        except:
            return 'Error'
    
    def wait_for_query(self, query_execution_id):
        """쿼리 실행 완료 대기"""
        max_attempts = 30
        for i in range(max_attempts):
            response = self.athena_client.get_query_execution(
                QueryExecutionId=query_execution_id
            )
            status = response['QueryExecution']['Status']['State']
            
            if status in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
                return status, response
            
            time.sleep(1)
        
        return 'TIMEOUT', response

# Streamlit UI
def main():
    st.title("🚀 S3 Log Analyzer - Auto Setup")
    st.markdown("S3 Access Log를 위한 Athena 테이블을 자동으로 생성합니다")
    
    # Sidebar 설정
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # AWS 리전 선택
        regions = [
            'us-east-1', 'us-west-2', 'eu-west-1', 'eu-central-1',
            'ap-northeast-1', 'ap-northeast-2', 'ap-southeast-1', 'ap-southeast-2'
        ]
        
        default_region = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
        
        selected_region = st.selectbox(
            "AWS Region",
            regions,
            index=regions.index(default_region) if default_region in regions else 0,
            help="Select the AWS region where your S3 buckets are located"
        )
        
        # Athena 결과 저장 위치
        athena_output = st.text_input(
            "Athena Output Location",
            value=f"s3://athena-results-{datetime.now().strftime('%Y%m%d')}/",
            help="Athena 쿼리 결과를 저장할 S3 위치"
        )
        
        # AWS 자격 증명 상태 확인
        st.subheader("🔐 AWS Credentials")
        try:
            sts = boto3.client('sts', region_name=selected_region)
            identity = sts.get_caller_identity()
            st.success(f"✅ Connected as: {identity['Arn'].split('/')[-1]}")
        except Exception as e:
            st.error("❌ AWS credentials not configured")
            return
    
    # AthenaTableCreator 인스턴스 생성
    try:
        creator = AthenaTableCreator(region_name=selected_region)
    except Exception as e:
        st.error(f"Failed to initialize AWS clients: {str(e)}")
        return
    
    # Main UI
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📁 S3 Log Location")
        
        # 버킷 선택
        buckets = creator.list_s3_buckets()
        if not buckets:
            st.warning("No S3 buckets found in this region")
            return
            
        selected_bucket = st.selectbox("Select Log Bucket", buckets)
        
        # 폴더 선택 (선택사항)
        if selected_bucket:
            folders = creator.list_s3_folders(selected_bucket)
            if folders:
                selected_folder = st.selectbox("Select Folder (Optional)", [''] + folders)
            else:
                selected_folder = ''
                st.info("No folders found in bucket")
    
    with col2:
        st.subheader("🗄️ Database Configuration")
        
        # 데이터베이스 이름 자동 생성
        safe_bucket_name = selected_bucket.replace('-', '_').replace('.', '_')
        default_db_name = f"s3_logs_{safe_bucket_name}"[:64]
        db_name = st.text_input("Database Name", value=default_db_name)
        
        # 테이블 이름 자동 생성
        default_table_name = "access_logs"
        table_name = st.text_input("Table Name", value=default_table_name)
    
    # S3 경로 미리보기
    s3_location = f"s3://{selected_bucket}/"
    if selected_folder:
        s3_location = f"s3://{selected_bucket}/{selected_folder}"
        # 폴더 선택 시 끝의 슬래시 제거 (이미 폴더명에 포함됨)
        if s3_location.endswith('//'):
            s3_location = s3_location[:-1]
    
    st.info(f"📍 S3 Location: `{s3_location}`")
    st.info(f"🌍 Region: `{selected_region}`")
    
    # 로그 파일 존재 확인
    if st.button("🔍 Verify Log Files"):
        prefix = selected_folder if selected_folder else ''
        exists, files = creator.verify_log_files(selected_bucket, prefix)
        
        if exists:
            st.success(f"✅ Found {len(files)} log files")
            with st.expander("View sample files"):
                for file in files[:5]:
                    st.text(file)
        else:
            st.warning("⚠️ No log files found in this location")
            st.info("Make sure S3 Server Access Logging is enabled and logs have been generated")
    
    # 생성 버튼
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🎯 Create Database & Table", type="primary", use_container_width=True):
            with st.spinner("Creating resources..."):
                try:
                    # 1. 데이터베이스 생성
                    st.write("1️⃣ Creating database...")
                    db_query_id = creator.create_database(db_name, athena_output)
                    status, _ = creator.wait_for_query(db_query_id)
                    
                    if status == 'SUCCEEDED':
                        st.success(f"✅ Database '{db_name}' created!")
                    else:
                        st.error(f"Failed to create database: {status}")
                        return
                    
                    # 2. 테이블 생성
                    st.write("2️⃣ Creating table...")
                    table_query_id = creator.create_s3_access_log_table(
                        db_name, table_name, s3_location, athena_output
                    )
                    status, response = creator.wait_for_query(table_query_id)
                    
                    if status == 'SUCCEEDED':
                        st.success(f"✅ Table '{db_name}.{table_name}' created!")
                        
                        # 3. 데이터 확인
                        st.write("3️⃣ Verifying data...")
                        test_query_id = creator.test_table_query(db_name, table_name, athena_output)
                        test_status, _ = creator.wait_for_query(test_query_id)
                        
                        if test_status == 'SUCCEEDED':
                            row_count = creator.get_query_result(test_query_id)
                            if row_count != '0' and row_count != 'Error':
                                st.success(f"✅ Table contains {row_count} rows of data!")
                            else:
                                st.warning("⚠️ Table created but no data found")
                                st.info(f"""
                                Possible reasons:
                                1. Log files haven't been generated yet (wait 5-15 minutes)
                                2. Wrong S3 location selected (current: {s3_location})
                                3. Log format mismatch
                                
                                Try these queries in Athena console:
                                ```sql
                                -- Check table
                                SELECT * FROM {db_name}.{table_name} LIMIT 10;
                                
                                -- Show table location
                                SHOW CREATE TABLE {db_name}.{table_name};
                                ```
                                """)
                        
                        st.balloons()
                        
                        with st.expander("📋 Sample Queries"):
                            st.markdown(f"""
                            ```sql
                            -- Check if data exists
                            SELECT COUNT(*) FROM {db_name}.{table_name};
                            
                            -- View first 10 logs
                            SELECT * FROM {db_name}.{table_name} LIMIT 10;
                            
                            -- Count by HTTP status
                            SELECT httpstatus, COUNT(*) as count
                            FROM {db_name}.{table_name}
                            WHERE httpstatus IS NOT NULL
                            GROUP BY httpstatus
                            ORDER BY count DESC;
                            
                            -- Find 404 errors
                            SELECT requestdatetime, key, remoteip, httpstatus
                            FROM {db_name}.{table_name}
                            WHERE httpstatus = '404';
                            
                            -- Top requested files
                            SELECT key, COUNT(*) as requests
                            FROM {db_name}.{table_name}
                            WHERE key IS NOT NULL
                            GROUP BY key
                            ORDER BY requests DESC
                            LIMIT 20;
                            ```
                            """)
                    else:
                        st.error(f"Failed to create table: {status}")
                        if 'QueryExecution' in response and 'Status' in response['QueryExecution']:
                            if 'StateChangeReason' in response['QueryExecution']['Status']:
                                st.error(response['QueryExecution']['Status']['StateChangeReason'])
                
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    # 디버깅 섹션
    with st.expander("🔧 Troubleshooting & Manual DDL"):
        st.markdown("""
        ### If no data appears:
        
        1. **Verify log files exist** using the "Verify Log Files" button above
        2. **Check S3 path** - make sure it points to where log files are stored
        3. **Wait for logs** - S3 Access Logs can take 5-15 minutes to appear
        
        ### Manual DDL for Athena Console:
        Copy and paste this into Athena console, replacing the LOCATION:
        """)
        
        st.code(f"""
                CREATE EXTERNAL TABLE `s3_access_logs_db.mybucket_logs`(
                `bucketowner` STRING, 
                `bucket_name` STRING, 
                `requestdatetime` STRING, 
                `remoteip` STRING, 
                `requester` STRING, 
                `requestid` STRING, 
                `operation` STRING, 
                `key` STRING, 
                `request_uri` STRING, 
                `httpstatus` STRING, 
                `errorcode` STRING, 
                `bytessent` BIGINT, 
                `objectsize` BIGINT, 
                `totaltime` STRING, 
                `turnaroundtime` STRING, 
                `referrer` STRING, 
                `useragent` STRING, 
                `versionid` STRING, 
                `hostid` STRING, 
                `sigv` STRING, 
                `ciphersuite` STRING, 
                `authtype` STRING, 
                `endpoint` STRING, 
                `tlsversion` STRING,
                `accesspointarn` STRING,
                `aclrequired` STRING)
                ROW FORMAT SERDE 
                'org.apache.hadoop.hive.serde2.RegexSerDe' 
                WITH SERDEPROPERTIES ( 
                'input.regex'='([^ ]*) ([^ ]*) \\[(.*?)\\] ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*) (\"[^\"]*\"|-) (-|[0-9]*) ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*) (\"[^\"]*\"|-) ([^ ]*)(?: ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*))?.*$') 
                STORED AS INPUTFORMAT 
                'org.apache.hadoop.mapred.TextInputFormat' 
                OUTPUTFORMAT 
                'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
                LOCATION '{s3_location}';
                """, language='sql'
                )

if __name__ == "__main__":
    main()
