from dataclasses import dataclass, field


@dataclass
class BrowserConfig:
    headless: bool = True
    timeout_ms: int = 30000
    user_agents: list[str] = field(
        default_factory=lambda: [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
    )


@dataclass
class RetryConfig:
    max_attempts: int = 3
    backoff_base_sec: int = 2


@dataclass
class CacheConfig:
    ttl_sec: int = 3600
    max_size: int = 1000


@dataclass
class ExportConfig:
    formats: list[str] = field(default_factory=lambda: ["json", "csv", "excel"])
    output_dir: str = "output"


@dataclass
class LogConfig:
    level: str = "INFO"
    rotation_size_mb: int = 10
    rotation_count: int = 5
    log_dir: str = "logs"


@dataclass
class MonitorConfig:
    metrics_interval_sec: int = 5


@dataclass
class SecurityConfig:
    allowed_domains: list[str] = field(default_factory=list)
    enforce_robots_txt: bool = True


@dataclass
class FeatureFlags:
    ENABLE_CACHE: bool = True
    ENABLE_HEADLESS: bool = True
    ENABLE_LOG: bool = True
    ENABLE_METRIC: bool = True
    ENABLE_EXPORT: bool = True


@dataclass
class AppConfig:
    browser: BrowserConfig = field(default_factory=BrowserConfig)
    retry: RetryConfig = field(default_factory=RetryConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    export: ExportConfig = field(default_factory=ExportConfig)
    log: LogConfig = field(default_factory=LogConfig)
    monitor: MonitorConfig = field(default_factory=MonitorConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    features: FeatureFlags = field(default_factory=FeatureFlags)

    def __post_init__(self) -> None:
        if not self.features.ENABLE_HEADLESS:
            self.browser.headless = False


config = AppConfig()
