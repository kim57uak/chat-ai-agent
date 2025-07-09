    def show_next_line(self):
        """코드 블록 채우기"""
        if not hasattr(self, 'code_blocks') or self.current_code_index >= len(self.code_blocks):
            self.typing_timer.stop()
            self.is_typing = False
            return
            
        start, end, code_content = self.code_blocks[self.current_code_index]
        code_lines = code_content.strip().split('\n')
        
        code_block_id = f"code_block_{self.current_code_index}"
        
        if not hasattr(self, 'current_code_line'):
            self.current_code_line = 0
            
        if self.current_code_line < len(code_lines):
            line = code_lines[self.current_code_line]
            escaped_line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace(' ', '&nbsp;')
            
            line_js = f"""
            var codeBlock = document.getElementById('{code_block_id}');
            if (codeBlock) {{
                var lineDiv = document.createElement('div');
                lineDiv.innerHTML = '{escaped_line}';
                codeBlock.appendChild(lineDiv);
                window.scrollTo(0, document.body.scrollHeight);
            }}
            """
            
            self.chat_display.page().runJavaScript(line_js)
            self.current_code_line += 1
        else:
            self.current_code_index += 1
            self.current_code_line = 0