import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import en from '../locales/en.json';
import zh from '../locales/zh.json';

export type Locale = 'en' | 'zh';

type TranslationValue = string | string[] | Record<string, unknown>;

type Translations = Record<string, Record<string, TranslationValue>>;

const LOCALE_MAP: Record<Locale, Translations> = {
  en: en as Translations,
  zh: zh as Translations,
};

interface I18nContextType {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: string, params?: Record<string, string | number>) => string;
  resolve: (key: string) => TranslationValue | undefined;
}

const I18nContext = createContext<I18nContextType>({
  locale: 'en',
  setLocale: () => {},
  t: (key: string) => key,
  resolve: () => undefined,
});

function resolveValue(obj: Translations, path: string): TranslationValue | undefined {
  const keys = path.split('.');
  let current: unknown = obj;
  for (const key of keys) {
    if (current && typeof current === 'object' && key in current) {
      current = (current as Record<string, unknown>)[key];
    } else {
      return undefined;
    }
  }
  return current as TranslationValue | undefined;
}

function replaceParams(text: string, params?: Record<string, string | number>): string {
  if (!params) return text;
  let result = text;
  for (const [key, value] of Object.entries(params)) {
    result = result.replace(`{${key}}`, String(value));
  }
  return result;
}

function detectBrowserLocale(): Locale {
  const saved = localStorage.getItem('locale') as Locale | null;
  if (saved && LOCALE_MAP[saved]) return saved;
  const lang = navigator.language || '';
  return lang.startsWith('zh') ? 'zh' : 'en';
}

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>(detectBrowserLocale);
  const [translations, setTranslations] = useState<Translations>(LOCALE_MAP[locale]);

  const setLocale = useCallback((newLocale: Locale) => {
    setLocaleState(newLocale);
    setTranslations(LOCALE_MAP[newLocale]);
    // persist to localStorage as fallback
    localStorage.setItem('locale', newLocale);
  }, []);

  const t = useCallback((key: string, params?: Record<string, string | number>): string => {
    const value = resolveValue(translations, key);
    if (typeof value === 'string') {
      return replaceParams(value, params);
    }
    // Fallback to English
    const enValue = resolveValue(LOCALE_MAP.en, key);
    if (typeof enValue === 'string') {
      return replaceParams(enValue, params);
    }
    return key;
  }, [translations]);

  const resolve = useCallback((key: string): TranslationValue | undefined => {
    return resolveValue(translations, key) || resolveValue(LOCALE_MAP.en, key);
  }, [translations]);

  // Restore locale from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem('locale') as Locale | null;
    if (saved && saved !== locale && LOCALE_MAP[saved]) {
      setLocale(saved);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <I18nContext.Provider value={{ locale, setLocale, t, resolve }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useLocale() {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error('useLocale must be used within I18nProvider');
  return ctx;
}

export { I18nContext };
