const ACCESS = "access_token";
const REFRESH = "refresh_token";

export const auth = {
  getAccess: () => (typeof window !== "undefined" ? localStorage.getItem(ACCESS) : null),
  set: (access: string, refresh: string) => {
    localStorage.setItem(ACCESS, access);
    localStorage.setItem(REFRESH, refresh);
  },
  clear: () => {
    localStorage.removeItem(ACCESS);
    localStorage.removeItem(REFRESH);
  },
  isAuthed: () => typeof window !== "undefined" && !!localStorage.getItem(ACCESS),
};
