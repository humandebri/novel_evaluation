from pydantic import BaseSettings

class Settings(BaseSettings):
    # Database Configuration
    db_user: str = "kakuyomu"
    db_password: str = "evaluation"
    db_host: str = "localhost"
    db_port: str = "5433"
    db_name: str = "novel_evaluation"
    db_pool_size: int = 20
    db_max_overflow: int = 5
    
    # LLM Configuration
    llm_api_key: str = ""
    llm_endpoint: str = "https://api.deepseek.com"
    llm_model: str = "deepseek-chat"
    
    # Scraper Configuration
    kakuyomu_base_url: str = "https://kakuyomu.jp"
    scrape_interval: float = 1.0
    max_retries: int = 3
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

settings = Settings()
