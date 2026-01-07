class SmartValve:
    def __init__(self):
        self.served = False
        self.request_count = 0

    def check(self, force: bool) -> tuple[bool, str]:
        """
        요청을 허용할지 결정합니다.
        Returns: (is_allowed, reason_message)
        """
        if self.served and not force:
            self.request_count += 1
            msg = (
                f"🛑 [MCP Vault] Context Blocked (Attempt #{self.request_count}).\n"
                "You already have the context map. Do not request it again.\n"
                "Use 'read_file' for specific details."
            )
            return False, msg
        
        self.served = True
        return True, ""

# 싱글톤 인스턴스
valve = SmartValve()