from src.domain.shared.exceptions import ConflictError, NotFoundError, PermissionDeniedError


class MeetingNotFoundError(NotFoundError):
    code, message = "meeting_not_found", "Meeting not found"


class MeetingAlreadyActiveError(ConflictError):
    code, message = "meeting_already_active", "This team already has an active meeting"


class MeetingEndedError(ConflictError):
    code, message = "meeting_ended", "The meeting has ended"


class MeetingNotEndedError(ConflictError):
    code, message = "meeting_not_ended", "The meeting has not ended yet"


class NotFacilitatorError(PermissionDeniedError):
    code, message = "not_facilitator", "Only the facilitator can do this"


class SectionConflictError(ConflictError):
    code, message = "section_conflict", "The meeting is no longer in that section"


class NoNextSectionError(ConflictError):
    code, message = "no_next_section", "Conclude is the last section; end the meeting instead"


class RatingNotOpenError(ConflictError):
    code, message = "rating_not_open", "Ratings open in the Conclude section"


class NotAttendeeError(PermissionDeniedError):
    code, message = "not_attendee", "Join the meeting first"
