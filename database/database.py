import sqlite3
from datetime import datetime, date
from typing import Optional, List, Dict, Any, Tuple

class Database:
    def __init__(self, db_file: str):
        self.connection = sqlite3.connect(db_file)
        self.cursor = self.connection.cursor()
        self._create_tables()

    def _create_tables(self):
        """Создание таблиц с оптимизированной структурой"""
        with self.connection:
            # Таблица пользователей
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL UNIQUE,
                    nickname VARCHAR(60) UNIQUE,
                    birthday DATE,
                    signup VARCHAR(60) DEFAULT 'setnickname',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Таблица встреч
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS meetings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    time TIME NOT NULL,
                    status VARCHAR(60) DEFAULT 'Можно записаться',
                    client_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (client_id) REFERENCES users(id),
                    UNIQUE(date, time)
                )
            """)
            
            # Создаем индексы для оптимизации запросов
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_meetings_date ON meetings(date)")
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_meetings_client ON meetings(client_id)")
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_nickname ON users(nickname)")

    # Методы для работы с пользователями
    def add_user(self, user_id: int) -> None:
        """Добавление нового пользователя"""
        with self.connection:
            self.cursor.execute(
                "INSERT OR IGNORE INTO users (user_id) VALUES (?)",
                (user_id,)
            )

    def user_exists(self, user_id: int) -> bool:
        """Проверка существования пользователя"""
        with self.connection:
            result = self.cursor.execute(
                "SELECT 1 FROM users WHERE user_id = ?",
                (user_id,)
            ).fetchone()
            return bool(result)

    def set_nickname(self, user_id: int, nickname: str) -> None:
        """Установка никнейма пользователя"""
        with self.connection:
            self.cursor.execute(
                "UPDATE users SET nickname = ? WHERE user_id = ?",
                (nickname, user_id)
            )

    def set_birthday(self, user_id: int, birthday: str) -> None:
        """Установка даты рождения пользователя"""
        with self.connection:
            self.cursor.execute(
                "UPDATE users SET birthday = ? WHERE user_id = ?",
                (birthday, user_id)
            )

    def get_user_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получение всей информации о пользователе"""
        with self.connection:
            result = self.cursor.execute(
                "SELECT * FROM users WHERE user_id = ?",
                (user_id,)
            ).fetchone()
            if result:
                return {
                    'id': result[0],
                    'user_id': result[1],
                    'nickname': result[2],
                    'birthday': result[3],
                    'signup': result[4]
                }
            return None

    def get_nickname(self, user_id: int) -> str:
        """Получить никнейм пользователя по его ID"""
        with self.connection:
            self.cursor.execute("SELECT nickname FROM users WHERE user_id = ?", (user_id,))
            result = self.cursor.fetchone()
            return result[0] if result else None

    def get_user_id_by_internal_id(self, internal_user_id: int) -> Optional[int]:
        """Получить Telegram user_id по внутреннему ID пользователя"""
        with self.connection:
            self.cursor.execute("SELECT user_id FROM users WHERE id = ?", (internal_user_id,))
            result = self.cursor.fetchone()
            return result[0] if result else None

    # Методы для работы со встречами
    def create_meeting(self, date: str, time: str) -> int:
        """Создает новую встречу"""
        with self.connection:
            cursor = self.connection.execute(
                'INSERT INTO meetings (date, time, status) VALUES (?, ?, ?)',
                (date, time, 'Можно записаться')
            )
            return cursor.lastrowid

    def get_meeting(self, meeting_id: int) -> Optional[Dict[str, Any]]:
        """Получение информации о встрече"""
        with self.connection:
            result = self.cursor.execute("""
                SELECT m.*, u.nickname 
                FROM meetings m 
                LEFT JOIN users u ON m.client_id = u.id 
                WHERE m.id = ?
            """, (meeting_id,)).fetchone()
            
            if result:
                meeting_data = {
                    'id': result[0],
                    'date': result[1],
                    'time': result[2],
                    'status': result[3],
                    'client_id': result[4],
                    'client_nickname': result[5]
                }
                return meeting_data
            return None

    def get_meetings_by_date(self, date_str: str) -> List[Dict[str, Any]]:
        """Получение всех встреч на определенную дату"""
        with self.connection:
            results = self.cursor.execute(
                """
                SELECT m.id, m.date, m.time, m.status, u.nickname AS client_nickname
                FROM meetings m 
                LEFT JOIN users u ON m.client_id = u.id 
                WHERE m.date = ?
                ORDER BY m.time
                """, (date_str,)).fetchall()
            
            return [{
                'id': row[0],
                'date': row[1],
                'time': row[2],
                'status': row[3],
                'client_nickname': row[4]
            } for row in results]

    def book_meeting(self, meeting_id: int, user_id: int) -> bool:
        """Бронирование встречи пользователем"""
        with self.connection:
            meeting = self.get_meeting(meeting_id)
            if not meeting or meeting['status'] != 'Можно записаться':
                return False
                
            user = self.cursor.execute(
                "SELECT id FROM users WHERE user_id = ?",
                (user_id,)
            ).fetchone()
            
            if not user:
                return False

            self.cursor.execute("""
                UPDATE meetings 
                SET client_id = ?, status = 'Мест нет' 
                WHERE id = ?
            """, (user[0], meeting_id))
            
            return True

    def cancel_meeting(self, meeting_id: int) -> bool:
        """Отмена бронирования встречи"""
        with self.connection:
            self.cursor.execute("""
                UPDATE meetings 
                SET client_id = NULL, status = 'Можно записаться' 
                WHERE id = ?
            """, (meeting_id,))
            return True

    def delete_meeting(self, meeting_id: int) -> bool:
        """Удаление встречи"""
        with self.connection:
            self.cursor.execute(
                "DELETE FROM meetings WHERE id = ?",
                (meeting_id,)
            )
            return self.cursor.rowcount > 0

    def delete_meetings_by_ids(self, meeting_ids: List[int]) -> int:
        """Удаление нескольких встреч по списку ID"""
        if not meeting_ids:
            return 0
        with self.connection:
            placeholders = ', '.join('?' for _ in meeting_ids)
            self.cursor.execute(
                f"DELETE FROM meetings WHERE id IN ({placeholders})",
                meeting_ids
            )
            return self.cursor.rowcount

    def update_meeting_time(self, meeting_id: int, new_time: str) -> bool:
        """Изменение времени встречи"""
        with self.connection:
            self.cursor.execute(
                "UPDATE meetings SET time = ? WHERE id = ?",
                (new_time, meeting_id)
            )
            return self.cursor.rowcount > 0

    def update_meeting_date(self, meeting_id: int, new_date: str) -> bool:
        """Изменение даты встречи"""
        with self.connection:
            self.cursor.execute(
                "UPDATE meetings SET date = ? WHERE id = ?",
                (new_date, meeting_id)
            )
            return self.cursor.rowcount > 0

    def get_user_meetings(self, user_id: int) -> List[Dict[str, Any]]:
        """Получение всех встреч пользователя"""
        with self.connection:
            results = self.cursor.execute(
                """
                SELECT m.* 
                FROM meetings m 
                JOIN users u ON m.client_id = u.id 
                WHERE u.user_id = ?
                ORDER BY m.date, m.time
                """, (user_id,)).fetchall()
            
            return [{
                'id': r[0],
                'date': r[1],
                'time': r[2],
                'status': r[3]
            } for r in results]

    def get_available_meetings(self) -> List[Dict[str, Any]]:
        """Получение всех доступных для записи встреч"""
        with self.connection:
            results = self.cursor.execute(
                """
                SELECT id, date, time, status
                FROM meetings
                WHERE status = 'Можно записаться'
                ORDER BY date, time
                """
            ).fetchall()
            
            return [{
                'id': r[0],
                'date': r[1],
                'time': r[2],
                'status': r[3]
            } for r in results]

    def get_all_meetings(self) -> List[Dict[str, Any]]:
        """Получение всех встреч"""
        with self.connection:
            results = self.cursor.execute(
                """
                SELECT m.id, m.date, m.time, m.status, m.client_id, u.nickname AS client_nickname 
                FROM meetings m 
                LEFT JOIN users u ON m.client_id = u.id
                ORDER BY m.date, m.time
                """
            ).fetchall()
            
            return [{
                'id': row[0],
                'date': row[1],
                'time': row[2],
                'status': row[3],
                'client_id': row[4],
                'client_nickname': row[5]
            } for row in results]

    def get_upcoming_birthdays(self, days: int = 7) -> List[Dict[str, Any]]:
        """Получение предстоящих дней рождения"""
        with self.connection:
            today = date.today()
            results = self.cursor.execute("""
                SELECT id, user_id, nickname, birthday 
                FROM users 
                WHERE birthday IS NOT NULL
            """).fetchall()
            
            upcoming = []
            for user in results:
                if not user[3]:  # Если дата рождения не указана
                    continue
                    
                try:
                    birth_date = datetime.strptime(user[3], '%d.%m.%Y').date()
                    
                    this_year_birth = date(today.year, birth_date.month, birth_date.day)
                    
                    
                    if this_year_birth < today:
                        this_year_birth = date(today.year + 1, birth_date.month, birth_date.day)
                    
                    days_until = (this_year_birth - today).days
                    if 0 <= days_until <= days:
                        upcoming.append({
                            'user_id': user[1],
                            'nickname': user[2],
                            'birthday': user[3],
                            'days_until': days_until,
                            'age': today.year - birth_date.year
                        })
                except ValueError:
                    continue
                    
            return upcoming

    def cleanup_old_meetings(self) -> int:
        """Удаление прошедших встреч"""
        with self.connection:
            today = date.today()
            self.cursor.execute("""
                DELETE FROM meetings 
                WHERE date < ?
            """, (today.strftime('%d.%m.%Y'),))
            return self.cursor.rowcount

    def change_user_nickname(self, new_nickname: str, old_nickname: str) -> bool:
        """Изменение никнейма пользователя"""
        with self.connection:
            try:
                self.cursor.execute(
                    "UPDATE users SET nickname = ? WHERE nickname = ?",
                    (new_nickname, old_nickname)
                )
                return True
            except sqlite3.IntegrityError:
                return False

    def get_meeting_id(self, nickname: str) -> Optional[int]:
        """Получить ID встречи по никнейму пользователя"""
        with self.connection:
            self.cursor.execute("""
                SELECT m.id 
                FROM meetings m 
                JOIN users u ON m.client_id = u.id 
                WHERE u.nickname = ?
            """, (nickname,))
            result = self.cursor.fetchone()
            return result[0] if result else None

    def get_user_info_by_nickname(self, nickname: str) -> Optional[Dict[str, Any]]:
        """Получение информации о пользователе по никнейму"""
        with self.connection:
            result = self.cursor.execute(
                "SELECT * FROM users WHERE nickname = ?",
                (nickname,)
            ).fetchone()
            if result:
                return {
                    'id': result[0],
                    'user_id': result[1],
                    'nickname': result[2],
                    'birthday': result[3],
                    'signup': result[4]
                }
            return None 