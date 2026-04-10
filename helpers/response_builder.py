from flask import jsonify

class ResponseBuilder:
    """Helper class for building standard API responses"""

    @staticmethod
    def success(message='Success', data=None):
        """Build success response"""
        if data is None:
            data = {}
        return {
            'success': True,
            'message': message,
            'data': data
        }

    @staticmethod
    def error(message='Error', code=400):
        """Build error response"""
        return {
            'success': False,
            'message': message,
            'code': code
        }, code

    @staticmethod
    def json_response(response, status_code=200):
        """Return JSON response"""
        if isinstance(response, tuple):
            return jsonify(response[0]), response[1]
        return jsonify(response), status_code
