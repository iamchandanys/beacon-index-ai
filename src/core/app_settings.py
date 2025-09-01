# This import should always remain at the very top
from __future__ import annotations

import os
import threading
import time

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Dict, Iterable, Optional
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.core.pipeline.policies import RetryPolicy
from azure.core.exceptions import ResourceNotFoundError, HttpResponseError
from dotenv import load_dotenv

load_dotenv()

# ---------- Configuration ----------

# 1) Configure which secrets you expect (single source of truth).
# Keys in this dict are your internal names; values are Key Vault secret names.
REQUIRED_SECRETS: Dict[str, str] = {
    # Azure OpenAI
    "AZURE_OPENAI_API_KEY": "AZURE-OPENAI-API-KEY",
    "AZURE_OPENAI_ENDPOINT": "AZURE-OPENAI-ENDPOINT",
    "AZURE_OPENAI_GPT_4O_MODEL": "AZURE-OPENAI-GPT-4O-MODEL",
    "AZURE_OPENAI_GPT_4O_FULL_ENDPOINT": "AZURE-OPENAI-GPT-4O-FULL-ENDPOINT",
    # Content Safety
    "AZURE_CONTENT_SAFETY_ENDPOINT": "AZURE-CONTENT-SAFETY-ENDPOINT",
    "AZURE_CONTENT_SAFETY_KEY": "AZURE-CONTENT-SAFETY-KEY",
    # Storage / Monitor
    "AZURE_STORAGE_CONN_STR": "AZURE-STORAGE-CONN-STR",
    "AZURE_MONITOR_CONN_STR": "AZURE-MONITOR-CONN-STR",
    # Cosmos
    "AZ_EMC_COSMOS_DB_CONNECTION_STRING": "AZ-EMC-COSMOS-DB-CONNECTION-STRING",
    "AZ_EMC_COSMOS_DB_SITES_DATABASE_NAME": "AZ-EMC-COSMOS-DB-SITES-DATABASE-NAME",
    "AZ_EMC_COSMOS_DB_CHAT_HISTORY_CONTAINER_NAME": "AZ-EMC-COSMOS-DB-CHAT-HISTORY-CONTAINER-NAME",
    "DEEPEVAL_API_KEY": "DEEPEVAL-API-KEY"
}

# 2) Key Vault config via env (works in local/dev and in cloud)
KEY_VAULT_URL = os.environ.get("KEY_VAULT_URL", "https://emc-dev-key-vault-v2.vault.azure.net/").strip()

# 3) Cache behavior
DEFAULT_TTL_SECONDS = int(os.environ.get("SETTINGS_CACHE_TTL_SECONDS", "0"))  # 0 means never auto‑expire (default). Set to e.g. 3600 for 1‑hour TTL
PARALLEL_FETCH_WORKERS = int(os.environ.get("SETTINGS_PARALLELISM", "8")) # number of threads when fetching secrets in parallel (default 8)

# ---------- Data Model ----------

@dataclass(frozen=True)
class Settings:
    # Mirror the keys you actually use in code (intentionally explicit)
    AZURE_OPENAI_API_KEY: str
    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_GPT_4O_MODEL: str
    AZURE_OPENAI_GPT_4O_FULL_ENDPOINT: str
    AZURE_CONTENT_SAFETY_ENDPOINT: str
    AZURE_CONTENT_SAFETY_KEY: str
    AZURE_STORAGE_CONN_STR: str
    AZURE_MONITOR_CONN_STR: str
    AZ_EMC_COSMOS_DB_CONNECTION_STRING: str
    AZ_EMC_COSMOS_DB_SITES_DATABASE_NAME: str
    AZ_EMC_COSMOS_DB_CHAT_HISTORY_CONTAINER_NAME: str
    DEEPEVAL_API_KEY: str

# ---------- Internal Singleton State ----------

