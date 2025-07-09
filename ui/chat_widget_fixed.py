    def show_next_line(self):
        """다음 줄 표시"""
        if self.current_line_index >= len(self.typing_lines):
            self.typing_timer.stop()
            self.is_typing = False
            return
            
        line = self.typing_lines[self.current_line_index]
        formatted_line = self.format_text(line)
        
        # 현재 메시지 컨테이너에 줄 추가
        line_js = f"""
        var contentDiv = document.getElementById('{self.current_message_id}_content');
        var lineDiv = document.createElement('div');
        lineDiv.innerHTML = `{formatted_line.replace('`', '\\`').replace('${', '\\${')}` + '<br>';
        contentDiv.appendChild(lineDiv);
        window.scrollTo(0, document.body.scrollHeight);
        """
        
        self.chat_display.page().runJavaScript(line_js)
        self.current_line_index += 1