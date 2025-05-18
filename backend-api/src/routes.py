from flask import jsonify
from .timestream_service import TimestreamService

timestream_service = TimestreamService()

def register_routes(app):
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({"status": "healthy"})

    @app.route('/api/file-types', methods=['GET'])
    def get_file_types():
        data = timestream_service.get_file_types()
        return jsonify(data)

    @app.route('/api/recent-files', methods=['GET'])
    def get_recent_files():
        data = timestream_service.get_recent_files()
        return jsonify(data)