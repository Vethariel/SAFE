def is_enough_length(password):
    return len(password) >= 8

def has_uppercase(password):
    return any(c.isupper() for c in password)

def has_lowercase(password):
    return any(c.islower() for c in password)

def has_digit(password):
    return any(c.isdigit() for c in password)

def has_no_spaces(password):
    return " " not in password

def is_valid_password(password):
    return (
        is_enough_length(password)
        and has_uppercase(password)
        and has_lowercase(password)
        and has_digit(password)
        and has_no_spaces(password)
    )