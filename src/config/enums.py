"""
Shared enums for consistent data across the application
Enum chung để đảm bảo tính nhất quán dữ liệu trong toàn bộ ứng dụng
"""

from enum import Enum


class SubjectEnum(str, Enum):
    """Enum cho các môn học - sử dụng trong toàn bộ ứng dụng"""
    TOAN = "Toán"
    VAN = "Văn học"
    ANH = "Anh"
    LY = "Vật lý"
    HOA = "Hóa"
    SINH = "Sinh"
    SU = "Sử"
    DIA = "Địa"
    GDCD = "GDCD"
    CONG_NGHE = "Công nghệ"
    GDTC = "GDTC"
    GDQP = "GDQP"

    @classmethod
    def get_values(cls):
        """Trả về list các giá trị để validation"""
        return [item.value for item in cls]

    @classmethod
    def from_string(cls, value: str):
        """Convert string to enum, return None if invalid"""
        for item in cls:
            if item.value.lower() == value.lower():
                return item
        return None


class GradeEnum(str, Enum):
    """Enum cho các lớp học - sử dụng trong toàn bộ ứng dụng"""
    GRADE_10 = "10"
    GRADE_11 = "11" 
    GRADE_12 = "12"

    @classmethod
    def get_values(cls):
        """Trả về list các giá trị để validation"""
        return [item.value for item in cls]

    @classmethod
    def from_string(cls, value: str):
        """Convert string to enum, return None if invalid"""
        for item in cls:
            if item.value == str(value):
                return item
        return None

# Constants để sử dụng trong validation
VALID_SUBJECTS = SubjectEnum.get_values()
VALID_GRADES = GradeEnum.get_values()