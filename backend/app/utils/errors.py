from flask import jsonify
import logging

logger = logging.getLogger(__name__)

class APIError(Exception):
    """API错误基类"""
    def __init__(self, message, status_code=400, error_code=None, code=None, data=None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or code
        self.data = data
        super().__init__(self.message)

def register_error_handlers(app):
    """注册错误处理器"""
    
    @app.errorhandler(APIError)
    def handle_api_error(error):
        """处理API错误"""
        logger.error(f"API Error: {error.message}", exc_info=True)
        response = {
            'success': False,
            'message': error.message,
            'error_code': error.error_code
        }
        if error.data is not None:
            response['data'] = error.data
        return jsonify(response), error.status_code
    
    @app.errorhandler(404)
    def handle_not_found(error):
        """处理404错误"""
        return jsonify({
            'success': False,
            'message': '资源不存在'
        }), 404
    
    @app.errorhandler(500)
    def handle_internal_error(error):
        """处理500错误"""
        logger.error(f"Internal Error: {str(error)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': '服务器内部错误'
        }), 500
    
    @app.errorhandler(Exception)
    def handle_general_error(error):
        """处理其他错误"""
        logger.error(f"Unexpected Error: {str(error)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': '发生未知错误'
        }), 500

