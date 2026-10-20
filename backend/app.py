from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
from routes.keyword_routes import keyword_bp
from routes.literature_routes import literature_bp
from routes.summary_routes import summary_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app, resources={r"/api/*": {"origins": ["http://localhost:5173", "http://127.0.0.1:5173"]}})

    app.register_blueprint(keyword_bp)
    app.register_blueprint(literature_bp)
    app.register_blueprint(summary_bp)

    @app.errorhandler(404)
    def not_found(_e):
        return jsonify({"code": 404, "message": "接口不存在", "data": None}), 404

    @app.errorhandler(500)
    def internal_error(_e):
        return jsonify({"code": 500, "message": "服务内部错误，请稍后重试", "data": None}), 500

    @app.get("/api/health")
    def health():
        return jsonify({"code": 0, "message": "ok", "data": {"status": "up"}})

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)