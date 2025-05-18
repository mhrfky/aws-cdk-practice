import boto3
import os
from datetime import datetime, timedelta


class TimestreamService:
    def __init__(self):
        self.client = boto3.client('timestream-query')
        self.db_name = os.environ.get('TIMESTREAM_DB_NAME')
        self.events_table = os.environ.get('TIMESTREAM_EVENTS_TABLE')
        self.file_types_table = os.environ.get('TIMESTREAM_FILE_TYPES_TABLE')

    def get_file_types(self):
        try:
            query = f"""
            SELECT file_extension as extension, count as count, last_update
            FROM "{self.db_name}"."{self.file_types_table}"
            ORDER BY count DESC
            """

            result = self.client.query(QueryString=query)

            data = []
            for row in result['Rows']:
                item = {}
                for i, col in enumerate(row['Data']):
                    if 'ScalarValue' in col:
                        if i == 0:
                            item['extension'] = col['ScalarValue']
                        elif i == 1:
                            item['count'] = int(col['ScalarValue'])
                        elif i == 2:
                            item['last_update'] = col['ScalarValue']
                data.append(item)

            return data
        except Exception as e:
            print(f"Error querying file types: {str(e)}")
            return []

    def get_recent_files(self, hours=1):
        try:
            one_hour_ago = (datetime.utcnow() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')

            query = f"""
            SELECT key, size, file_extension, time
            FROM "{self.db_name}"."{self.events_table}"
            WHERE time > '{one_hour_ago}'
            ORDER BY time DESC
            LIMIT 20
            """

            result = self.client.query(QueryString=query)

            data = []
            for row in result['Rows']:
                item = {}
                for i, col in enumerate(row['Data']):
                    if 'ScalarValue' in col:
                        if i == 0:
                            item['key'] = col['ScalarValue']
                        elif i == 1:
                            item['size'] = int(col['ScalarValue'])
                        elif i == 2:
                            item['file_extension'] = col['ScalarValue']
                        elif i == 3:
                            item['timestamp'] = col['ScalarValue']
                data.append(item)

            return data
        except Exception as e:
            print(f"Error querying recent files: {str(e)}")
            return []