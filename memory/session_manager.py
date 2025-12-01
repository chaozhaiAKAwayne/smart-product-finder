"""
会话管理器
管理用户会话状态和偏好设置
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path


class SessionManager:
    """会话管理器 - 内存中的会话状态管理"""

    def __init__(self, session_file: str = "logs/sessions.json"):
        self.session_file = Path(session_file)
        self.session_file.parent.mkdir(parents=True, exist_ok=True)
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.current_session_id: Optional[str] = None
        self.logger = logging.getLogger(__name__)
        self.load_sessions()

    def create_session(self, session_id: str, user_preferences: Dict[str, Any] = None) -> str:
        """
        创建新会话

        Args:
            session_id: 会话ID
            user_preferences: 用户偏好设置

        Returns:
            会话ID
        """
        self.sessions[session_id] = {
            'id': session_id,
            'created_at': datetime.now().isoformat(),
            'last_accessed': datetime.now().isoformat(),
            'preferences': user_preferences or {},
            'search_count': 0,
            'state': {}
        }
        self.current_session_id = session_id
        self.logger.info(f"Created session: {session_id}")
        self.save_sessions()
        return session_id

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话"""
        session = self.sessions.get(session_id)
        if session:
            session['last_accessed'] = datetime.now().isoformat()
            self.save_sessions()
        return session

    def update_session_state(self, session_id: str, state: Dict[str, Any]):
        """更新会话状态"""
        if session_id in self.sessions:
            self.sessions[session_id]['state'].update(state)
            self.sessions[session_id]['last_accessed'] = datetime.now().isoformat()
            self.save_sessions()
            self.logger.info(f"Updated session state: {session_id}")

    def increment_search_count(self, session_id: str):
        """增加搜索计数"""
        if session_id in self.sessions:
            self.sessions[session_id]['search_count'] += 1
            self.save_sessions()

    def get_user_preferences(self, session_id: str) -> Dict[str, Any]:
        """获取用户偏好设置"""
        session = self.get_session(session_id)
        return session.get('preferences', {}) if session else {}

    def update_user_preferences(
        self,
        session_id: str,
        preferences: Dict[str, Any]
    ):
        """更新用户偏好设置"""
        if session_id in self.sessions:
            self.sessions[session_id]['preferences'].update(preferences)
            self.save_sessions()
            self.logger.info(f"Updated user preferences: {session_id}")

    def save_sessions(self):
        """保存会话到文件"""
        try:
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(self.sessions, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Failed to save sessions: {str(e)}")

    def load_sessions(self):
        """从文件加载会话"""
        try:
            if self.session_file.exists():
                with open(self.session_file, 'r', encoding='utf-8') as f:
                    self.sessions = json.load(f)
                self.logger.info(f"Loaded {len(self.sessions)} sessions")
        except Exception as e:
            self.logger.error(f"Failed to load sessions: {str(e)}")
            self.sessions = {}

    def get_active_sessions(self) -> Dict[str, Dict[str, Any]]:
        """获取所有活跃会话"""
        return self.sessions

    def delete_session(self, session_id: str):
        """删除会话"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            self.save_sessions()
            self.logger.info(f"Deleted session: {session_id}")
