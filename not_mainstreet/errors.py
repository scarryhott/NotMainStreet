class NotMainStreetError(Exception):
    """Base error for integration pipeline."""


class ValidationError(NotMainStreetError):
    pass


class ContinuityViolation(NotMainStreetError):
    pass


class UnsupportedIntegrationMode(NotMainStreetError):
    pass
