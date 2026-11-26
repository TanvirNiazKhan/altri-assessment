from src.domain.shared.exceptions import BusinessRuleViolationError, NotFoundError


class MeasurableNotFoundError(NotFoundError):
    code, message = "measurable_not_found", "Measurable not found"


class InvalidWeekError(BusinessRuleViolationError):
    code, message = (
        "invalid_week",
        "Week must be a Monday within the scorecard window, not in the future",
    )


class NotOffTrackError(BusinessRuleViolationError):
    code, message = "not_off_track", "Only an off-track score can be made into an Issue"
