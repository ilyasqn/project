"""User domain exceptions."""


class UserNotFoundError(Exception):
    pass


class UserAlreadyExistsError(Exception):
    pass
