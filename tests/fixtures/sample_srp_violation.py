"""Sample Python file with SOLID violations (used in tests)."""

# ---- SRP violation: class does too many things ----
class GodClass:
    def create_user(self): pass
    def delete_user(self): pass
    def send_email(self): pass
    def generate_report(self): pass
    def export_csv(self): pass
    def calculate_tax(self): pass
    def process_payment(self): pass
    def log_activity(self): pass
    def validate_input(self): pass
    def compress_image(self): pass
    def resize_image(self): pass  # 11th public method – triggers SRP001


# ---- OCP violation: isinstance checks ----
class ShapeRenderer:
    def render(self, shape):
        if isinstance(shape, int):
            print("circle")
        elif isinstance(shape, str):
            print("rectangle")
        elif isinstance(shape, float):
            print("triangle")
        else:
            pass


# ---- LSP violation: NotImplementedError without ABC ----
class BaseWorker:
    def work(self):
        raise NotImplementedError("subclasses must implement work()")


# ---- ISP violation: fat interface ----
from abc import ABC, abstractmethod

class FatInterface(ABC):
    @abstractmethod
    def method_a(self): ...
    @abstractmethod
    def method_b(self): ...
    @abstractmethod
    def method_c(self): ...
    @abstractmethod
    def method_d(self): ...
    @abstractmethod
    def method_e(self): ...
    @abstractmethod
    def method_f(self): ...
    @abstractmethod
    def method_g(self): ...
    @abstractmethod
    def method_h(self): ...  # 8 abstract methods – triggers ISP001


# ---- DIP violation: direct concrete instantiation ----
class DatabaseRepository:
    pass


class UserService:
    def get_user(self, user_id):
        repo = DatabaseRepository()  # DIP violation
        return repo
