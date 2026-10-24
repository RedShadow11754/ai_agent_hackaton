import re

_URL_RE = re.compile(
    r"(?:hxxps?|https?|ftp)://[^\s<>\"'{}]+",
    re.IGNORECASE,
)

message = """Dear user,

Your account password expires today. You must reset it immediately or lose access to email and payroll.

Reset now: hxxps://secure-login[.]test/portal/reset?user=analyst

Thank you,
IT Support"""

for m in _URL_RE.finditer(message):
    print(f"Match: {m.group(0)!r}")