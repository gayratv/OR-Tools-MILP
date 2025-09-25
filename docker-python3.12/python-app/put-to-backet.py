import boto3
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Глобальная переменная для кэширования S3 клиента (Singleton pattern)
_s3_client = None

def get_s3_client():
    """
    Фабрика для S3 клиента с ленивой инициализацией и проверкой конфигурации.
    Создает клиент только при первом вызове и кэширует его.
    """
    global _s3_client
    if _s3_client:
        return _s3_client

    # Конфигурация считывается здесь, в момент первого запроса клиента
    ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL")
    REGION_NAME = os.getenv("S3_REGION_NAME")
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

    if not all([ENDPOINT_URL, REGION_NAME, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY]):
        raise ValueError("Необходимые переменные окружения для S3 не настроены.")

    try:
        session = boto3.session.Session()
        _s3_client = session.client(
            service_name='s3',
            endpoint_url=ENDPOINT_URL,
            region_name=REGION_NAME,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        print("S3 клиент успешно инициализирован.")
        return _s3_client
    except Exception as e:
        print(f"Ошибка при инициализации S3 клиента: {e}", file=sys.stderr)
        # Выбрасываем исключение, чтобы вызывающий код мог его обработать
        raise

def upload_file_to_s3(local_file_path: Path, s3_object_key: str = None) -> bool:
    """
    Загружает локальный файл в S3 бакет.

    Args:
        local_file_path (Path): Путь к файлу, который нужно загрузить (объект pathlib.Path).
        s3_object_key (str, optional): Имя объекта в S3 бакете. Если не указано,
                                       используется базовое имя локального файла.
                                       По умолчанию None.

    Returns:
        bool: True, если загрузка прошла успешно, False в противном случае.
    """
    try:
        s3_client = get_s3_client()
        BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
        if not BUCKET_NAME:
            raise ValueError("Переменная окружения S3_BUCKET_NAME не задана.")
    except (ValueError, Exception) as e:
        print(f"Не удалось подготовиться к загрузке: {e}", file=sys.stderr)
        return False

    # Определяем имя объекта в S3, если оно не было явно указано
    if s3_object_key is None:
        s3_object_key = local_file_path.name

    print(f"Начинается загрузка файла '{local_file_path}' в бакет '{BUCKET_NAME}' как '{s3_object_key}'...")
    try:
        # upload_file принимает строковый путь, поэтому преобразуем Path в str
        s3_client.upload_file(str(local_file_path), BUCKET_NAME, s3_object_key)
        print(f"Файл '{local_file_path}' успешно загружен в S3 как '{s3_object_key}'.")
        return True
    except FileNotFoundError:
        print(f"Файл не найден по пути: {local_file_path}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Ошибка при загрузке файла '{local_file_path}' в S3: {e}", file=sys.stderr)
        return False

if __name__ == "__main__":
    # При прямом запуске, мы сами отвечаем за загрузку .env
    dotenv_path = Path(__file__).parent / 'responce/.env'
    load_dotenv(dotenv_path=dotenv_path)

    try:
        # Пример использования функции: загрузка самого себя
        current_script_path = Path(__file__).resolve()
        # Можно указать другое имя для объекта в S3, например 'my_script_uploaded.py'
        # или оставить None, чтобы использовалось 'put-to-backet.py'
        success = upload_file_to_s3(current_script_path, 'user2/test-backet_function.py')

        if success:
            print("Пример загрузки завершен успешно.")
        else:
            print("Пример загрузки завершен с ошибкой.", file=sys.stderr)

        # Пример загрузки несуществующего файла
        print("\nПопытка загрузки несуществующего файла:")
        upload_file_to_s3(Path("non_existent_file.txt"))
    except Exception as e:
        # Эта ошибка поймает проблемы с инициализацией клиента, если они возникнут
        print(f"КРИТИЧЕСКАЯ ОШИБКА: Выполнение скрипта прервано из-за: {e}", file=sys.stderr)
        sys.exit(1)
