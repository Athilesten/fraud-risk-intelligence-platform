ROLE_PERMISSIONS = {
    "admin": [
        "predict",
        "batch_predict",
        "read_logs",
        "read_monitoring",
        "read_streaming",
        "read_datalake",
        "manage_system",
    ],
    "risk_analyst": [
        "predict",
        "batch_predict",
        "read_logs",
        "read_monitoring",
    ],
    "data_engineer": [
        "read_monitoring",
        "read_streaming",
        "read_datalake",
    ],
    "viewer": [
        "read_logs",
        "read_monitoring",
    ],
    "service": [
        "predict",
        "batch_predict",
        "read_logs",
        "read_monitoring",
        "read_streaming",
        "read_datalake",
        "manage_system",
    ],
}


def normalize_role(role):
    return str(role or "viewer").strip().lower()


def role_has_permission(role, permission):
    return permission in ROLE_PERMISSIONS.get(normalize_role(role), [])


def role_summary(role):
    normalized_role = normalize_role(role)
    return {
        "role": normalized_role,
        "permissions": ROLE_PERMISSIONS.get(normalized_role, []),
    }
