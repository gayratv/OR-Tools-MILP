import type {ParsedQs} from "qs";

/**
 * Безопасно извлекает строковое значение из параметра запроса Express.
 * @param {string | ParsedQs | (string | ParsedQs)[] | undefined} value - Значение из req.query.
 * @returns {string | undefined} - Строковое значение или undefined, если это не строка.
 */
export function getQueryParamString(value: string | ParsedQs | (string | ParsedQs)[] | undefined): string | undefined {
    return typeof value === "string" ? value : undefined;
}