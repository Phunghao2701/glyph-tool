import i18next, { type InitOptions } from "i18next";
import { initReactI18next } from "react-i18next";
import { resources } from "./resources";

const STORAGE_KEY = "vfk-language";

function storedLanguage(): "vi" | "en" {
  try {
    return localStorage.getItem(STORAGE_KEY) === "en" ? "en" : "vi";
  } catch {
    return "vi";
  }
}

void i18next
  .use(initReactI18next)
  .init({
    resources: resources as unknown as InitOptions["resources"],
    lng: storedLanguage(),
    fallbackLng: "vi",
    supportedLngs: ["vi", "en"],
    defaultNS: "translation",
    interpolation: { escapeValue: false },
    react: { useSuspense: false },
  });

function syncLanguage(language: string) {
  const locale = language.startsWith("en") ? "en" : "vi";
  document.documentElement.lang = locale;
  try {
    localStorage.setItem(STORAGE_KEY, locale);
  } catch {
    // The app still works when browser storage is unavailable.
  }
}

i18next.on("languageChanged", syncLanguage);
syncLanguage(i18next.language || "vi");

export default i18next;
