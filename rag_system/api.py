"""
RAG系统API服务
"""

from flask import Flask, request, jsonify
from services.rag_pipeline import rag_pipeline
import os

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({"status": "healthy", "service": "RAG System"})

@app.route('/query', methods=['POST'])
def process_query():
    """处理查询接口"""
    try:
        # 获取请求数据
        data = request.get_json()
        query = data.get('query')
        session_id = data.get('session_id', 'default')
        
        if not query:
            return jsonify({"error": "查询内容不能为空"}), 400
        
        # 处理查询
        result = rag_pipeline.process_query(query, session_id)
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/query', methods=['GET'])
def query_form():
    """简单的查询表单"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>RAG知识库系统</title>
        <meta charset="utf-8">
    </head>
    <body>
        <h1>RAG知识库系统</h1>
        <form id="queryForm">
            <textarea name="query" id="query" placeholder="请输入您的问题..." rows="4" cols="50"></textarea><br><br>
            <input type="text" name="session_id" id="session_id" placeholder="会话ID（可选）" value="default"><br><br>
            <button type="submit">提交</button>
        </form>
        <div id="result"></div>
        
        <script>
            document.getElementById('queryForm').addEventListener('submit', function(e) {
                e.preventDefault();
                
                const query = document.getElementById('query').value;
                const session_id = document.getElementById('session_id').value;
                
                fetch('/query', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({query: query, session_id: session_id})
                })
                .then(response => response.json())
                .then(data => {
                    document.getElementById('result').innerHTML = '<h2>答案：</h2><p>' + data.answer + '</p>';
                })
                .catch(error => {
                    document.getElementById('result').innerHTML = '<p style="color: red;">错误：' + error + '</p>';
                });
            });
        </script>
    </body>
    </html>
    '''

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=True)