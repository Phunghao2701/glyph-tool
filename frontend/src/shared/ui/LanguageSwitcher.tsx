import { useTranslation } from "react-i18next";
import { Button } from "./Button";

export function LanguageSwitcher() {
  const { i18n, t } = useTranslation();
  const language = i18n.resolvedLanguage?.startsWith("en") ? "en" : "vi";

  return <div className="language-switcher" role="group" aria-label={t("navigation.language")}>
    <Button kind="quiet" type="button" aria-pressed={language === "vi"} onClick={() => void i18n.changeLanguage("vi")}>{t("language.vietnamese")}</Button>
    <Button kind="quiet" type="button" aria-pressed={language === "en"} onClick={() => void i18n.changeLanguage("en")}>{t("language.english")}</Button>
  </div>;
}
