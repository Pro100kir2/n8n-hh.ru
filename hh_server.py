import http.server
import json
import logging
import urllib.parse
from http import HTTPStatus
from typing import Any, Dict

# Import business logic
from apply_vacancy import apply_to_vacancy
from search_vacancies import search_vacancies

import os
from dotenv import load_dotenv

load_dotenv()

# -------------------- CONFIGURATION & LOGGING --------------------

HOST = os.getenv("SERVER_HOST", "127.0.0.1")
PORT = int(os.getenv("SERVER_PORT", 8000))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("HHServer")



class HHRequestHandler(http.server.BaseHTTPRequestHandler):
    
    def do_GET(self):
        """Handle GET requests (Search)."""
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        
        if path == "/search":
            query_params = urllib.parse.parse_qs(parsed_url.query)
            self._handle_search(query_params)
        else:
            self._send_json_response(
                {"error": "Not Found", "path": path}, 
                status_code=HTTPStatus.NOT_FOUND
            )

    def do_POST(self):
        """Handle POST requests (Apply)."""
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        if path == "/apply":
            self._handle_apply()
        else:
            self._send_json_response(
                {"error": "Not Found", "path": path}, 
                status_code=HTTPStatus.NOT_FOUND
            )

    def _handle_search(self, query_params: Dict[str, list]):
        """Logic for vacancy search."""
        search_text = query_params.get("text", ["Frontend"])[0]
        page_num = int(query_params.get("page", ["0"])[0])
        logger.info(f"Processing Search Request: {search_text}, page {page_num}")
        
        try:
            vacancies = search_vacancies(search_text, page_num)
            
            if vacancies is None:
                self._send_json_response(
                    {"error": "Search returned no data. Check server logs (session might be invalid)."}, 
                    status_code=HTTPStatus.INTERNAL_SERVER_ERROR
                )
            else:
                self._send_json_response(vacancies)
                
        except Exception as e:
            logger.error(f"Search failed: {e}", exc_info=True)
            self._send_json_response(
                {"error": "Internal Server Error", "message": str(e)}, 
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR
            )

    def _handle_apply(self):
        """Logic for applying to a vacancy."""
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length == 0:
                self._send_json_response(
                    {"error": "Empty body"}, 
                    status_code=HTTPStatus.BAD_REQUEST
                )
                return

            body = self.rfile.read(content_length)
            data = json.loads(body.decode("utf-8"))
            
            url = data.get("url")
            message = data.get("message", "")

            if not url:
                self._send_json_response(
                    {"error": "Missing 'url' field"}, 
                    status_code=HTTPStatus.BAD_REQUEST
                )
                return

            logger.info(f"Processing Apply Request for: {url}")
            result = apply_to_vacancy(url, message)
            self._send_json_response(result)

        except json.JSONDecodeError:
            self._send_json_response(
                {"error": "Invalid JSON"}, 
                status_code=HTTPStatus.BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Apply failed: {e}", exc_info=True)
            self._send_json_response(
                {"error": "Internal Server Error", "message": str(e)}, 
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR
            )

    def _send_json_response(self, data: Any, status_code: int = 200):
        """Helper to send valid JSON responses."""
        response_body = json.dumps(data, ensure_ascii=False)
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(response_body.encode("utf-8"))


# -------------------- MAIN --------------------

def run_server():
    server_address = (HOST, PORT)
    
    httpd = http.server.HTTPServer(server_address, HHRequestHandler)
    logger.info(f"HH Proxy Server running on http://{HOST}:{PORT}")
    logger.info("Endpoints:")
    logger.info(f"  GET  /search?text=Frontend")
    logger.info(f"  POST /apply  {{ 'url': '...', 'message': '...' }}")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Stopping server...")
        httpd.server_close()

if __name__ == "__main__":
    run_server()