class _SettingsProvider:
    """
    Thread-safe provider that:
      - builds a single SecretClient with sane retries
      - fetches all required secrets in parallel once
      - caches results with optional TTL
      - supports env var overrides
    """
    _instance: Optional["_SettingsProvider"] = None
    _instance_lock = threading.Lock()

    def __init__(self):
        self._lock = threading.RLock()
        self._client = self._create_secret_client() if KEY_VAULT_URL else None
        self._cached: Optional[Settings] = None
        self._expires_at: float = 0.0

    @classmethod
    def instance(cls) -> "_SettingsProvider":
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = _SettingsProvider()
        return cls._instance

    def get_settings(self) -> Settings:
        # Fast path: return cached if valid
        if self._cached and (DEFAULT_TTL_SECONDS == 0 or time.time() < self._expires_at):
            return self._cached

        # Slow path: refresh
        with self._lock:
            if self._cached and (DEFAULT_TTL_SECONDS == 0 or time.time() < self._expires_at):
                return self._cached  # double-checked locking

            values = self._load_all()
            self._cached = Settings(**values)
            self._expires_at = time.time() + DEFAULT_TTL_SECONDS if DEFAULT_TTL_SECONDS > 0 else float("inf")
            return self._cached

    def refresh(self) -> Settings:
        """Force a refetch from Key Vault (ignores TTL)."""
        with self._lock:
            values = self._load_all(force=True)
            self._cached = Settings(**values)
            self._expires_at = time.time() + DEFAULT_TTL_SECONDS if DEFAULT_TTL_SECONDS > 0 else float("inf")
            return self._cached

    # ----- helpers -----

    def _create_secret_client(self) -> Optional[SecretClient]:
        """
        Build a SecretClient with robust retry policy.
        In Azure, DefaultAzureCredential will use Managed Identity if available.
        """
        if not KEY_VAULT_URL:
            return None

        # Prefer DefaultAzureCredential (covers Managed Identity, Workload Identity, etc.)
        credential = DefaultAzureCredential(exclude_shared_token_cache_credential=True)

        retry_policy = RetryPolicy(
            # 429/5xx handling + exponential backoff
            retry_total=8,
            retry_backoff_factor=0.8,
            retry_on_status_codes=[409, 429, 500, 502, 503, 504],
        )
        return SecretClient(vault_url=KEY_VAULT_URL, credential=credential, retry_policy=retry_policy)

    def _load_all(self, force: bool = False) -> Dict[str, str]:
        """
        Merge strategy:
          1. Env var overrides (always win)
          2. Otherwise, Key Vault values (fetched once, in parallel)
        """
        values: Dict[str, str] = {}

        # 1) Apply env overrides first
        for key in REQUIRED_SECRETS.keys():
            env_val = os.environ.get(key)
            if env_val is not None and env_val != "":
                values[key] = env_val

        # 2) Fetch missing values from Key Vault (if configured)
        missing = [k for k in REQUIRED_SECRETS.keys() if k not in values]

        if missing:
            if not self._client:
                missing_str = ", ".join(missing)
                raise RuntimeError(
                    f"KEY_VAULT_URL is not configured but the following settings are missing "
                    f"from environment: {missing_str}"
                )

            kv_names = {k: REQUIRED_SECRETS[k] for k in missing}
            fetched = self._get_secrets_parallel(kv_names.values())

            # Map back to our internal keys
            for internal_key, kv_secret_name in kv_names.items():
                if kv_secret_name not in fetched or fetched[kv_secret_name] in (None, ""):
                    raise RuntimeError(
                        f"Required secret '{kv_secret_name}' for '{internal_key}' was not found or empty in Key Vault."
                    )
                values[internal_key] = fetched[kv_secret_name]

        # 3) Final guard: all required values present
        absent = [k for k in REQUIRED_SECRETS.keys() if k not in values or values[k] in (None, "")]
        if absent:
            raise RuntimeError(f"Missing required settings: {', '.join(absent)}")

        return values

    def _get_secrets_parallel(self, secret_names: Iterable[str]) -> Dict[str, str]:
        """
        Fetch secrets concurrently to minimize cold-start latency.
        Each secret is fetched once; failures raise a clear error.
        """
        results: Dict[str, str] = {}

        def _fetch_one(name: str) -> None:
            try:
                secret = self._client.get_secret(name)  # single network call
                results[name] = secret.value
            except ResourceNotFoundError:
                results[name] = None  # handled by caller with clearer error
            except HttpResponseError as e:
                raise RuntimeError(f"Key Vault error fetching '{name}': {e.message}") from e
            except Exception as e:
                raise RuntimeError(f"Unexpected error fetching '{name}': {e}") from e

        with ThreadPoolExecutor(max_workers=max(PARALLEL_FETCH_WORKERS, 1)) as pool:
            futures = {pool.submit(_fetch_one, n): n for n in secret_names}
            for future in as_completed(futures):
                # propagate the first exception immediately
                _ = future.result()

        return results

# ---------- Public API ----------

def get_settings() -> Settings:
    """
    Returns an immutable Settings object from cache.
    - First call: loads all secrets (env overrides win), caches result
    - Subsequent calls: O(1) with no Key Vault round-trips (until TTL expiry)
    """
    return _SettingsProvider.instance().get_settings()

def refresh_settings() -> Settings:
    """
    Forces a fresh read from Key Vault ignoring TTL.
    Useful after you rotate secrets or during a health probe endpoint.
    """
    return _SettingsProvider.instance().refresh()

# ---------- Testing ----------
if __name__ == "__main__":
    settings = get_settings()
    print(settings)