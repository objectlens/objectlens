from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from ..auth import User, get_current_user, require_role
from ..config import get_settings
from ..models import (
    ProviderCapabilityCheck,
    ProviderResponse,
    ProviderSettingsResponse,
    ProviderStatusResponse,
)
from ..providers import get_provider, get_provider_registry
from ..providers.types import ProviderConnectionPublic

router = APIRouter(tags=["provider"])


@router.get("/providers", response_model=list[ProviderConnectionPublic])
def list_providers(
    current_user: Annotated[User, Depends(get_current_user)] = None,
) -> list[ProviderConnectionPublic]:
    return get_provider_registry().list_connections()


@router.post("/providers/reload", response_model=list[ProviderConnectionPublic])
def reload_providers(
    current_user: Annotated[User, Depends(require_role("admin"))] = None,
) -> list[ProviderConnectionPublic]:
    registry = get_provider_registry()
    registry._load_all()
    return registry.list_connections()


@router.get("/providers/{provider_id}", response_model=ProviderConnectionPublic)
def provider_connection(provider_id: str) -> ProviderConnectionPublic:
    registry = get_provider_registry()
    try:
        connection = registry.get_connection(provider_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Provider connection not found.") from exc
    return registry.public_connection(connection)


@router.get("/providers/{provider_id}/status", response_model=ProviderStatusResponse)
def provider_status(provider_id: str, run: str | None = None) -> ProviderStatusResponse:
    import io
    import time

    registry = get_provider_registry()
    capabilities = []

    # 0. Handle Unverified/Not Run state (no 'run' parameter provided on page load)
    if not run:
        capabilities.append(
            ProviderCapabilityCheck(
                name="Endpoint Connection",
                status="not_run",
                message="Not run yet. Click 'Verify Connection' or 'Run Full Capability Audit'.",
            )
        )
        capabilities.append(
            ProviderCapabilityCheck(
                name="List Buckets (s3:ListAllMyBuckets)",
                status="not_run",
                message="Not run yet. Click 'Verify Connection' or 'Run Full Capability Audit'.",
            )
        )
        capabilities.append(
            ProviderCapabilityCheck(
                name="List Objects (s3:ListBucket)",
                status="not_run",
                message="Not run yet. Click 'Run Full Capability Audit' to verify.",
            )
        )
        capabilities.append(
            ProviderCapabilityCheck(
                name="Upload Object (s3:PutObject)",
                status="not_run",
                message="Not run yet. Click 'Run Full Capability Audit' to verify.",
            )
        )
        capabilities.append(
            ProviderCapabilityCheck(
                name="Delete Object (s3:DeleteObject)",
                status="not_run",
                message="Not run yet. Click 'Run Full Capability Audit' to verify.",
            )
        )
        return ProviderStatusResponse(
            provider_id=provider_id,
            status="healthy",
            can_list_buckets=True,
            visible_bucket_count=0,
            message="Status: Unverified (Diagnostics not run yet)",
            capabilities=capabilities,
        )

    # 1. Connection & Initialization
    try:
        provider = registry.get(provider_id)
        endpoint_url = provider.endpoint_url or "AWS S3 Edge"
        capabilities.append(
            ProviderCapabilityCheck(
                name="Endpoint Connection",
                status="healthy",
                message=f"S3 client initialized successfully for endpoint: {endpoint_url}",
            )
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Provider connection not found.") from exc
    except Exception as exc:
        capabilities.append(
            ProviderCapabilityCheck(
                name="Endpoint Connection", status="unhealthy", message=str(exc)
            )
        )
        capabilities.append(
            ProviderCapabilityCheck(
                name="List Buckets (s3:ListAllMyBuckets)",
                status="skipped",
                message="Skipped: Client connection failed",
            )
        )
        capabilities.append(
            ProviderCapabilityCheck(
                name="List Objects (s3:ListBucket)",
                status="skipped",
                message="Skipped: Client connection failed",
            )
        )
        capabilities.append(
            ProviderCapabilityCheck(
                name="Upload Object (s3:PutObject)",
                status="skipped",
                message="Skipped: Client connection failed",
            )
        )
        capabilities.append(
            ProviderCapabilityCheck(
                name="Delete Object (s3:DeleteObject)",
                status="skipped",
                message="Skipped: Client connection failed",
            )
        )
        return ProviderStatusResponse(
            provider_id=provider_id,
            status="unhealthy",
            can_list_buckets=False,
            visible_bucket_count=0,
            message="Client connection failed",
            capabilities=capabilities,
        )

    # 2. List Buckets Check
    buckets = []
    try:
        buckets = provider.list_buckets()
        capabilities.append(
            ProviderCapabilityCheck(
                name="List Buckets (s3:ListAllMyBuckets)",
                status="healthy",
                message=f"Discovered {len(buckets)} accessible buckets",
            )
        )
    except Exception as exc:
        capabilities.append(
            ProviderCapabilityCheck(
                name="List Buckets (s3:ListAllMyBuckets)", status="unhealthy", message=str(exc)
            )
        )
        capabilities.append(
            ProviderCapabilityCheck(
                name="List Objects (s3:ListBucket)",
                status="skipped",
                message="Skipped: List Buckets failed",
            )
        )
        capabilities.append(
            ProviderCapabilityCheck(
                name="Upload Object (s3:PutObject)",
                status="skipped",
                message="Skipped: List Buckets failed",
            )
        )
        capabilities.append(
            ProviderCapabilityCheck(
                name="Delete Object (s3:DeleteObject)",
                status="skipped",
                message="Skipped: List Buckets failed",
            )
        )
        return ProviderStatusResponse(
            provider_id=provider_id,
            status="unhealthy",
            can_list_buckets=False,
            visible_bucket_count=0,
            message=str(exc),
            capabilities=capabilities,
        )

    # Early return if simple check requested
    if run == "simple":
        capabilities.append(
            ProviderCapabilityCheck(
                name="List Objects (s3:ListBucket)",
                status="skipped",
                message="Skipped: Run full capability audit to verify",
            )
        )
        capabilities.append(
            ProviderCapabilityCheck(
                name="Upload Object (s3:PutObject)",
                status="skipped",
                message="Skipped: Run full capability audit to verify",
            )
        )
        capabilities.append(
            ProviderCapabilityCheck(
                name="Delete Object (s3:DeleteObject)",
                status="skipped",
                message="Skipped: Run full capability audit to verify",
            )
        )
        return ProviderStatusResponse(
            provider_id=provider_id,
            status="healthy",
            can_list_buckets=True,
            visible_bucket_count=len(buckets),
            message="Connected (basic connection check passed)",
            capabilities=capabilities,
        )

    # Target bucket selection for object-level checks (only when run == "deep")
    target_bucket = None
    if provider.default_bucket:
        target_bucket = provider.default_bucket
    elif buckets:
        target_bucket = buckets[0].name

    if not target_bucket:
        capabilities.append(
            ProviderCapabilityCheck(
                name="List Objects (s3:ListBucket)",
                status="skipped",
                message="No buckets found to perform validation",
            )
        )
        capabilities.append(
            ProviderCapabilityCheck(
                name="Upload Object (s3:PutObject)",
                status="skipped",
                message="No buckets found to perform validation",
            )
        )
        capabilities.append(
            ProviderCapabilityCheck(
                name="Delete Object (s3:DeleteObject)",
                status="skipped",
                message="No buckets found to perform validation",
            )
        )
        return ProviderStatusResponse(
            provider_id=provider_id,
            status="healthy",
            can_list_buckets=True,
            visible_bucket_count=len(buckets),
            message="Connected (no buckets available for diagnostics)",
            capabilities=capabilities,
        )

    # 3. List Objects Check
    try:
        provider.list_objects(bucket=target_bucket, limit=1)
        capabilities.append(
            ProviderCapabilityCheck(
                name="List Objects (s3:ListBucket)",
                status="healthy",
                message=f"Successfully queried objects in bucket: {target_bucket}",
            )
        )
    except Exception as exc:
        capabilities.append(
            ProviderCapabilityCheck(
                name="List Objects (s3:ListBucket)",
                status="unhealthy",
                message=f"Bucket {target_bucket}: {exc}",
            )
        )

    # 4. Upload Object Check
    test_key = f".objectlens_health_check_{int(time.time())}.txt"
    upload_ok = False
    try:
        provider.upload_object(
            bucket=target_bucket,
            key=test_key,
            file_obj=io.BytesIO(b"objectlens health check content"),
            content_type="text/plain",
        )
        capabilities.append(
            ProviderCapabilityCheck(
                name="Upload Object (s3:PutObject)",
                status="healthy",
                message=f"Successfully uploaded test file in bucket: {target_bucket}",
            )
        )
        upload_ok = True
    except Exception as exc:
        capabilities.append(
            ProviderCapabilityCheck(
                name="Upload Object (s3:PutObject)",
                status="unhealthy",
                message=f"Bucket {target_bucket}: {exc}",
            )
        )

    # 5. Delete Object Check
    if upload_ok:
        try:
            provider.delete_object(bucket=target_bucket, key=test_key)
            capabilities.append(
                ProviderCapabilityCheck(
                    name="Delete Object (s3:DeleteObject)",
                    status="healthy",
                    message=f"Successfully cleaned up test file in bucket: {target_bucket}",
                )
            )
        except Exception as exc:
            capabilities.append(
                ProviderCapabilityCheck(
                    name="Delete Object (s3:DeleteObject)",
                    status="unhealthy",
                    message=f"Bucket {target_bucket}: {exc}",
                )
            )
    else:
        capabilities.append(
            ProviderCapabilityCheck(
                name="Delete Object (s3:DeleteObject)",
                status="skipped",
                message="Skipped: Upload test failed",
            )
        )

    failed_checks = [c.name for c in capabilities if c.status == "unhealthy"]
    if failed_checks:
        overall_msg = f"Connected but has permission issues: {', '.join(failed_checks)}"
    else:
        overall_msg = "All checks passed successfully"

    return ProviderStatusResponse(
        provider_id=provider_id,
        status="healthy",
        can_list_buckets=True,
        visible_bucket_count=len(buckets),
        message=overall_msg,
        capabilities=capabilities,
    )


@router.get("/providers/{provider_id}/settings", response_model=ProviderSettingsResponse)
def provider_settings(provider_id: str) -> ProviderSettingsResponse:
    registry = get_provider_registry()
    try:
        connection = registry.get_connection(provider_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Provider connection not found.") from exc
    return ProviderSettingsResponse(
        provider_id=provider_id,
        config_source=registry.config_source,
        secrets_loaded=bool(connection.access_key_id and connection.secret_access_key),
        secret_fields=["access_key_id", "secret_access_key"],
        editable=False,
    )


@router.get("/provider", response_model=ProviderResponse)
def provider_info() -> ProviderResponse:
    try:
        provider = get_provider(get_settings())
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return ProviderResponse(
        id=getattr(provider, "connection_id", provider.provider),
        name=getattr(provider, "connection_name", provider.display_name),
        type=provider.provider,
        provider=provider.provider,
        display_name=provider.display_name,
        endpoint_url=provider.endpoint_url,
        region=None,
        default_bucket=provider.default_bucket,
    )
