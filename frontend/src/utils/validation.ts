// Client-side mirrors of the backend Pydantic validators (see user_schema.py)
// so users get immediate feedback instead of a 422 round-trip.

export const USERNAME_PATTERN = /^[a-zA-Z0-9_.-]+$/;
const SPECIAL_CHARACTERS = "@#_!$%*.-";
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export const PASSWORD_RULES_HINT =
  "Min 8 characters, with an uppercase, lowercase, digit and one of @ # _ ! $ % * . -";

export function validateEmail(email: string): string | null {
  if (!email.trim()) return "Email is required";
  if (!EMAIL_PATTERN.test(email.trim())) return "Enter a valid email address";
  return null;
}

export function validateUserName(userName: string): string | null {
  if (!userName.trim()) return "Username is required";
  if (userName.length < 3 || userName.length > 200) {
    return "Username must be between 3 and 200 characters";
  }
  if (!USERNAME_PATTERN.test(userName)) {
    return "Only letters, numbers and _ . - are allowed";
  }
  return null;
}

export function validateName(name: string): string | null {
  const trimmed = name.trim();
  if (trimmed.length < 2 || trimmed.length > 100) {
    return "Name must be between 2 and 100 characters";
  }
  return null;
}



export function validateNewPassword(password: string): string | null {
  if (password.length < 8 || password.length > 128) {
    return "Password must be between 8 and 128 characters";
  }
  if (!/[A-Z]/.test(password)) return "Add at least one uppercase character";
  if (!/[a-z]/.test(password)) return "Add at least one lowercase character";
  if (!/[0-9]/.test(password)) return "Add at least one digit";
  if (![...SPECIAL_CHARACTERS].some((char) => password.includes(char))) {
    return "Add at least one special character ( @ # _ ! $ % * . - )";
  }
  const allowed = /^[A-Za-z0-9@#_!$%*.-]+$/;
  if (!allowed.test(password)) {
    return "Only letters, numbers and @ # _ ! $ % * . - are allowed";
  }
  return null;
}

export function validateOtp(otp: string): string | null {
  if (!/^[0-9]{6}$/.test(otp)) return "Enter the 6-digit code";
  return null;
}
